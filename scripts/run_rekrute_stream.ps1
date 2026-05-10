param(
    [int]$Pages = 1,
    [string]$Keyword = "python",
    [int]$IntervalSeconds = 60
)

$ErrorActionPreference = "Stop"

Set-Location -Path (Split-Path -Parent $PSScriptRoot)

Write-Host "Starting Rekrute streaming producer..."
python -m src.streaming.producer --source rekrute --pages $Pages --keyword $Keyword --loop --interval-seconds $IntervalSeconds
