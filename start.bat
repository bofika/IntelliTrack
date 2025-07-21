@echo off
setlocal

rem Change to the directory where this script resides
pushd "%~dp0"

rem Activate the virtual environment
if exist "venv310\Scripts\activate.bat" (
    call "venv310\Scripts\activate.bat"
) else (
    echo Virtual environment not found. Expected venv310 directory.
)

rem Set PYTHONPATH to the src directory
set "PYTHONPATH=%CD%\src"

rem Launch the application
python -m gui.main_window

popd

rem Keep the window open
pause
