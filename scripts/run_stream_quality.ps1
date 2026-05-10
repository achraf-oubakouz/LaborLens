$ErrorActionPreference = "Stop"

Set-Location -Path (Split-Path -Parent $PSScriptRoot)

Write-Host "Running streaming Great Expectations checks..."
python -m quality.ge_runner --target stream --persist
