$ErrorActionPreference = "Stop"

Set-Location -Path (Split-Path -Parent $PSScriptRoot)

Write-Host "Creating Kafka topics..."
python .\create_kafka_topics.py
Write-Host "Kafka topics ready."
