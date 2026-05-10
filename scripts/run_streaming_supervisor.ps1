param(
    [int]$RekrutePages = 1,
    [string]$RekruteKeyword = "python",
    [int]$RekruteIntervalSeconds = 60,
    [int]$MarocAnnoncesPages = 2,
    [int]$MarocAnnoncesIntervalSeconds = 120,
    [switch]$IncludeLinkedIn,
    [string]$LinkedInKeyword = "",
    [int]$LinkedInIntervalSeconds = 300
)

$ErrorActionPreference = "Stop"

Set-Location -Path (Split-Path -Parent $PSScriptRoot)

$ArgsList = @(
    "-m", "src.streaming.supervisor",
    "--rekrute-pages", $RekrutePages,
    "--rekrute-keyword", $RekruteKeyword,
    "--rekrute-interval-seconds", $RekruteIntervalSeconds,
    "--maroc-annonces-pages", $MarocAnnoncesPages,
    "--maroc-annonces-interval-seconds", $MarocAnnoncesIntervalSeconds
)

if ($IncludeLinkedIn) {
    $ArgsList += @("--include-linkedin", "--linkedin-keyword", $LinkedInKeyword, "--linkedin-interval-seconds", $LinkedInIntervalSeconds)
}

Write-Host "Starting LaborLens streaming supervisor..."
python @ArgsList
