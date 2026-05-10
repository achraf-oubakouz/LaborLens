function Resolve-LaborLensPython {
    $projectRoot = Split-Path -Parent $PSScriptRoot
    $venvPython = Join-Path $projectRoot "venv\Scripts\python.exe"
    $dotVenvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"

    if (Test-Path $dotVenvPython) {
        return @($dotVenvPython)
    }
    if (Test-Path $venvPython) {
        return @($venvPython)
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        return @("python")
    }
    if (Get-Command py -ErrorAction SilentlyContinue) {
        return @("py", "-3")
    }

    throw "No Python interpreter found. Install Python or create .venv with `python -m venv .venv`."
}
