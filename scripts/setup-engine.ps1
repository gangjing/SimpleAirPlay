param([string]$Destination = (Join-Path $PSScriptRoot '..\engine'))
$ErrorActionPreference = 'Stop'
$url = 'https://github.com/leapbtw/uxplay-windows/releases/download/2.0.0.1736/uxplay-windows.zip'
$expected = '9d3a51c15fc9db857351195e7eb7bbb21700d9ae25d936a54bcf8536b62cca18'
$cacheDir = Join-Path $PSScriptRoot '..\.cache'
New-Item -ItemType Directory -Force $cacheDir | Out-Null
$archive = Join-Path $cacheDir 'uxplay-windows-2.0.0.1736.zip'
if (-not (Test-Path -LiteralPath $archive)) {
    Invoke-WebRequest -Uri $url -OutFile $archive
}
if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash -ne $expected) {
    throw 'Engine archive checksum mismatch. Remove the cached archive and try again.'
}
New-Item -ItemType Directory -Force $Destination | Out-Null
Expand-Archive -LiteralPath $archive -DestinationPath $Destination -Force
if (-not (Test-Path -LiteralPath (Join-Path $Destination 'uxplay-windows.exe'))) {
    throw 'Engine archive is missing uxplay-windows.exe.'
}
Write-Host "Verified engine 2.0.0.1736 is ready in $Destination"
