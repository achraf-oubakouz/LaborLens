$ErrorActionPreference = "Stop"

Set-Location -Path (Split-Path -Parent $PSScriptRoot)

Write-Host "Starting PostgreSQL, Kafka, Schema Registry, and Superset..."
docker compose up -d postgres kafka schema-registry superset

Write-Host "Waiting briefly for services to initialize..."
Start-Sleep -Seconds 20

.\scripts\apply_schema.ps1
.\scripts\create_topics.ps1

Write-Host "Streaming stack is ready."
docker compose ps
