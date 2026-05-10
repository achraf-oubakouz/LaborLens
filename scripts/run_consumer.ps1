$ErrorActionPreference = "Stop"

Set-Location -Path (Split-Path -Parent $PSScriptRoot)

Write-Host "Starting LaborLens streaming consumer..."
python -m src.streaming.consumer
