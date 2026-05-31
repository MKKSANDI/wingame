"""
Game Performance Optimizer - Windows 11 Edition
Modern GUI with Fluent Design principles using PyQt6
Queue-based optimization system with progress tracking
"""

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                              QHBoxLayout, QLabel, QPushButton, QScrollArea,
                              QFrame, QComboBox, QFileDialog, QMessageBox,
                              QProgressDialog, QDialog, QProgressBar, QToolButton,
                              QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty, QThread, pyqtSignal, QTimer, QPoint
from PyQt6.QtGui import QFont, QPainter, QColor, QPixmap, QIcon
import sys
import winreg
import subprocess
import json
import os
import platform
import ctypes
import time

ACCENT_COLOR = "#4EB5A2"
ACCENT_COLOR_HOVER = "#5EC3B3"
ACCENT_COLOR_PRESSED = "#3A8E7C"
SURFACE_COLOR = "rgba(18, 18, 18, 0.92)"
SURFACE_BORDER = "rgba(255, 255, 255, 0.08)"
APP_NAME = "WinGame"
APP_FOLDER = "WinGame"
LOGO_FILENAME = "WinGame.png"
SYSTEM_ICON = "system.png"
GAME_ICON = "game.png"
CONFIG_FILENAME = "optimizer_config.json"
RESTART_REQUIRED_TOGGLES = {"disable_hyperv", "disable_vm_platform", "all_cores"}


def get_app_root():
    """Return directory containing assets for both script and frozen exe"""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def asset_path(filename):
    """Resolve asset path regardless of working directory"""
    return os.path.join(get_app_root(), filename)


_SERVICE_CACHE = None


def fetch_third_party_services():
    """Return list of non-Microsoft services (by path outside Windows)"""
    global _SERVICE_CACHE
    if _SERVICE_CACHE is not None:
        return _SERVICE_CACHE

    try:
        command = [
            "powershell",
            "-NoProfile",
            "-Command",
            "(Get-CimInstance Win32_Service | Where-Object { $_.PathName -and ($_.PathName -notlike 'C:\\\\Windows\\\\*') }) "
            "| Select-Object Name, DisplayName | ConvertTo-Json -Compress"
        ]
        result = subprocess.run(command, capture_output=True, text=True, timeout=10)
        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout)
            if isinstance(data, dict):
                data = [data]
            services = [
                {"Name": svc.get("Name", ""), "DisplayName": svc.get("DisplayName", svc.get("Name", ""))}
                for svc in data if svc.get("Name")
            ]
            _SERVICE_CACHE = services
            return services
    except Exception:
        pass

    _SERVICE_CACHE = []
    return _SERVICE_CACHE


def config_directory():
    r"""Return per-user config directory inside AppData\Local"""
    base = os.getenv("LOCALAPPDATA") or os.path.join(os.path.expanduser("~"), "AppData", "Local")
    path = os.path.join(base, APP_FOLDER)
    os.makedirs(path, exist_ok=True)
    return path


def config_path():
    """Return full config file path"""
    return os.path.join(config_directory(), CONFIG_FILENAME)


