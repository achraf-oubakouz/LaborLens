$ErrorActionPreference = "Stop"

Set-Location -Path (Split-Path -Parent $PSScriptRoot)

Write-Host "Running batch Great Expectations checks..."
python -m quality.ge_runner --target batch --persist
