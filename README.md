# WinGame

WinGame is a Windows gaming optimization tool with a PyQt6 desktop UI.
It applies a controlled set of registry, service, power, and boot tweaks used for performance-focused profiles.

## What it does

- queues changes in UI, then applies in one explicit batch
- auto-detects CPU/GPU vendor for vendor-specific tweak paths
- supports export/import of optimization profile JSON
- supports per-service control for selected background services
- prompts for restart only when required by selected toggles
- can create a Windows restore point before applying changes

## Safety model

- no hidden background daemon
- no auto-apply on toggle; changes apply only when `Apply All Enabled` is clicked
- all toggles are reversible through the same UI
- restore point prompt is available before applying a batch

## Requirements

- Windows 10/11 (64-bit)
- Administrator privileges
- Python 3.10+
- PyQt6 stack from `requirements.txt`

## Run from source

```powershell
cd "D:\Moved From C\Desktop\Projects\WinGame"
python -m pip install -r requirements.txt
python GamePerformanceOptimizer.py
```

## Build

PyInstaller build:

```powershell
cd "D:\Moved From C\Desktop\Projects\WinGame"
.\BUILD_EXE.bat
```

Nuitka build:

```powershell
cd "D:\Moved From C\Desktop\Projects\WinGame"
.\BUILD_NUITKA.bat
```

## Main script

- `GamePerformanceOptimizer.py`: primary maintained app entry point
- `GameOptimizer.py`: older variant retained for reference

## Notes

- some settings require reboot (`Hyper-V`, `VM Platform`, `all cores boot`)
- commands requiring elevation are run only after admin check
