@echo off
chcp 65001 >nul
echo Installing requirements...
python -m pip install --upgrade pyside6 pyinstaller
echo Building exe...
python -m PyInstaller --onefile --windowed --name TaskManager task_manager.py
echo.
echo Done! Your exe is in the "dist" folder: dist\TaskManager.exe
pause