def is_running_as_admin():
    """Check if current process has admin rights"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def relaunch_as_admin():
    """Re-launch the script/executable with elevation"""
    if getattr(sys, "frozen", False):
        executable = sys.executable
        params = " ".join(f'"{arg}"' for arg in sys.argv[1:])
    else:
        executable = sys.executable
        script = os.path.abspath(sys.argv[0])
        extra = " ".join(f'"{arg}"' for arg in sys.argv[1:])
        params = f'"{script}"'
        if extra:
            params += f" {extra}"

    try:
        hinstance = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", executable, params or None, None, 1
        )
        return hinstance > 32
    except Exception:
        return False


class OptimizationWorker(QThread):
    """Worker thread for applying optimizations without blocking UI"""
    progress = pyqtSignal(int, str)  # progress percentage, status message
    finished = pyqtSignal(bool, str, bool)  # success, message, restart_required
    
    def __init__(self, optimizer, enabled_tweaks, restart_keys=None, parent=None):
        super().__init__(parent)
        self.optimizer = optimizer
        self.enabled_tweaks = enabled_tweaks
        self.restart_keys = restart_keys or set()
        
    def run(self):
        """Apply all enabled optimizations"""
        applicable_items = [(key, enabled) for key, enabled in self.enabled_tweaks.items() if key != "gpu_tier"]
        total = len(applicable_items) or 1
        success_count = 0
        fail_count = 0
        restart_needed = False

        for i, (key, enabled) in enumerate(applicable_items, 1):
                
            try:
                # Update progress
                progress_pct = int((i / total) * 100)
                self.progress.emit(progress_pct, f"Applying: {key.replace('_', ' ').title()}")
                
                # Apply the tweak
                if enabled:
                    self.optimizer.apply_tweak(key, True)
                    success_count += 1
                    if key in self.restart_keys:
                        restart_needed = True
                else:
                    self.optimizer.apply_tweak(key, False)
                    success_count += 1
                    if key in self.restart_keys:
                        restart_needed = True
                    
                time.sleep(0.1)  # Small delay for visual feedback
                
            except Exception as e:
                fail_count += 1
                self.progress.emit(progress_pct, f"Failed: {key} - {str(e)}")
                time.sleep(0.3)
        
        # Finished
        if fail_count > 0:
            msg = f"Applied {success_count} optimizations\n{fail_count} failed (may need restart)"
            self.finished.emit(True, msg, restart_needed)
        else:
            msg = f"Successfully applied {success_count} optimizations!\n\nRestart your PC for all changes to take effect."
            self.finished.emit(True, msg, restart_needed)


class ModernProgressDialog(QDialog):
    """Modern progress dialog with Windows 11 styling"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Applying Optimizations")
        self.setModal(True)
        self.setFixedSize(500, 150)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint)
        
        # Remove window buttons
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)
        
        # Set style
        self.setStyleSheet("""
            QDialog {
                background-color: rgba(18,18,18,0.96);
                border: 1px solid rgba(255,255,255,0.06);
                border-radius: 10px;
            }
            QLabel {
                color: #ffffff;
                background: transparent;
            }
            QProgressBar {
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 4px;
                background-color: rgba(255,255,255,0.03);
                height: 8px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: %s;
                border-radius: 3px;
            }
        """ % ACCENT_COLOR)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("Applying Gaming Optimizations")
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.DemiBold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFixedHeight(24)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Preparing...")
        self.status_label.setFont(QFont("Segoe UI", 9))
        self.status_label.setStyleSheet("color: #b3b3b3;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
    def update_progress(self, value, status):
        """Update progress bar and status"""
        self.progress_bar.setValue(value)
        self.status_label.setText(status)


class ToggleSwitch(QWidget):
    """Modern Windows 11 style toggle switch - no auto-apply"""

    def __init__(self, parent=None, callback=None,
                 track_width=44, track_height=20,
                 circle_diameter=16, margin=2):
        super().__init__(parent)
        self._checked = False
        self._callback = callback
        self.track_width = track_width
        self.track_height = track_height
        self.circle_diameter = circle_diameter
        self.margin = margin
        self._circle_min = margin
        self._circle_max = track_width - circle_diameter - margin
        self._circle_position = self._circle_min
        self.setFixedSize(track_width, track_height)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.animation = QPropertyAnimation(self, b"circle_position", self)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.animation.setDuration(150)

    @pyqtProperty(int)
    def circle_position(self):
        return self._circle_position

    @circle_position.setter
    def circle_position(self, pos):
        self._circle_position = pos
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background
        if self._checked:
            painter.setBrush(QColor(ACCENT_COLOR))
        else:
            painter.setBrush(QColor("#4a4a4a"))

        painter.setPen(Qt.PenStyle.NoPen)
        radius = self.track_height / 2
        painter.drawRoundedRect(0, 0, self.track_width, self.track_height, radius, radius)

        # Circle
        painter.setBrush(QColor("#ffffff"))
        painter.drawEllipse(self._circle_position, self.margin, self.circle_diameter, self.circle_diameter)

    def mousePressEvent(self, event):
        self._checked = not self._checked

        if self._checked:
            self.animation.setStartValue(self._circle_position)
            self.animation.setEndValue(self._circle_max)
        else:
            self.animation.setStartValue(self._circle_position)
            self.animation.setEndValue(self._circle_min)

        self.animation.start()
        
        if self._callback:
            self._callback(self._checked)

    def isChecked(self):
        return self._checked

    def setChecked(self, checked):
        if self._checked != checked:
            self._checked = checked
            self._circle_position = self._circle_max if checked else self._circle_min
            self.update()


class OptimizationCard(QFrame):
    """Card widget for each optimization option"""

    def __init__(self, title, description, key, callback=None, parent=None):
        super().__init__(parent)
        self.key = key
        self.callback = callback

        self.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.03);
                border-radius: 6px;
                border: 1px solid rgba(255, 255, 255, 0.08);
            }
            QFrame:hover {
                background-color: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.12);
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)

        # Left side - text
        text_layout = QVBoxLayout()
        text_layout.setSpacing(3)

        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Normal))
        title_label.setStyleSheet("color: #ffffff; border: none; background: transparent;")

        desc_label = QLabel(description)
        desc_label.setFont(QFont("Segoe UI", 8))
        desc_label.setStyleSheet("color: rgba(255, 255, 255, 0.6); border: none; background: transparent;")
        desc_label.setWordWrap(True)

        text_layout.addWidget(title_label)
        text_layout.addWidget(desc_label)

        # Right side - toggle
        self.toggle = ToggleSwitch(callback=self.on_toggle)

        layout.addLayout(text_layout, 1)
        layout.addWidget(self.toggle, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

    def on_toggle(self, checked):
        if self.callback:
            self.callback(self.key, checked)

    def setChecked(self, checked):
        self.toggle.setChecked(checked)
        
    def isChecked(self):
        return self.toggle.isChecked()


class ComboCard(QFrame):
    """Card with dropdown selection"""

    def __init__(self, title, description, options, key, callback=None, parent=None):
        super().__init__(parent)
        self.key = key
        self.callback = callback

        self.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.03);
                border-radius: 6px;
                border: 1px solid rgba(255, 255, 255, 0.08);
            }
            QFrame:hover {
                background-color: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.12);
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)

        # Left side - text
        text_layout = QVBoxLayout()
        text_layout.setSpacing(3)

        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Normal))
        title_label.setStyleSheet("color: #ffffff; border: none; background: transparent;")

        desc_label = QLabel(description)
        desc_label.setFont(QFont("Segoe UI", 8))
        desc_label.setStyleSheet("color: rgba(255, 255, 255, 0.6); border: none; background: transparent;")
        desc_label.setWordWrap(True)

        text_layout.addWidget(title_label)
        text_layout.addWidget(desc_label)

        # Right side - combo box
        self.combo = QComboBox()
        self.combo.addItems(options)
        self.combo.setFixedWidth(200)
        self.combo.setFont(QFont("Segoe UI", 9))
        self.combo.setStyleSheet("""
            QComboBox {
                background-color: rgba(255, 255, 255, 0.05);
                color: #ffffff;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 4px;
                padding: 5px 10px;
            }
            QComboBox:hover {
                background-color: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.15);
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #ffffff;
                margin-right: 6px;
            }
            QComboBox QAbstractItemView {
                background-color: #2b2b2b;
                color: #ffffff;
                selection-background-color: %(accent)s;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
        """ % {"accent": ACCENT_COLOR})
        self.combo.currentTextChanged.connect(self.on_change)

        layout.addLayout(text_layout, 1)
        layout.addWidget(self.combo, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

    def on_change(self, text):
        if self.callback:
            self.callback(self.key, text)

    def setCurrentText(self, text):
        self.combo.setCurrentText(text)
        
    def getCurrentText(self):
        return self.combo.currentText()


class SectionHeader(QWidget):
    """Section header with icon"""

    def __init__(self, text, icon_path=None, parent=None):
        super().__init__(parent)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Icon
        if icon_path and os.path.exists(icon_path):
            icon_label = QLabel()
            pixmap = QPixmap(icon_path)
            pixmap = pixmap.scaled(20, 20, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            icon_label.setPixmap(pixmap)
            layout.addWidget(icon_label)
        
        # Text
        label = QLabel(text)
        label.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        label.setStyleSheet("color: #ffffff;")
        layout.addWidget(label)
        
        layout.addStretch()


class ModernButton(QPushButton):
    """Modern Windows 11 style button"""

    def __init__(self, text, style="primary", parent=None):
        super().__init__(text, parent)
        self.setFont(QFont("Segoe UI", 9, QFont.Weight.Normal))
        self.setFixedHeight(32)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        if style == "primary":
            self.setStyleSheet("""
                QPushButton {
                    background-color: %(accent)s;
                    color: #ffffff;
                    border: none;
                    border-radius: 4px;
                    padding: 0 20px;
                }
                QPushButton:hover {
                    background-color: %(accent_hover)s;
                }
                QPushButton:pressed {
                    background-color: %(accent_pressed)s;
                }
            """ % {
                "accent": ACCENT_COLOR,
                "accent_hover": ACCENT_COLOR_HOVER,
                "accent_pressed": ACCENT_COLOR_PRESSED
            })
        elif style == "success":
            self.setStyleSheet("""
                QPushButton {
                    background-color: #3A9A84;
                    color: #ffffff;
                    border: none;
                    border-radius: 4px;
                    padding: 0 24px;
                }
                QPushButton:hover {
                    background-color: #46B697;
                }
                QPushButton:pressed {
                    background-color: #2E7B69;
                }
            """)
        elif style == "secondary":
            self.setStyleSheet("""
                QPushButton {
                    background-color: rgba(255, 255, 255, 0.06);
                    color: #ffffff;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 4px;
                    padding: 0 20px;
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 0.08);
                    border: 1px solid rgba(255, 255, 255, 0.15);
                }
                QPushButton:pressed {
                    background-color: rgba(255, 255, 255, 0.04);
                }
            """)


class TitleButton(QToolButton):
    """Custom title bar button"""

    def __init__(self, symbol, role="control", callback=None):
        super().__init__()
        self.setText(symbol)
        self.role = role
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(38, 26)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setStyleSheet(self._build_style())
        if callback:
            self.clicked.connect(callback)

    def _build_style(self):
        if self.role == "close":
            return """
                QToolButton {
                    color: #ffffff;
                    background-color: transparent;
                    border: none;
                    border-radius: 4px;
                    font-size: 13px;
                }
                QToolButton:hover {
                    background-color: #c42b1c;
                }
                QToolButton:pressed {
                    background-color: #aa2417;
                }
            """
        return """
            QToolButton {
                color: rgba(255, 255, 255, 0.8);
                background-color: transparent;
                border: none;
                border-radius: 4px;
                font-size: 13px;
            }
            QToolButton:hover {
                background-color: rgba(255, 255, 255, 0.08);
            }
            QToolButton:pressed {
                background-color: rgba(255, 255, 255, 0.12);
            }
        """


class TitleBar(QWidget):
    """Custom frameless window title bar"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._parent = parent
        self._mouse_pos = QPoint()
        self.setFixedHeight(48)
        self.setObjectName("TitleBar")
        self._corner_radius = 14
        self._apply_style()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(10)

        title_layout = QVBoxLayout()
        title_layout.setSpacing(0)

        self.title_label = QLabel(APP_NAME)
        self.title_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        self.title_label.setStyleSheet("color: #ffffff;")

        self.subtitle_label = QLabel("Performance Optimizer")
        self.subtitle_label.setFont(QFont("Segoe UI", 8))
        self.subtitle_label.setStyleSheet("color: rgba(255,255,255,0.55);")

        title_layout.addWidget(self.title_label)
        title_layout.addWidget(self.subtitle_label)

        layout.addLayout(title_layout)
        layout.addStretch()

        self.min_button = TitleButton("–", callback=self._parent.showMinimized)
        self.max_button = TitleButton("□", callback=self._parent.toggle_max_restore)
        self.close_button = TitleButton("×", role="close", callback=self._parent.close)

        layout.addWidget(self.min_button)
        layout.addWidget(self.max_button)
        layout.addWidget(self.close_button)

    def update_max_button(self, maximized: bool):
        self.max_button.setText("❐" if maximized else "□")
        self.set_corner_radius(0 if maximized else 14)

    def set_corner_radius(self, radius: int):
        self._corner_radius = radius
        self._apply_style()

    def _apply_style(self):
        self.setStyleSheet(f"""
            #TitleBar {{
                background-color: rgba(0, 0, 0, 0);
                border-top-left-radius: {self._corner_radius}px;
                border-top-right-radius: {self._corner_radius}px;
            }}
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._mouse_pos = event.globalPosition().toPoint() - self._parent.frameGeometry().topLeft()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton and not self._parent._is_maximized:
            self._parent.move(event.globalPosition().toPoint() - self._mouse_pos)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._parent.toggle_max_restore()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)


