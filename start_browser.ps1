param(
    [string] $DebuggerAddress = "localhost:9222",
    [string] $UserDataDir = (Join-Path $PSScriptRoot ".chrome-debug")
)

$ErrorActionPreference = "Stop"

function Test-DebugBrowser {
    try {
        Invoke-RestMethod -Uri "http://$DebuggerAddress/json/version" -TimeoutSec 2 | Out-Null
        return $true
    } catch {
        return $false
    }
}

function Find-Chrome {
    $command = Get-Command chrome.exe -ErrorAction SilentlyContinue
    if ($command) {
        return $command.Source
    }

    $candidates = @(
        "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
        "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
        "$env:LocalAppData\Google\Chrome\Application\chrome.exe",
        "$env:ProgramFiles\Chromium\Application\chrome.exe",
        "${env:ProgramFiles(x86)}\Chromium\Application\chrome.exe"
    )

    foreach ($candidate in $candidates) {
        if ($candidate -and (Test-Path -LiteralPath $candidate)) {
            return $candidate
        }
    }

    throw "Chrome was not found. Install Chrome or add chrome.exe to PATH."
}

if (Test-DebugBrowser) {
    Write-Host "[browser] Chrome remote debugging is already reachable at $DebuggerAddress"
    exit 0
}

New-Item -ItemType Directory -Force -Path $UserDataDir | Out-Null
$chrome = Find-Chrome
$port = ($DebuggerAddress -split ":")[-1]

Write-Host "[browser] starting Chrome remote debugging at $DebuggerAddress"
Start-Process -FilePath $chrome -ArgumentList @(
    "--remote-debugging-port=$port",
    "--user-data-dir=$UserDataDir",
    "--no-first-run",
    "--no-default-browser-check"
)

for ($attempt = 0; $attempt -lt 20; $attempt++) {
    Start-Sleep -Milliseconds 500
    if (Test-DebugBrowser) {
        Write-Host "[browser] ready"
        exit 0
    }
}

throw "Chrome started, but remote debugging did not become reachable at $DebuggerAddress."
