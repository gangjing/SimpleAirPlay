$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Push-Location $projectRoot
try {
    if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
        python -m venv .venv
        if ($LASTEXITCODE -ne 0) { throw 'Could not create Python environment.' }
    }
    $pythonExe = Join-Path $projectRoot '.venv\Scripts\python.exe'
    & $pythonExe -m pip install -r requirements-build.txt
    if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
    & $pythonExe -m py_compile simple_airplay.py
    if ($LASTEXITCODE -ne 0) { throw 'Python validation failed.' }
    & $pythonExe -m PyInstaller --noconfirm --windowed --onedir --name SimpleAirPlay simple_airplay.py
    if ($LASTEXITCODE -ne 0) { throw 'PyInstaller build failed.' }
    & (Join-Path $PSScriptRoot 'setup-engine.ps1') -Destination (Join-Path $projectRoot 'dist\SimpleAirPlay\engine')
    Copy-Item -LiteralPath 'README.md','LICENSE','THIRD_PARTY.md' -Destination 'dist\SimpleAirPlay' -Force
    Write-Host 'Build complete: dist\SimpleAirPlay\SimpleAirPlay.exe'
} finally {
    Pop-Location
}
