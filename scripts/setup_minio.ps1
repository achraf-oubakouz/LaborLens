$ErrorActionPreference = "Stop"

Set-Location -Path (Split-Path -Parent $PSScriptRoot)
. .\scripts\Resolve-Python.ps1
$PythonCommand = @(Resolve-LaborLensPython)

Write-Host "Starting MinIO..."
docker compose up -d minio
Start-Sleep -Seconds 5

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
