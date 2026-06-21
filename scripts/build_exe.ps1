# Build a distributable SecureOffice Admin executable.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File .\scripts\build_exe.ps1
#
# Result:
#   dist\SecureOfficeAdmin.exe

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $repoRoot

$python = "py"
$venvPython = ".\.venv\Scripts\python.exe"

function Assert-LastCommand($message) {
    if ($LASTEXITCODE -ne 0) {
        throw $message
    }
}

if (-not (Test-Path -LiteralPath $venvPython)) {
    Write-Host "Creating local virtual environment..." -ForegroundColor Cyan
    & $python -3.12 -m venv .venv
    Assert-LastCommand "Could not create virtual environment."
}

Write-Host "Installing build dependencies..." -ForegroundColor Cyan
& $venvPython -m pip install --disable-pip-version-check -r requirements.txt
Assert-LastCommand "Could not install runtime dependencies."
& $venvPython -m pip install --disable-pip-version-check "pyinstaller>=6.0.0,<7.0.0"
Assert-LastCommand "Could not install PyInstaller."

Write-Host "Cleaning previous build output..." -ForegroundColor Cyan
if (Test-Path -LiteralPath "dist") { Remove-Item -LiteralPath "dist" -Recurse -Force }
if (Test-Path -LiteralPath "build") { Remove-Item -LiteralPath "build" -Recurse -Force }

Write-Host "Building SecureOfficeAdmin.exe..." -ForegroundColor Cyan
& $venvPython -m PyInstaller --clean packaging\SecureOfficeAdmin.spec
Assert-LastCommand "PyInstaller build failed."

Write-Host ""
Write-Host "Done: dist\SecureOfficeAdmin.exe" -ForegroundColor Green
