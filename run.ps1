$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Push-Location $scriptDir

if (Test-Path "$scriptDir/venv310/Scripts/Activate.ps1") {
    & "$scriptDir/venv310/Scripts/Activate.ps1"
} else {
    Write-Host "Virtual environment not found. Expected venv310 directory."
}

$env:PYTHONPATH = Join-Path $scriptDir 'src'

python -m gui.main_window

Pop-Location

Read-Host 'Press Enter to exit'
