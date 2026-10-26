# PolarLabs QR Studio Windows ARM64 build.
# Requires Windows ARM64 and native ARM64 Python 3.13.
$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot
python -m pip install -r requirements-build.txt
python -m PyInstaller --noconfirm --clean --onefile --windowed `
  --name PolarLabs-QR-Studio `
  --icon PolarLabs-QR.ico `
  --add-data "PolarLabs-QR.ico;." `
  --add-data "PolarLabs-QR.png;." `
  --collect-all customtkinter `
  --collect-all resvg_py `
  --collect-all zxingcpp `
  studio.py
Write-Output "Build completata: dist\PolarLabs-QR-Studio.exe"
