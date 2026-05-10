$ErrorActionPreference = "Stop"

Set-Location -Path (Split-Path -Parent $PSScriptRoot)

Write-Host "Starting MinIO..."
docker compose up -d minio
Start-Sleep -Seconds 5

Write-Host "Creating LaborLens MinIO bucket if needed..."
python .\setup_minio_bucket.py
