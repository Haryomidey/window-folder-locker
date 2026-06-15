@echo off
setlocal

cd /d "%~dp0"

echo Building Windows Folder Locker...
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo Python was not found. Install Python 3.9 or newer and try again.
    pause
    exit /b 1
)

python -c "import tkinter as tk; root = tk.Tk(); root.withdraw(); root.destroy()" >nul 2>&1
if errorlevel 1 (
    echo Tkinter is not working in this Python installation.
    echo.
    echo Fix:
    echo 1. Run the Python installer again.
    echo 2. Choose Modify.
    echo 3. Enable "tcl/tk and IDLE".
    echo 4. Finish the install, then run build.bat again.
    echo.
    echo You can test it with:
    echo python -m tkinter
    pause
    exit /b 1
)

python -m pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    python -m pip install pyinstaller
    if errorlevel 1 (
        echo Failed to install PyInstaller.
        pause
        exit /b 1
    )
)

echo Cleaning old build files...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist WindowsFolderLocker.spec del WindowsFolderLocker.spec

echo Creating executable...
python -m PyInstaller ^
    --name WindowsFolderLocker ^
    --windowed ^
    --onefile ^
    --clean ^
    folder_locker.py

if errorlevel 1 (
    echo Build failed.
    pause
    exit /b 1
)

echo Creating desktop shortcut...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$desktop = [Environment]::GetFolderPath('Desktop');" ^
    "$shortcutPath = Join-Path $desktop 'Windows Folder Locker.lnk';" ^
    "$targetPath = Join-Path (Resolve-Path '.\dist').Path 'WindowsFolderLocker.exe';" ^
    "$shell = New-Object -ComObject WScript.Shell;" ^
    "$shortcut = $shell.CreateShortcut($shortcutPath);" ^
    "$shortcut.TargetPath = $targetPath;" ^
    "$shortcut.WorkingDirectory = Split-Path $targetPath;" ^
    "$shortcut.Description = 'Windows Folder Locker';" ^
    "$shortcut.Save()"

if errorlevel 1 (
    echo Shortcut creation failed, but the executable was built successfully.
    echo You can still run dist\WindowsFolderLocker.exe directly.
) else (
    echo Desktop shortcut created: Windows Folder Locker
)

echo.
echo Build complete:
echo %cd%\dist\WindowsFolderLocker.exe
echo.
pause