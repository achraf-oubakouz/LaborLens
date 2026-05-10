$ErrorActionPreference = "Stop"

Set-Location -Path (Split-Path -Parent $PSScriptRoot)
. .\scripts\Resolve-Python.ps1
$PythonCommand = @(Resolve-LaborLensPython)

Write-Host "Starting LaborLens platform services..."
docker compose up -d postgres kafka schema-registry minio superset airflow-postgres airflow-init airflow-webserver airflow-scheduler

Write-Host "Waiting briefly for services to initialize..."
Start-Sleep -Seconds 30

Write-Host "Creating LaborLens MinIO bucket if needed..."
try {
    if ($PythonCommand.Length -gt 1) {
        & $PythonCommand[0] $PythonCommand[1] .\setup_minio_bucket.py
    } else {
        & $PythonCommand[0] .\setup_minio_bucket.py
    }
} catch {
    Write-Host "Python MinIO setup failed, falling back to Docker mc..."
    docker run --rm --network laborlens_default minio/mc alias set local http://minio:9000 minioadmin minioadmin
    docker run --rm --network laborlens_default minio/mc mb -p local/laborlens
}

.\scripts\apply_schema.ps1
.\scripts\create_topics.ps1

Write-Host "Starting automated streaming consumer and supervisor..."
docker compose up -d streaming-consumer streaming-supervisor

Write-Host "Streaming stack is ready."
docker compose ps
