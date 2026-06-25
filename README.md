# Aero
<img width="180" height="180" alt="_jjf830gdbfp7fnqjekoe_0" src="https://github.com/user-attachments/assets/57c2adf9-b5ef-453a-a9df-de9e573b8560"/>

Aero is a Windows Explorer opacity controller with tray support, startup persistence, and a simple CustomTkinter interface.

## Features
- Adjust Explorer opacity.
- Clear applied effect.
- Start with Windows.
- Minimize to system tray.
- Restore or exit from tray.
- Custom app icon support.
<img width="716" height="383" alt="image" src="https://github.com/user-attachments/assets/9494f481-79d9-4157-8081-23c07e90762e"/>

## Download
Go to the latest GitHub Release and download `Aero.exe`.

## Requirements
- Windows 10 or Windows 11.

You do not need to install Python or any libraries if you use the released `Aero.exe`.

## How to run
1. Download `Aero.exe` from Releases.
2. Double-click it.
3. Use the tray icon to hide or restore the app.

## Files
- `Aero.exe` — packaged app.
- `icon.ico` — app icon used by the build.
- `config.json` — generated automatically next to the exe.
- `aero.log` — generated automatically next to the exe.

## Building from source
Install dependencies:
```powershell
python -m pip install -r requirements.txt
```

Build:
```powershell
python -m PyInstaller --noconfirm --onefile --windowed --name Aero --icon=icon.ico --add-data "icon.ico;." main.py
```

## Notes
If the tray icon does not appear correctly, make sure `pystray` and `Pillow` are installed in the build environment.
