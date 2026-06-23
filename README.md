# Aero

A small Windows utility for testing acrylic transparency with GradientColor.

## Features
- Modern compact UI
- Opacity slider
- Startup toggle

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

## Notes
- Settings are saved to `config.json`.
