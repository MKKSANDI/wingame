# WinGame

WinGame is a Windows gaming optimization desktop app built with PyQt6.
It applies a selected set of system-level performance tweaks through an explicit apply flow.

## Main behavior

- queues toggle changes in UI
- applies selected changes only when `Apply All Enabled` is triggered
- supports per-service selections for background service optimization
- supports profile export/import (`JSON`)
- prompts for restart when chosen toggles require it
- offers restore point creation before applying a batch

## Tweak areas

- CPU scheduling and responsiveness
- GPU profile and thread-priority tweaks by vendor
- power plan controls
- optional Hyper-V / VM platform disable flow
- selected background service tuning

## Safety model

- no auto-apply while toggling
- no hidden startup service added by the app
- reversible paths for each controlled setting
- pre-apply confirmation and optional restore point prompt

## Requirements

- Windows 10/11 (64-bit)
- Administrator privileges
- Python 3.10+
- packages from `requirements.txt`

## Run from source

```powershell
cd "D:\Moved From C\Desktop\Projects\WinGame"
python -m pip install -r requirements.txt
python GamePerformanceOptimizer.py
```

## Build

```powershell
cd "D:\Moved From C\Desktop\Projects\WinGame"
.\BUILD_EXE.bat
```

```powershell
cd "D:\Moved From C\Desktop\Projects\WinGame"
.\BUILD_NUITKA.bat
```

## Notes

- some settings require reboot (`Hyper-V`, `VM Platform`, `all cores boot`)
- `GamePerformanceOptimizer.py` is the primary maintained entry point
