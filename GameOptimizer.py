"""
Game Performance Optimizer - Windows 11 Edition
Modern GUI with Fluent Design principles using PyQt6
"""

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                              QHBoxLayout, QLabel, QPushButton, QScrollArea,
                              QFrame, QComboBox, QFileDialog, QMessageBox)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, pyqtProperty
from PyQt6.QtGui import QFont, QPainter, QColor, QPen, QIcon
import sys
import winreg
import subprocess
import json
import os
import platform
import ctypes


class ToggleSwitch(QWidget):
    """Modern Windows 11 style toggle switch"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._checked = False
        self._circle_position = 3
        self.setFixedSize(50, 24)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.animation = QPropertyAnimation(self, b"circle_position", self)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.animation.setDuration(200)

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
            painter.setBrush(QColor("#0067C0"))  # Windows 11 accent blue
        else:
            painter.setBrush(QColor("#5a5a5a"))

        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, 0, 50, 24, 12, 12)

        # Circle
        painter.setBrush(QColor("#ffffff"))
        painter.drawEllipse(self._circle_position, 3, 18, 18)

    def mousePressEvent(self, event):
        self._checked = not self._checked

        if self._checked:
            self.animation.setStartValue(self._circle_position)
            self.animation.setEndValue(29)
        else:
            self.animation.setStartValue(self._circle_position)
            self.animation.setEndValue(3)

        self.animation.start()

    def isChecked(self):
        return self._checked

    def setChecked(self, checked):
        if self._checked != checked:
            self._checked = checked
            self._circle_position = 29 if checked else 3
            self.update()


class OptimizationCard(QFrame):
    """Card widget for each optimization option"""

    def __init__(self, title, description, key, callback=None, parent=None):
        super().__init__(parent)
        self.key = key
        self.callback = callback

        self.setStyleSheet("""
            QFrame {
                background-color: #2b2b2b;
                border-radius: 8px;
                border: 1px solid #3f3f3f;
            }
            QFrame:hover {
                background-color: #323232;
                border: 1px solid #4f4f4f;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)

        # Left side - text
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)

        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        title_label.setStyleSheet("color: #ffffff; border: none; background: transparent;")

        desc_label = QLabel(description)
        desc_label.setFont(QFont("Segoe UI", 9))
        desc_label.setStyleSheet("color: #b3b3b3; border: none; background: transparent;")
        desc_label.setWordWrap(True)

        text_layout.addWidget(title_label)
        text_layout.addWidget(desc_label)

        # Right side - toggle
        self.toggle = ToggleSwitch()
        self.toggle.mousePressEvent = self.on_toggle

        layout.addLayout(text_layout, 1)
        layout.addWidget(self.toggle, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

    def on_toggle(self, event):
        # Call parent's mousePressEvent to animate
        ToggleSwitch.mousePressEvent(self.toggle, event)

        # Call callback
        if self.callback:
            self.callback(self.key, self.toggle.isChecked())

    def setChecked(self, checked):
        self.toggle.setChecked(checked)


class ComboCard(QFrame):
    """Card with dropdown selection"""

    def __init__(self, title, description, options, key, callback=None, parent=None):
        super().__init__(parent)
        self.key = key
        self.callback = callback

        self.setStyleSheet("""
            QFrame {
                background-color: #2b2b2b;
                border-radius: 8px;
                border: 1px solid #3f3f3f;
            }
            QFrame:hover {
                background-color: #323232;
                border: 1px solid #4f4f4f;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)

        # Left side - text
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)

        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        title_label.setStyleSheet("color: #ffffff; border: none; background: transparent;")

        desc_label = QLabel(description)
        desc_label.setFont(QFont("Segoe UI", 9))
        desc_label.setStyleSheet("color: #b3b3b3; border: none; background: transparent;")
        desc_label.setWordWrap(True)

        text_layout.addWidget(title_label)
        text_layout.addWidget(desc_label)

        # Right side - combo box
        self.combo = QComboBox()
        self.combo.addItems(options)
        self.combo.setFixedWidth(180)
        self.combo.setFont(QFont("Segoe UI", 9))
        self.combo.setStyleSheet("""
            QComboBox {
                background-color: #3f3f3f;
                color: #ffffff;
                border: 1px solid #5a5a5a;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QComboBox:hover {
                background-color: #4a4a4a;
                border: 1px solid #6a6a6a;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid #ffffff;
                margin-right: 8px;
            }
            QComboBox QAbstractItemView {
                background-color: #3f3f3f;
                color: #ffffff;
                selection-background-color: #0067C0;
                border: 1px solid #5a5a5a;
            }
        """)
        self.combo.currentTextChanged.connect(self.on_change)

        layout.addLayout(text_layout, 1)
        layout.addWidget(self.combo, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

    def on_change(self, text):
        if self.callback:
            self.callback(self.key, text)

    def setCurrentText(self, text):
        self.combo.setCurrentText(text)


class SectionHeader(QLabel):
    """Section header label"""

    def __init__(self, text, icon="", parent=None):
        super().__init__(f"{icon}  {text}" if icon else text, parent)
        self.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self.setStyleSheet("""
            color: #ffffff;
            background-color: #252525;
            padding: 12px 20px;
            border-radius: 6px;
        """)


class ModernButton(QPushButton):
    """Modern Windows 11 style button"""

    def __init__(self, text, style="primary", parent=None):
        super().__init__(text, parent)
        self.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
        self.setFixedHeight(38)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        if style == "primary":
            self.setStyleSheet("""
                QPushButton {
                    background-color: #0067C0;
                    color: #ffffff;
                    border: none;
                    border-radius: 4px;
                    padding: 0 24px;
                }
                QPushButton:hover {
                    background-color: #1a7fd4;
                }
                QPushButton:pressed {
                    background-color: #005a9e;
                }
            """)
        elif style == "success":
            self.setStyleSheet("""
                QPushButton {
                    background-color: #107c10;
                    color: #ffffff;
                    border: none;
                    border-radius: 4px;
                    padding: 0 28px;
                }
                QPushButton:hover {
                    background-color: #128d12;
                }
                QPushButton:pressed {
                    background-color: #0e6b0e;
                }
            """)
        elif style == "secondary":
            self.setStyleSheet("""
                QPushButton {
                    background-color: #3f3f3f;
                    color: #ffffff;
                    border: 1px solid #5a5a5a;
                    border-radius: 4px;
                    padding: 0 24px;
                }
                QPushButton:hover {
                    background-color: #4a4a4a;
                    border: 1px solid #6a6a6a;
                }
                QPushButton:pressed {
                    background-color: #353535;
                }
            """)


class GameOptimizer(QMainWindow):
    """Main application window"""

    def __init__(self):
        super().__init__()

        # Check admin
        if not self.is_admin():
            QMessageBox.critical(None, "Admin Required",
                "This application requires administrator privileges.\n\nPlease run as administrator.")
            sys.exit(1)

        self.setWindowTitle("Game Performance Optimizer")
        self.setMinimumSize(950, 750)

        # Configuration
        self.config_file = "optimizer_config.json"
        self.tweaks_state = {}
        self.cards = {}

        # Detect system
        self.cpu_vendor = self.detect_cpu()
        self.gpu_vendor = self.detect_gpu()

        # Load config
        self.load_config()

        # Setup UI
        self.setup_ui()

        # Center window
        self.center_window()

    def is_admin(self):
        """Check if running with admin privileges"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

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
                return "INTEL"
            return "UNKNOWN"
        except:
            return "UNKNOWN"

    def detect_gpu(self):
        """Detect GPU vendor"""
        try:
            result = subprocess.run(['wmic', 'path', 'win32_VideoController', 'get', 'name'],
                                  capture_output=True, text=True)
            output = result.stdout.upper()

            if "NVIDIA" in output or "GEFORCE" in output:
                return "NVIDIA"
            elif "AMD" in output or "RADEON" in output:
                return "AMD"
            elif "INTEL" in output:
                return "INTEL"
            return "UNKNOWN"
        except:
            return "UNKNOWN"

    def setup_ui(self):
        """Setup the user interface"""
        # Main widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Set window background
        self.setStyleSheet("QMainWindow { background-color: #202020; }")

        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header
        header = QWidget()
        header.setStyleSheet("background-color: #1a1a1a;")
        header.setFixedHeight(80)
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(30, 0, 30, 0)

        title = QLabel("⚡ Game Performance Optimizer")
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        title.setStyleSheet("color: #ffffff;")

        system_info = QLabel(f"System: {self.cpu_vendor} CPU  |  {self.gpu_vendor} GPU")
        system_info.setFont(QFont("Segoe UI", 9))
        system_info.setStyleSheet("color: #888888;")

        header_layout.addWidget(title)
        header_layout.addWidget(system_info)

        main_layout.addWidget(header)

        # Scrollable content area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("""
            QScrollArea {
                background-color: #202020;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #202020;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #3f3f3f;
                border-radius: 6px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #4f4f4f;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(30, 20, 30, 20)
        scroll_layout.setSpacing(15)

        # Create sections
        self.create_cpu_section(scroll_layout)
        self.create_gpu_section(scroll_layout)
        self.create_system_section(scroll_layout)
        self.create_power_section(scroll_layout)

        scroll_layout.addStretch()

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

        # Bottom bar
        self.create_bottom_bar(main_layout)

    def create_cpu_section(self, layout):
        """Create CPU optimization section"""
        layout.addWidget(SectionHeader("CPU Optimizations", "⚙️"))

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
        layout.addWidget(SectionHeader("GPU Optimizations", "🎮"))

        self.add_card(layout, "gpu_gaming_opt",
            "Gaming GPU Optimizations",
            "Applies base gaming performance registry tweaks for GPU",
            self.on_toggle)

        # GPU tier combo
        combo = ComboCard("GPU Performance Tier",
            "Select optimization level based on your GPU capabilities",
            ["Low-Medium", "Medium-High"],
            "gpu_tier",
            self.on_combo_change)
        combo.setCurrentText(self.tweaks_state.get("gpu_tier", "Low-Medium"))
        self.cards["gpu_tier"] = combo
        layout.addWidget(combo)

        self.add_card(layout, "gpu_thread_priority",
            f"Enable {self.gpu_vendor} Thread Priority",
            f"Optimizes GPU driver thread scheduling for {self.gpu_vendor}",
            self.on_toggle)

    def create_system_section(self, layout):
        """Create system optimization section"""
        layout.addWidget(SectionHeader("System Optimizations", "💻"))

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

    def create_power_section(self, layout):
        """Create power management section"""
        layout.addWidget(SectionHeader("Power Management", "⚡"))

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
        bottom.setStyleSheet("background-color: #1a1a1a;")
        bottom.setFixedHeight(70)

        bottom_layout = QHBoxLayout(bottom)
        bottom_layout.setContentsMargins(30, 15, 30, 15)

        bottom_layout.addStretch()

        export_btn = ModernButton("Export Config", "secondary")
        export_btn.clicked.connect(self.export_config)
        bottom_layout.addWidget(export_btn)

        import_btn = ModernButton("Import Config", "secondary")
        import_btn.clicked.connect(self.import_config)
        bottom_layout.addWidget(import_btn)

        apply_btn = ModernButton("Apply All Optimizations", "success")
        apply_btn.clicked.connect(self.apply_all)
        bottom_layout.addWidget(apply_btn)

        layout.addWidget(bottom)

    def on_toggle(self, key, checked):
        """Handle toggle switch changes"""
        self.tweaks_state[key] = checked
        self.save_config()

        # Apply the tweak immediately
        if checked:
            self.apply_tweak(key, True)
        else:
            self.apply_tweak(key, False)

    def on_combo_change(self, key, value):
        """Handle combo box changes"""
        self.tweaks_state[key] = value
        self.save_config()

    def apply_tweak(self, key, enable):
        """Apply individual tweak"""
        try:
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
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to apply {key}:\n{str(e)}")

    def apply_all(self):
        """Apply all enabled optimizations"""
        reply = QMessageBox.question(self, "Apply All Optimizations",
            "This will apply all enabled optimizations.\n\nSome changes require a restart.\n\nContinue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            count = 0
            for key, enabled in self.tweaks_state.items():
                if enabled and key != "gpu_tier":
                    try:
                        self.apply_tweak(key, True)
                        count += 1
                    except:
                        pass

            QMessageBox.information(self, "Complete",
                f"Applied {count} optimization(s) successfully!\n\nRestart your PC for all changes to take effect.")

    # Tweak implementation methods
    def toggle_power_throttling(self, enabled):
        """Toggle power throttling"""
        if enabled:
            subprocess.run(["powershell", "-Command",
                "New-Item -Path 'HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\System' -Force | Out-Null; "
                "Set-ItemProperty -Path 'HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\System' "
                "-Name 'EnablePowerThrottling' -Value 0 -Type DWord -Force"],
                check=True, capture_output=True)
        else:
            subprocess.run(["powershell", "-Command",
                "Remove-ItemProperty -Path 'HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\System' "
                "-Name 'EnablePowerThrottling' -ErrorAction SilentlyContinue"],
                capture_output=True)

    def toggle_cpu_gaming(self, enabled):
        """Toggle CPU gaming optimization"""
        key_path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games"
        key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path)

        if enabled:
            winreg.SetValueEx(key, "GPU Priority", 0, winreg.REG_DWORD, 8)
            winreg.SetValueEx(key, "Priority", 0, winreg.REG_DWORD, 6)
            winreg.SetValueEx(key, "Scheduling Category", 0, winreg.REG_SZ, "High")
            winreg.SetValueEx(key, "SFIO Priority", 0, winreg.REG_SZ, "High")
        else:
            winreg.SetValueEx(key, "Priority", 0, winreg.REG_DWORD, 2)
            winreg.SetValueEx(key, "Scheduling Category", 0, winreg.REG_SZ, "Medium")
            winreg.SetValueEx(key, "SFIO Priority", 0, winreg.REG_SZ, "Normal")

        winreg.CloseKey(key)

    def toggle_pc_responsiveness(self, enabled):
        """Toggle PC responsiveness"""
        key_path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile"
        key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path)

        if enabled:
            winreg.SetValueEx(key, "NetworkThrottlingIndex", 0, winreg.REG_DWORD, 0xffffffff)
            winreg.SetValueEx(key, "SystemResponsiveness", 0, winreg.REG_DWORD, 0)
        else:
            winreg.SetValueEx(key, "NetworkThrottlingIndex", 0, winreg.REG_DWORD, 10)
            winreg.SetValueEx(key, "SystemResponsiveness", 0, winreg.REG_DWORD, 20)

        winreg.CloseKey(key)

    def toggle_game_dvr(self, enabled):
        """Toggle Game DVR"""
        key_path = r"System\GameConfigStore"
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)

        if enabled:
            winreg.SetValueEx(key, "GameDVR_Enabled", 0, winreg.REG_DWORD, 0)
            winreg.SetValueEx(key, "GameDVR_FSEBehaviorMode", 0, winreg.REG_DWORD, 2)
        else:
            winreg.SetValueEx(key, "GameDVR_Enabled", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "GameDVR_FSEBehaviorMode", 0, winreg.REG_DWORD, 0)

        winreg.CloseKey(key)

    def toggle_maintenance(self, enabled):
        """Toggle Windows maintenance"""
        key_path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Schedule\Maintenance"
        key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path)

        if enabled:
            winreg.SetValueEx(key, "MaintenanceDisabled", 0, winreg.REG_DWORD, 1)
        else:
            try:
                winreg.DeleteValue(key, "MaintenanceDisabled")
            except:
                pass

        winreg.CloseKey(key)

    def toggle_energy_estimation(self, enabled):
        """Toggle energy estimation"""
        if enabled:
            subprocess.run(["sc", "config", "diagtrack", "start=", "disabled"],
                         capture_output=True)
            subprocess.run(["sc", "stop", "diagtrack"], capture_output=True)
        else:
            subprocess.run(["sc", "config", "diagtrack", "start=", "auto"],
                         capture_output=True)

    def toggle_cpu_priority(self, enabled):
        """Toggle CPU priority"""
        key_path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games"
        key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path)

        if enabled:
            winreg.SetValueEx(key, "GPU Priority", 0, winreg.REG_DWORD, 8)
            winreg.SetValueEx(key, "Priority", 0, winreg.REG_DWORD, 6)
            winreg.SetValueEx(key, "Scheduling Category", 0, winreg.REG_SZ, "High")
            winreg.SetValueEx(key, "SFIO Priority", 0, winreg.REG_SZ, "High")
        else:
            winreg.SetValueEx(key, "Priority", 0, winreg.REG_DWORD, 2)
            winreg.SetValueEx(key, "Scheduling Category", 0, winreg.REG_SZ, "Medium")

        winreg.CloseKey(key)

    def toggle_all_cores(self, enabled):
        """Toggle all CPU cores"""
        if enabled:
            subprocess.run(["bcdedit", "/set", "{current}", "numproc", str(os.cpu_count())],
                         capture_output=True)
        else:
            subprocess.run(["bcdedit", "/deletevalue", "{current}", "numproc"],
                         capture_output=True)

    def toggle_gpu_gaming(self, enabled):
        """Toggle GPU gaming optimizations"""
        self.toggle_cpu_gaming(enabled)

    def toggle_gpu_thread_priority(self, enabled):
        """Toggle GPU thread priority"""
        if self.gpu_vendor == "NVIDIA":
            key_path = r"SYSTEM\CurrentControlSet\Services\nvlddmkm\Parameters"
            key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path)

            if enabled:
                winreg.SetValueEx(key, "ThreadPriority", 0, winreg.REG_DWORD, 31)
            else:
                try:
                    winreg.DeleteValue(key, "ThreadPriority")
                except:
                    pass

            winreg.CloseKey(key)

    def toggle_hyperv(self, enabled):
        """Toggle Hyper-V"""
        if enabled:
            subprocess.run(["dism", "/online", "/disable-feature",
                          "/featurename:Microsoft-Hyper-V-All", "/norestart"],
                         capture_output=True)
        else:
            subprocess.run(["dism", "/online", "/enable-feature",
                          "/featurename:Microsoft-Hyper-V-All", "/norestart"],
                         capture_output=True)

    def toggle_vm_platform(self, enabled):
        """Toggle VM Platform"""
        if enabled:
            subprocess.run(["dism", "/online", "/disable-feature",
                          "/featurename:VirtualMachinePlatform", "/norestart"],
                         capture_output=True)
        else:
            subprocess.run(["dism", "/online", "/enable-feature",
                          "/featurename:VirtualMachinePlatform", "/norestart"],
                         capture_output=True)

    def toggle_services(self, enabled):
        """Toggle unnecessary services"""
        services = ["SysMain", "WSearch", "DiagTrack"]

        for service in services:
            if enabled:
                subprocess.run(["sc", "config", service, "start=", "disabled"],
                             capture_output=True)
                subprocess.run(["sc", "stop", service], capture_output=True)
            else:
                subprocess.run(["sc", "config", service, "start=", "auto"],
                             capture_output=True)

    def toggle_ultimate_performance(self, enabled):
        """Toggle ultimate performance power plan"""
        if enabled:
            subprocess.run(["powercfg", "-duplicatescheme",
                          "e9a42b02-d5df-448d-aa00-03f14749eb61"],
                         capture_output=True)
            subprocess.run(["powercfg", "/setactive",
                          "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"],
                         capture_output=True)
        else:
            subprocess.run(["powercfg", "/setactive",
                          "381b4222-f694-41f0-9685-ff5bb260df2e"],
                         capture_output=True)

    def save_config(self):
        """Save configuration"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.tweaks_state, f, indent=4)
        except Exception as e:
            print(f"Failed to save config: {e}")

    def load_config(self):
        """Load configuration"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.tweaks_state = json.load(f)
            else:
                self.tweaks_state = {}
        except Exception as e:
            print(f"Failed to load config: {e}")
            self.tweaks_state = {}

    def export_config(self):
        """Export configuration"""
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Configuration",
            "", "JSON Files (*.json)")

        if file_path:
            try:
                with open(file_path, 'w') as f:
                    json.dump(self.tweaks_state, f, indent=4)
                QMessageBox.information(self, "Success", "Configuration exported successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export:\n{str(e)}")

    def import_config(self):
        """Import configuration"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Import Configuration",
            "", "JSON Files (*.json)")

        if file_path:
            try:
                with open(file_path, 'r') as f:
                    imported = json.load(f)

                self.tweaks_state = imported
                self.save_config()

                # Update UI
                for key, value in imported.items():
                    if key in self.cards:
                        if isinstance(self.cards[key], OptimizationCard):
                            self.cards[key].setChecked(value)
                        elif isinstance(self.cards[key], ComboCard):
                            self.cards[key].setCurrentText(value)

                QMessageBox.information(self, "Success",
                    "Configuration imported successfully!\n\nToggle switches updated.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to import:\n{str(e)}")


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = GameOptimizer()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
