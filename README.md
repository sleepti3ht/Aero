# Aero

A small Windows utility for testing acrylic transparency with GradientColor.

## Features
- Modern compact UI
- Opacity slider
- Tint color picker
- Startup toggle
- Log window

## Run locally
```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Build
```powershell
pyinstaller --onefile --windowed --name Aero main.py
```

## Release
Push a tag like `v1.0.0` to trigger GitHub Actions.

## Notes
- Settings are saved to `config.json`.
- A log is written to `aero.log`.