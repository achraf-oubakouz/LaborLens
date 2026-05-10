$ErrorActionPreference = "Stop"

Set-Location -Path (Split-Path -Parent $PSScriptRoot)

Write-Host "Applying PostgreSQL schema..."
Get-Content .\sql\schema.sql | docker compose exec -T postgres psql -U emploi -d emploi_maroc
Write-Host "Schema applied."
