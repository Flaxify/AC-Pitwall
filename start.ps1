param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]] $PitwallArgs
)

$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot

$python = Get-Command py -ErrorAction SilentlyContinue
if ($python) {
    $pythonExe = "py"
    $pythonArgs = @("-3")
} else {
    $python = Get-Command python -ErrorAction SilentlyContinue
    if (-not $python) {
        throw "Python 3.11+ is required. Install Python, then rerun .\start.ps1"
    }
    $pythonExe = "python"
    $pythonArgs = @()
}

if (-not (Test-Path .venv)) {
    Write-Host "[setup] creating .venv"
    & $pythonExe @pythonArgs -m venv .venv
}

$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
Write-Host "[setup] installing pitwall into .venv"
& $venvPython -m pip --disable-pip-version-check install -e .

& (Join-Path $PSScriptRoot "start_browser.ps1")

if (-not $PitwallArgs -or $PitwallArgs.Count -eq 0) {
    $PitwallArgs = @("scrape")
}

& (Join-Path $PSScriptRoot ".venv\Scripts\pitwall.exe") @PitwallArgs