class ServiceListWidget(QFrame):
    """Expandable list of third-party services with toggles"""

    def __init__(self, states, callback, parent=None):
        super().__init__(parent)
        self.states = dict(states or {})
        self.callback = callback
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.02);
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 8px;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(10)
        self.toggles = {}

        header = QLabel("Select the non-Microsoft services you want WinGame to pause during optimization:")
        header.setWordWrap(True)
        header.setFont(QFont("Segoe UI", 9))
        header.setStyleSheet("color: rgba(255, 255, 255, 0.75);")
        layout.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 10px;
            }
            QScrollBar::handle:vertical {
                background-color: rgba(255, 255, 255, 0.15);
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: rgba(255, 255, 255, 0.25);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
        """)
        scroll.setMinimumHeight(180)
        scroll.setMaximumHeight(240)

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(8)

        services = fetch_third_party_services()
        if not services:
            empty = QLabel("No third-party services detected.")
            empty.setStyleSheet("color: rgba(255, 255, 255, 0.45);")
            container_layout.addWidget(empty)
        else:
            for svc in services:
                row_frame = QFrame()
                row_frame.setStyleSheet("""
                    QFrame {
                        background-color: rgba(255, 255, 255, 0.04);
                        border: 1px solid rgba(255, 255, 255, 0.08);
                        border-radius: 8px;
                    }
                """)
                row_layout = QHBoxLayout(row_frame)
                row_layout.setContentsMargins(14, 8, 14, 8)
                row_layout.setSpacing(12)

                text_layout = QVBoxLayout()
                text_layout.setSpacing(0)

                display = QLabel(svc['DisplayName'] or svc['Name'])
                display.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
                display.setStyleSheet("color: rgba(255,255,255,0.92);")

                technical = QLabel(svc['Name'])
                technical.setFont(QFont("Segoe UI", 8))
                technical.setStyleSheet("color: rgba(255,255,255,0.5);")

                text_layout.addWidget(display)
                text_layout.addWidget(technical)

                toggle = ToggleSwitch(
                    callback=lambda checked, name=svc["Name"]: self.on_toggle(name, checked),
                    track_width=32,
                    track_height=16,
                    circle_diameter=12,
                    margin=2
                )
                toggle.setChecked(self.states.get(svc["Name"], False))

                row_layout.addLayout(text_layout, 1)
                row_layout.addWidget(toggle, 0, Qt.AlignmentFlag.AlignVCenter)

                container_layout.addWidget(row_frame)
                self.toggles[svc["Name"]] = toggle

        container_layout.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll)

    def on_toggle(self, name, checked):
        self.states[name] = checked
        if self.callback:
            self.callback(dict(self.states))

    def apply_states(self, states):
        self.states = dict(states or {})
        for name, toggle in self.toggles.items():
            toggle.setChecked(self.states.get(name, False))


class GameOptimizer(QMainWindow):
    """Main application window"""

    def __init__(self):
        super().__init__()

        # Check admin
        if not is_running_as_admin():
            QMessageBox.critical(None, "Administrator Rights Required",
                "Could not obtain administrator privileges. Please re-launch WinGame as administrator.")
            sys.exit(1)

        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(950, 750)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowSystemMenuHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self._is_maximized = False

        # Configuration
        self.config_file = config_path()
        self.tweaks_state = {}
        self.cards = {}
        self.service_states = {}

        # Detect system
        self.cpu_vendor = self.detect_cpu()
        self.gpu_vendor = self.detect_gpu()

        # Load config
        self.load_config()

        # Setup UI
        self.setup_ui()

        # Center window
        self.center_window()

    def center_window(self):
        """Center window on screen"""
        frame_geometry = self.frameGeometry()
        screen_center = self.screen().availableGeometry().center()
        frame_geometry.moveCenter(screen_center)
        self.move(frame_geometry.topLeft())

    def detect_cpu(self):
        """Detect CPU vendor"""
        try:
            cpu_info = platform.processor().upper()
            if "AMD" in cpu_info:
                return "AMD"
            elif "INTEL" in cpu_info:
                return "Intel"
            return "Unknown"
        except:
            return "Unknown"

    def detect_gpu(self):
        """Detect GPU vendor"""
        try:
            result = subprocess.run(['wmic', 'path', 'win32_VideoController', 'get', 'name'],
                                  capture_output=True, text=True, timeout=5)
            output = result.stdout.upper()

            if "NVIDIA" in output or "GEFORCE" in output:
                return "NVIDIA"
            elif "AMD" in output or "RADEON" in output:
                return "AMD"
            elif "INTEL" in output:
                return "Intel"
            return "Unknown"
        except:
            return "Unknown"

    def setup_ui(self):
        """Setup the user interface"""
        # Main widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        self.setStyleSheet("""
            QMainWindow {
                background-color: transparent;
            }
        """)

        self.outer_layout = QVBoxLayout(central_widget)
        self.outer_layout.setContentsMargins(12, 12, 12, 12)
        self.outer_layout.setSpacing(0)

        self.window_frame = QWidget()
        self.window_frame.setObjectName("WindowFrame")
        self.update_window_frame_style()

        self.shadow_effect = QGraphicsDropShadowEffect(self)
        self.shadow_effect.setBlurRadius(28)
        self.shadow_effect.setColor(QColor(0, 0, 0, 180))
        self.shadow_effect.setOffset(0, 12)
        self.window_frame.setGraphicsEffect(self.shadow_effect)

        self.frame_layout = QVBoxLayout(self.window_frame)
        self.frame_layout.setContentsMargins(0, 0, 0, 0)
        self.frame_layout.setSpacing(0)

        self.title_bar = TitleBar(self)
        self.frame_layout.addWidget(self.title_bar)
        self.title_bar.update_max_button(self._is_maximized)

        # Header
        header = QWidget()
        header.setStyleSheet("""
            background-color: rgba(255, 255, 255, 0.02);
            border-bottom: 1px solid rgba(255, 255, 255, 0.04);
        """)
        header.setFixedHeight(70)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(28, 8, 28, 8)

        # Title section
        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)

        name_row = QHBoxLayout()
        name_row.setSpacing(12)

        name_label = QLabel(APP_NAME)
        name_label.setFont(QFont("Segoe UI", 18, QFont.Weight.DemiBold))
        name_label.setStyleSheet("color: #ffffff; border: none;")
        name_row.addWidget(name_label, 0, Qt.AlignmentFlag.AlignVCenter)

        logo_badge = self.build_logo_badge()
        if logo_badge:
            name_row.addWidget(logo_badge, 0, Qt.AlignmentFlag.AlignVCenter)

        name_row.addStretch()
        title_layout.addLayout(name_row)

        system_info = QLabel(f"Detected: {self.cpu_vendor} CPU • {self.gpu_vendor} GPU")
        system_info.setFont(QFont("Segoe UI", 9))
        system_info.setStyleSheet("color: rgba(255, 255, 255, 0.55); border: none;")

        title_layout.addWidget(system_info)
        header_layout.addLayout(title_layout)

        header_layout.addStretch()

        self.frame_layout.addWidget(header)

        # Scrollable content area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background-color: transparent;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background-color: rgba(255, 255, 255, 0.15);
                border-radius: 5px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: rgba(255, 255, 255, 0.25);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(28, 18, 28, 18)
        scroll_layout.setSpacing(20)

        # Create sections
        self.create_cpu_section(scroll_layout)
        self.create_gpu_section(scroll_layout)
        self.create_system_section(scroll_layout)
        self.create_power_section(scroll_layout)

        scroll_layout.addStretch()

        scroll.setWidget(scroll_content)
        self.frame_layout.addWidget(scroll)

        # Bottom bar
        self.create_bottom_bar(self.frame_layout)

        self.outer_layout.addWidget(self.window_frame)

    def create_cpu_section(self, layout):
        """Create CPU optimization section"""
        layout.addWidget(SectionHeader("CPU Optimizations", asset_path(SYSTEM_ICON)))
        
        layout.addSpacing(8)

        self.add_card(layout, "power_throttling",
            "Disable Power Throttling",
            "Prevents Windows from limiting CPU performance for power saving",
            self.on_toggle)

        self.add_card(layout, "cpu_gaming_opt",
            "Optimize CPU for Gaming",
            "Sets high priority for gaming processes in multimedia profile",
            self.on_toggle)

        self.add_card(layout, "pc_responsiveness",
            "Increase PC Responsiveness",
            "Disables network throttling and improves system responsiveness",
            self.on_toggle)

        self.add_card(layout, "disable_dvr",
            "Disable Game DVR",
            "Turns off Xbox Game Bar recording features to free resources",
            self.on_toggle)

        self.add_card(layout, "disable_maintenance",
            "Disable Maintenance Tasks",
            "Prevents automatic maintenance from running during gaming",
            self.on_toggle)

        self.add_card(layout, "disable_energy",
            "Disable Energy Estimation",
            "Stops energy logging service to reduce CPU overhead",
            self.on_toggle)

        self.add_card(layout, "cpu_priority",
            f"Enable {self.cpu_vendor} CPU Priority",
            f"Optimizes CPU scheduling for {self.cpu_vendor} processors",
            self.on_toggle)

        self.add_card(layout, "all_cores",
            "Use All CPU Cores at Startup",
            "Forces Windows to use all processor cores during boot",
            self.on_toggle)

    def create_gpu_section(self, layout):
        """Create GPU optimization section"""
        layout.addWidget(SectionHeader("GPU Optimizations", asset_path(GAME_ICON)))
        
        layout.addSpacing(8)

        self.add_card(layout, "gpu_gaming_opt",
            "Gaming GPU Optimizations",
            "Applies base gaming performance registry tweaks for GPU",
            self.on_toggle)

        # GPU tier combo
        combo = ComboCard("GPU Performance Tier",
            "Select optimization level based on your GPU capabilities",
            ["Low-Medium (Budget GPU)", "Medium-High (Powerful GPU)"],
            "gpu_tier",
            self.on_combo_change)
        combo.setCurrentText(self.tweaks_state.get("gpu_tier", "Low-Medium (Budget GPU)"))
        self.cards["gpu_tier"] = combo
        layout.addWidget(combo)

        self.add_card(layout, "gpu_thread_priority",
            f"Enable {self.gpu_vendor} Thread Priority",
            f"Optimizes GPU driver thread scheduling for {self.gpu_vendor}",
            self.on_toggle)

    def create_system_section(self, layout):
        """Create system optimization section"""
        layout.addWidget(SectionHeader("System Optimizations", asset_path(SYSTEM_ICON)))
        
        layout.addSpacing(8)

        self.add_card(layout, "disable_hyperv",
            "Disable Hyper-V",
            "Disables virtualization features to free CPU resources (requires restart)",
            self.on_toggle)

        self.add_card(layout, "disable_vm_platform",
            "Disable Virtual Machine Platform",
            "Turns off VM platform to reduce CPU overhead (requires restart)",
            self.on_toggle)

        self.add_card(layout, "disable_services",
            "Disable Unnecessary Services",
            "Stops non-essential background services",
            self.on_toggle)

        self.service_list_widget = ServiceListWidget(
            self.service_states,
            self.on_service_states_changed
        )
        layout.addWidget(self.service_list_widget)
        self.service_list_widget.setVisible(self.tweaks_state.get("disable_services", False))

    def create_power_section(self, layout):
        """Create power management section"""
        layout.addWidget(SectionHeader("Power Management", asset_path(SYSTEM_ICON)))
        
        layout.addSpacing(8)

        self.add_card(layout, "ultimate_performance",
            "Ultimate Performance Power Plan",
            "Enables maximum performance power plan (disables power saving)",
            self.on_toggle)

    def add_card(self, layout, key, title, description, callback):
        """Helper to add optimization card"""
        card = OptimizationCard(title, description, key, callback)
        card.setChecked(self.tweaks_state.get(key, False))
        self.cards[key] = card
        layout.addWidget(card)

    def create_bottom_bar(self, layout):
        """Create bottom control bar"""
        bottom = QWidget()
        bottom.setStyleSheet("""
            background-color: rgba(255, 255, 255, 0.02);
            border-top: 1px solid rgba(255, 255, 255, 0.04);
        """)
        bottom.setFixedHeight(60)

        bottom_layout = QHBoxLayout(bottom)
        bottom_layout.setContentsMargins(24, 14, 24, 14)

        bottom_layout.addStretch()

        export_btn = ModernButton("Export Config", "secondary")
        export_btn.clicked.connect(self.export_config)
        bottom_layout.addWidget(export_btn)

        import_btn = ModernButton("Import Config", "secondary")
        import_btn.clicked.connect(self.import_config)
        bottom_layout.addWidget(import_btn)

        apply_btn = ModernButton("Apply All Enabled", "success")
        apply_btn.clicked.connect(self.apply_all)
        apply_btn.setFixedWidth(150)
        bottom_layout.addWidget(apply_btn)

        layout.addWidget(bottom)

    def build_logo_badge(self):
        """Create logo display without boxed background"""
        logo_file = asset_path(LOGO_FILENAME)
        if not os.path.exists(logo_file):
            return None
        pixmap = QPixmap(logo_file)
        if pixmap.isNull():
            return None

        badge = QLabel()
        badge.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scaled = pixmap.scaled(42, 42, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        badge.setPixmap(scaled)

        return badge

    def update_window_frame_style(self):
        """Update frame rounding based on maximize state"""
        radius = 0 if self._is_maximized else 14
        border = "0px" if self._is_maximized else f"1px solid {SURFACE_BORDER}"
        self.window_frame.setStyleSheet(f"""
            #WindowFrame {{
                background-color: {SURFACE_COLOR};
                border-radius: {radius}px;
                border: {border};
            }}
        """)

    def toggle_max_restore(self):
        """Toggle between maximized and normal frameless states"""
        if self._is_maximized:
            self.showNormal()
            self._is_maximized = False
            self.outer_layout.setContentsMargins(12, 12, 12, 12)
            self.shadow_effect.setEnabled(True)
        else:
            self.showMaximized()
            self._is_maximized = True
            self.outer_layout.setContentsMargins(0, 0, 0, 0)
            self.shadow_effect.setEnabled(False)

        self.update_window_frame_style()
        self.title_bar.update_max_button(self._is_maximized)

    def on_toggle(self, key, checked):
        """Handle toggle switch changes - QUEUE ONLY, don't apply"""
        self.tweaks_state[key] = checked
        self.save_config()
        # No immediate application - changes are queued
        if key == "disable_services" and hasattr(self, "service_list_widget"):
            self.service_list_widget.setVisible(checked)

    def on_combo_change(self, key, value):
        """Handle combo box changes"""
        self.tweaks_state[key] = value
        self.save_config()

    def on_service_states_changed(self, states):
        """Handle per-service toggle changes"""
        self.service_states = states
        self.tweaks_state["service_states"] = states
        self.save_config()

    def apply_all(self):
        """Apply all enabled optimizations with progress dialog"""
        reply = QMessageBox.question(self, "Apply All Optimizations",
            "This will apply all enabled optimizations.\n\n"
            "Some changes may require a system restart to take full effect.\n\n"
            "Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply != QMessageBox.StandardButton.Yes:
            return

        restore_reply = QMessageBox.question(
            self,
            "Create Restore Point",
            "Create a Windows restore point before applying changes?\n\n"
            "Recommended for safer rollback.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Yes,
        )
        if restore_reply == QMessageBox.StandardButton.Cancel:
            return
        if restore_reply == QMessageBox.StandardButton.Yes:
            ok, detail = self.create_restore_point()
            if not ok:
                continue_reply = QMessageBox.question(
                    self,
                    "Restore Point Failed",
                    "Could not create a restore point automatically.\n\n"
                    f"{detail}\n\n"
                    "Continue applying optimizations anyway?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )
                if continue_reply != QMessageBox.StandardButton.Yes:
                    return
        
        # Create progress dialog
        progress_dialog = ModernProgressDialog(self)
        progress_dialog.show()
        
        # Create worker thread
        self.worker = OptimizationWorker(self, self.tweaks_state, RESTART_REQUIRED_TOGGLES)
        self.worker.progress.connect(progress_dialog.update_progress)
        self.worker.finished.connect(lambda success, msg, restart: self.on_apply_finished(progress_dialog, success, msg, restart))
        self.worker.start()

    def on_apply_finished(self, progress_dialog, success, message, restart_required):
        """Called when optimization worker finishes"""
        progress_dialog.close()
        
        if success:
            QMessageBox.information(self, "Complete", message)
        else:
            QMessageBox.warning(self, "Warning", message)

        if restart_required:
            self.prompt_for_restart()

    def create_restore_point(self):
        """Try creating a restore point. Returns (ok, detail)."""
        description = f"WinGame_{time.strftime('%Y%m%d_%H%M%S')}"
        command = [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            f"Checkpoint-Computer -Description '{description}' -RestorePointType 'MODIFY_SETTINGS'",
        ]
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=90,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        except Exception as exc:
            return False, f"Checkpoint command error: {exc}"

        if result.returncode == 0:
            return True, f"Created restore point: {description}"

        detail = (result.stderr or result.stdout or "Unknown error").strip()
        return False, detail

    def prompt_for_restart(self):
        """Prompt user to restart now or later"""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Restart Required")
        msg_box.setIcon(QMessageBox.Icon.Question)
        msg_box.setText("Some optimizations you enabled require a system restart to finish applying.\n\nRestart now or restart later?")
        restart_now = msg_box.addButton("Restart Now", QMessageBox.ButtonRole.AcceptRole)
        restart_later = msg_box.addButton("Restart Later", QMessageBox.ButtonRole.RejectRole)
        msg_box.setDefaultButton(restart_now)
        msg_box.exec()

        if msg_box.clickedButton() == restart_now:
            try:
                subprocess.run(["shutdown", "/r", "/t", "0"], check=True)
            except Exception as e:
                QMessageBox.warning(self, "Restart Failed", f"Unable to restart automatically.\n\n{e}")

    # ==================== TWEAK IMPLEMENTATION METHODS ====================

    def apply_tweak(self, key, enable):
        """Apply individual tweak"""
        if key == "power_throttling":
            self.toggle_power_throttling(enable)
        elif key == "cpu_gaming_opt":
            self.toggle_cpu_gaming(enable)
        elif key == "pc_responsiveness":
            self.toggle_pc_responsiveness(enable)
        elif key == "disable_dvr":
            self.toggle_game_dvr(enable)
        elif key == "disable_maintenance":
            self.toggle_maintenance(enable)
        elif key == "disable_energy":
            self.toggle_energy_estimation(enable)
        elif key == "cpu_priority":
            self.toggle_cpu_priority(enable)
        elif key == "all_cores":
            self.toggle_all_cores(enable)
        elif key == "gpu_gaming_opt":
            self.toggle_gpu_gaming(enable)
        elif key == "gpu_thread_priority":
            self.toggle_gpu_thread_priority(enable)
        elif key == "disable_hyperv":
            self.toggle_hyperv(enable)
        elif key == "disable_vm_platform":
            self.toggle_vm_platform(enable)
        elif key == "disable_services":
            self.toggle_services(enable)
        elif key == "ultimate_performance":
            self.toggle_ultimate_performance(enable)

    def toggle_power_throttling(self, enable):
        """Toggle power throttling via Group Policy"""
        if enable:
            subprocess.run([
                "powershell", "-Command",
                "New-Item -Path 'HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\System' -Force | Out-Null; "
                "Set-ItemProperty -Path 'HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\System' "
                "-Name 'EnablePowerThrottling' -Value 0 -Type DWord -Force"
            ], check=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            subprocess.run([
                "powershell", "-Command",
                "Remove-ItemProperty -Path 'HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\System' "
                "-Name 'EnablePowerThrottling' -ErrorAction SilentlyContinue"
            ], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)

    def toggle_cpu_gaming(self, enable):
        """Toggle CPU gaming optimization"""
        key_path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games"
        try:
            key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path)
            
            if enable:
                winreg.SetValueEx(key, "Affinity", 0, winreg.REG_DWORD, 0)
                winreg.SetValueEx(key, "Background Only", 0, winreg.REG_SZ, "False")
                winreg.SetValueEx(key, "Clock Rate", 0, winreg.REG_DWORD, 10000)
                winreg.SetValueEx(key, "GPU Priority", 0, winreg.REG_DWORD, 8)
                winreg.SetValueEx(key, "Priority", 0, winreg.REG_DWORD, 6)
                winreg.SetValueEx(key, "Scheduling Category", 0, winreg.REG_SZ, "High")
                winreg.SetValueEx(key, "SFIO Priority", 0, winreg.REG_SZ, "High")
            else:
                winreg.SetValueEx(key, "Priority", 0, winreg.REG_DWORD, 2)
                winreg.SetValueEx(key, "Scheduling Category", 0, winreg.REG_SZ, "Medium")
                winreg.SetValueEx(key, "SFIO Priority", 0, winreg.REG_SZ, "Normal")
            
            winreg.CloseKey(key)
        except Exception as e:
            raise Exception(f"CPU gaming optimization failed: {e}")

    def toggle_pc_responsiveness(self, enable):
        """Toggle PC responsiveness settings"""
        key_path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile"
        try:
            key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path)
            
            if enable:
                winreg.SetValueEx(key, "NetworkThrottlingIndex", 0, winreg.REG_DWORD, 0xffffffff)
                winreg.SetValueEx(key, "SystemResponsiveness", 0, winreg.REG_DWORD, 0)
            else:
                winreg.SetValueEx(key, "NetworkThrottlingIndex", 0, winreg.REG_DWORD, 10)
                winreg.SetValueEx(key, "SystemResponsiveness", 0, winreg.REG_DWORD, 20)
            
            winreg.CloseKey(key)
        except Exception as e:
            raise Exception(f"PC responsiveness failed: {e}")

    def toggle_game_dvr(self, enable):
        """Toggle Game DVR and Game Bar"""
        try:
            key_path = r"System\GameConfigStore"
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
            
            if enable:
                winreg.SetValueEx(key, "GameDVR_Enabled", 0, winreg.REG_DWORD, 0)
                winreg.SetValueEx(key, "GameDVR_FSEBehaviorMode", 0, winreg.REG_DWORD, 2)
                winreg.SetValueEx(key, "GameDVR_HonorUserFSEBehaviorMode", 0, winreg.REG_DWORD, 0)
                winreg.SetValueEx(key, "GameDVR_DXGIHonorFSEWindowsCompatible", 0, winreg.REG_DWORD, 0)
                winreg.SetValueEx(key, "GameDVR_EFSEFeatureFlags", 0, winreg.REG_DWORD, 0)
            else:
                winreg.SetValueEx(key, "GameDVR_Enabled", 0, winreg.REG_DWORD, 1)
                winreg.SetValueEx(key, "GameDVR_FSEBehaviorMode", 0, winreg.REG_DWORD, 0)
            
            winreg.CloseKey(key)
        except Exception as e:
            raise Exception(f"Game DVR toggle failed: {e}")

    def toggle_maintenance(self, enable):
        """Toggle Windows automatic maintenance"""
        key_path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Schedule\Maintenance"
        try:
            key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path)
            
            if enable:
                winreg.SetValueEx(key, "MaintenanceDisabled", 0, winreg.REG_DWORD, 1)
            else:
                try:
                    winreg.DeleteValue(key, "MaintenanceDisabled")
                except:
                    pass
            
            winreg.CloseKey(key)
        except Exception as e:
            raise Exception(f"Maintenance toggle failed: {e}")

    def toggle_energy_estimation(self, enable):
        """Toggle energy estimation service"""
        try:
            if enable:
                key_path = r"SYSTEM\CurrentControlSet\Control\Power"
                key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path)
                winreg.SetValueEx(key, "EnergyEstimationEnabled", 0, winreg.REG_DWORD, 0)
                winreg.CloseKey(key)
                
                subprocess.run(["sc", "config", "diagtrack", "start=", "disabled"],
                             capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                subprocess.run(["sc", "stop", "diagtrack"],
                             capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                key_path = r"SYSTEM\CurrentControlSet\Control\Power"
                key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path)
                try:
                    winreg.DeleteValue(key, "EnergyEstimationEnabled")
                except:
                    pass
                winreg.CloseKey(key)
                
                subprocess.run(["sc", "config", "diagtrack", "start=", "auto"],
                             capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        except Exception as e:
            raise Exception(f"Energy estimation toggle failed: {e}")

    def toggle_cpu_priority(self, enable):
        """Toggle CPU priority based on vendor"""
        key_path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games"
        try:
            key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path)
            
            if enable:
                if self.cpu_vendor == "AMD":
                    winreg.SetValueEx(key, "GPU Priority", 0, winreg.REG_DWORD, 8)
                    winreg.SetValueEx(key, "Priority", 0, winreg.REG_DWORD, 6)
                    winreg.SetValueEx(key, "Scheduling Category", 0, winreg.REG_SZ, "High")
                    winreg.SetValueEx(key, "SFIO Priority", 0, winreg.REG_SZ, "High")
                elif self.cpu_vendor == "Intel":
                    winreg.SetValueEx(key, "Affinity", 0, winreg.REG_DWORD, 0)
                    winreg.SetValueEx(key, "Background Only", 0, winreg.REG_SZ, "False")
                    winreg.SetValueEx(key, "Clock Rate", 0, winreg.REG_DWORD, 10000)
                    winreg.SetValueEx(key, "Scheduling Category", 0, winreg.REG_SZ, "High")
                    winreg.SetValueEx(key, "SFIO Priority", 0, winreg.REG_SZ, "High")
                    winreg.SetValueEx(key, "GPU Priority", 0, winreg.REG_DWORD, 8)
                    winreg.SetValueEx(key, "Priority", 0, winreg.REG_DWORD, 6)
                    
                    try:
                        intel_key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Intel\GMM")
                        winreg.SetValueEx(intel_key, "DedicatedSegmentSize", 0, winreg.REG_DWORD, 1298)
                        winreg.CloseKey(intel_key)
                    except:
                        pass
            else:
                winreg.SetValueEx(key, "Priority", 0, winreg.REG_DWORD, 2)
                winreg.SetValueEx(key, "Scheduling Category", 0, winreg.REG_SZ, "Medium")
            
            winreg.CloseKey(key)
        except Exception as e:
            raise Exception(f"CPU priority toggle failed: {e}")

    def toggle_all_cores(self, enable):
        """Toggle using all CPU cores at startup"""
        try:
            if enable:
                core_count = os.cpu_count()
                subprocess.run(["bcdedit", "/set", "{current}", "numproc", str(core_count)],
                             capture_output=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                subprocess.run(["bcdedit", "/deletevalue", "{current}", "numproc"],
                             capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        except Exception as e:
            raise Exception(f"All cores toggle failed: {e}")

    def toggle_gpu_gaming(self, enable):
        """Toggle GPU gaming optimizations"""
        try:
            self.toggle_cpu_gaming(enable)
            self.toggle_game_dvr(enable)
            
            if enable and "gpu_tier" in self.tweaks_state:
                tier = self.tweaks_state["gpu_tier"]
                self.apply_gpu_tier(tier)
        except Exception as e:
            raise Exception(f"GPU gaming optimization failed: {e}")

    def apply_gpu_tier(self, tier):
        """Apply GPU tier specific settings"""
        key_path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile"
        try:
            key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path)
            
            if "Low-Medium" in tier:
                winreg.SetValueEx(key, "SystemResponsiveness", 0, winreg.REG_DWORD, 1)
            else:
                winreg.SetValueEx(key, "SystemResponsiveness", 0, winreg.REG_DWORD, 0)
            
            winreg.CloseKey(key)
        except Exception as e:
            raise Exception(f"GPU tier application failed: {e}")

    def toggle_gpu_thread_priority(self, enable):
        """Toggle GPU thread priority based on vendor"""
        try:
            if self.gpu_vendor == "NVIDIA":
                key_path = r"SYSTEM\CurrentControlSet\Services\nvlddmkm\Parameters"
                key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path)
                
                if enable:
                    winreg.SetValueEx(key, "ThreadPriority", 0, winreg.REG_DWORD, 31)
                else:
                    try:
                        winreg.DeleteValue(key, "ThreadPriority")
                    except:
                        pass
                
                winreg.CloseKey(key)
                
            elif self.gpu_vendor == "AMD":
                key_path = r"SYSTEM\CurrentControlSet\Services\amdkmdap\Parameters"
                key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path)
                
                if enable:
                    winreg.SetValueEx(key, "ThreadPriority", 0, winreg.REG_DWORD, 31)
                else:
                    try:
                        winreg.DeleteValue(key, "ThreadPriority")
                    except:
                        pass
                
                winreg.CloseKey(key)
                
            elif self.gpu_vendor == "Intel":
                key_path = r"SOFTWARE\Intel\GMM"
                key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path)
                
                if enable:
                    winreg.SetValueEx(key, "DedicatedSegmentSize", 0, winreg.REG_DWORD, 1298)
                else:
                    try:
                        winreg.DeleteValue(key, "DedicatedSegmentSize")
                    except:
                        pass
                
                winreg.CloseKey(key)
        except Exception as e:
            raise Exception(f"GPU thread priority toggle failed: {e}")

    def toggle_hyperv(self, enable):
        """Toggle Hyper-V"""
        try:
            if enable:
                subprocess.run([
                    "dism", "/online", "/disable-feature",
                    "/featurename:Microsoft-Hyper-V-All", "/norestart"
                ], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                subprocess.run([
                    "dism", "/online", "/enable-feature",
                    "/featurename:Microsoft-Hyper-V-All", "/norestart"
                ], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        except Exception as e:
            raise Exception(f"Hyper-V toggle failed: {e}")

    def toggle_vm_platform(self, enable):
        """Toggle Virtual Machine Platform"""
        try:
            if enable:
                subprocess.run([
                    "dism", "/online", "/disable-feature",
                    "/featurename:VirtualMachinePlatform", "/norestart"
                ], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                subprocess.run([
                    "dism", "/online", "/enable-feature",
                    "/featurename:VirtualMachinePlatform", "/norestart"
                ], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        except Exception as e:
            raise Exception(f"VM Platform toggle failed: {e}")

    def toggle_services(self, enable):
        """Toggle unnecessary background services"""
        service_states = self.tweaks_state.get("service_states", {})
        if not service_states:
            return

        for service, selected in service_states.items():
            try:
                if enable and selected:
                    subprocess.run(["sc", "config", service, "start=", "disabled"],
                                   capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                    subprocess.run(["sc", "stop", service],
                                   capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                else:
                    subprocess.run(["sc", "config", service, "start=", "auto"],
                                   capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                    subprocess.run(["sc", "start", service],
                                   capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            except Exception:
                continue

    def toggle_ultimate_performance(self, enable):
        """Toggle ultimate performance power plan"""
        try:
            if enable:
                subprocess.run([
                    "powercfg", "-duplicatescheme",
                    "e9a42b02-d5df-448d-aa00-03f14749eb61"
                ], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                
                subprocess.run([
                    "powercfg", "/setactive",
                    "e9a42b02-d5df-448d-aa00-03f14749eb61"
                ], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                subprocess.run([
                    "powercfg", "/setactive",
                    "381b4222-f694-41f0-9685-ff5bb260df2e"
                ], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        except Exception as e:
            raise Exception(f"Power plan toggle failed: {e}")

    # ==================== CONFIG MANAGEMENT ====================

    def save_config(self):
        """Save configuration to file"""
        try:
            self.tweaks_state["service_states"] = getattr(self, "service_states", {})
            with open(self.config_file, 'w') as f:
                json.dump(self.tweaks_state, f, indent=4)
        except Exception as e:
            print(f"Failed to save config: {e}")

    def load_config(self):
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.tweaks_state = json.load(f)
            else:
                self.tweaks_state = {}
            self.service_states = self.tweaks_state.get("service_states", {})
            self.tweaks_state["service_states"] = self.service_states
        except Exception as e:
            print(f"Failed to load config: {e}")
            self.tweaks_state = {}
            self.service_states = {}

    def export_config(self):
        """Export configuration to a file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Configuration",
            "game_optimizer_config.json",
            "JSON Files (*.json)"
        )

        if file_path:
            try:
                with open(file_path, 'w') as f:
                    export_data = {
                        "version": "1.0",
                        "cpu_vendor": self.cpu_vendor,
                        "gpu_vendor": self.gpu_vendor,
                        "settings": self.tweaks_state
                    }
                    json.dump(export_data, f, indent=4)
                QMessageBox.information(self, "Success", 
                    f"Configuration exported successfully!\n\nSaved to: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export configuration:\n{str(e)}")

    def import_config(self):
        """Import configuration from a file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Configuration",
            "",
            "JSON Files (*.json)"
        )

        if file_path:
            try:
                with open(file_path, 'r') as f:
                    imported = json.load(f)
                
                if "settings" in imported:
                    settings = imported["settings"]
                else:
                    settings = imported
                
                self.tweaks_state = settings
                self.save_config()
                self.service_states = self.tweaks_state.get("service_states", {})

                # Update UI
                for key, value in settings.items():
                    if key in self.cards:
                        if isinstance(self.cards[key], OptimizationCard):
                            self.cards[key].setChecked(value)
                        elif isinstance(self.cards[key], ComboCard):
                            self.cards[key].setCurrentText(value)
                if hasattr(self, "service_list_widget"):
                    self.service_list_widget.apply_states(self.service_states)
                    self.service_list_widget.setVisible(self.tweaks_state.get("disable_services", False))

                QMessageBox.information(self, "Success",
                    "Configuration imported successfully!\n\n"
                    "All toggle switches have been updated.\n"
                    "Click 'Apply All Enabled' to apply the settings.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to import configuration:\n{str(e)}")


def main():
    """Main entry point"""
    if not is_running_as_admin():
        if relaunch_as_admin():
            return
        else:
            print("This application requires administrator privileges.")
            return

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    app.setApplicationName(APP_NAME)
    app.setOrganizationName("GameOptimizer")

    window = GameOptimizer()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
