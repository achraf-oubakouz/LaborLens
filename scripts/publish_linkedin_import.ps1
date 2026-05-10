param(
    [string]$CsvPath = "data/imports/linkedin_jobs.csv",
    [string]$Keyword = ""
)

$ErrorActionPreference = "Stop"

Set-Location -Path (Split-Path -Parent $PSScriptRoot)

Write-Host "Publishing LinkedIn CSV import..."
python -m src.streaming.producer --source linkedin --linkedin-csv $CsvPath --keyword $Keyword
