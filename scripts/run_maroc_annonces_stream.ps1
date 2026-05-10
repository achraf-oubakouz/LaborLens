param(
    [int]$Pages = 2,
    [int]$IntervalSeconds = 120
)

$ErrorActionPreference = "Stop"

Set-Location -Path (Split-Path -Parent $PSScriptRoot)

Write-Host "Starting MarocAnnonces streaming producer..."
python -m src.streaming.producer --source maroc_annonces --pages $Pages --loop --interval-seconds $IntervalSeconds
