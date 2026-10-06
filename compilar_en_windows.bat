@echo off
python -m pip install --upgrade pip
python -m pip install pyinstaller pywebview
python app_launcher.py --build
pause
