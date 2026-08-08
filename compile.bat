@echo off
echo ========================================================
echo     GORGONA-ONE AI // COMPILING EXECUTABLE
echo ========================================================
echo.
cd /d "%~dp0"
echo [1/3] Installing PyInstaller...
"%USERPROFILE%\.local\bin\uv.exe" pip install pyinstaller

echo.
echo [2/3] Compiling GorgonaOne.exe...
"%USERPROFILE%\.local\bin\uv.exe" run pyinstaller --noconfirm --onefile --add-data "static;static/" --name "GorgonaOne" main.py

echo.
echo [3/3] Build Complete! Check the 'dist/GorgonaOne' folder.
echo You can run the executable 'GorgonaOne.exe'.
pause
