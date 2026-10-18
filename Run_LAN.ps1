# Local Wi-Fi/LAN access for this ACADEMIC DEMO ONLY.
# Run on the Windows computer that contains PostgreSQL, Python and Node.js.
# Does not modify/delete existing PostgreSQL data or .env files.
param(
    [string]$IPv4 = '',
    [switch]$AddFirewallRule
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path

if (!(Test-Path (Join-Path $root 'backend\.env'))) {
    throw 'backend/.env missing. Back up existing secrets; run START_HERE_WINDOWS.ps1 only after confirming the existing Docker database.'
}
if (!(Test-Path (Join-Path $root 'backend\.venv\Scripts\python.exe'))) {
    throw 'Python venv missing. Run START_HERE_WINDOWS.ps1 first (it preserves existing Docker data).'
}
if (!(Get-Command npm -ErrorAction SilentlyContinue)) { throw 'Node.js/npm is missing.' }
if (!(Get-Command docker -ErrorAction SilentlyContinue)) { throw 'Docker Desktop is missing.' }

$dockerRunning = docker inspect --format '{{.State.Running}}' landguard-demo-postgres 2>$null
if ($LASTEXITCODE -ne 0 -or "$dockerRunning".Trim() -ne 'true') {
    throw 'Existing PostgreSQL container is not running. Open Docker Desktop and start landguard-demo-postgres; do not remove its volume.'
}

if (!$IPv4) {
    # Prefer the interface that carries the Windows default route rather than WSL/Docker/virtual switches.
    $routes = @(Get-NetRoute -AddressFamily IPv4 -DestinationPrefix '0.0.0.0/0' -ErrorAction SilentlyContinue |
        Sort-Object RouteMetric, InterfaceMetric)
    foreach ($route in $routes) {
        $ips = @(Get-NetIPAddress -InterfaceIndex $route.InterfaceIndex -AddressFamily IPv4 -ErrorAction SilentlyContinue)
        foreach ($item in $ips) {
            if ($item.IPAddress -match '^(10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[01])\.)' -and
                $item.AddressState -eq 'Preferred') {
                $IPv4 = $item.IPAddress
                break
            }
        }
        if ($IPv4) { break }
    }
}
if (!$IPv4) {
    throw 'No active private-network IPv4 address found. Find the main PC IPv4 via ipconfig, then rerun: .\Run_LAN.ps1 -IPv4 192.168.1.105'
}
try { $parsedIp = [System.Net.IPAddress]::Parse($IPv4) }
catch { throw 'Invalid IPv4 address.' }
if ($parsedIp.AddressFamily -ne [System.Net.Sockets.AddressFamily]::InterNetwork -or
    $IPv4 -notmatch '^(10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[01])\.)') {
    throw 'For safety only RFC1918 private LAN IPv4 addresses are accepted. Never expose this demo to the public Internet.'
}
$matchedIp = Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue | Where-Object { $_.IPAddress -eq $IPv4 } | Select-Object -First 1
if (!$matchedIp) { throw "IP $IPv4 does not belong to this Windows PC. Use ipconfig to find the correct address." }
$network = Get-NetConnectionProfile -InterfaceIndex $matchedIp.InterfaceIndex -ErrorAction SilentlyContinue
if (!$network -or $network.NetworkCategory -ne 'Private') {
    throw 'This network must be marked Private in Windows Settings > Network & internet > Properties. Do not share this development server on a Public network.'
}

if ($AddFirewallRule) {
    # Requires explicitly elevated PowerShell. Never allow public profiles or arbitrary remote IPs.
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    if (!$principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw 'Run PowerShell as Administrator ONLY to add the LAN firewall rule, then start again without -AddFirewallRule.'
    }
    $ruleName = 'Smart LandGuard BD Demo LAN 4173 (Private subnet only)'
    if (!(Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue)) {
        New-NetFirewallRule -DisplayName $ruleName -Direction Inbound -Action Allow -Protocol TCP `
            -LocalPort 4173 -Profile Private -RemoteAddress LocalSubnet | Out-Null
    }
    Write-Host 'Private LAN Windows Firewall rule added/confirmed for port 4173 only.' -ForegroundColor Green
}

# LAN browsers request same-origin /api through Vite. Flask stays on 127.0.0.1:8000.
# The Origin must be explicitly allowed or login/register POSTs fail CSRF validation.
$lanOrigin = 'http://{0}:4173' -f $IPv4
$env:LANDGUARD_ALLOWED_ORIGINS = 'http://localhost:4173,http://127.0.0.1:4173,' + $lanOrigin
$env:LANDGUARD_ENV = 'development'

Write-Host ''
Write-Host 'Launching backend and frontend in separate terminal windows...' -ForegroundColor Cyan
$backend = Join-Path $root 'Run_Backend.ps1'
$frontend = Join-Path $root 'Run_Frontend.ps1'
# Child processes inherit only the temporary origins environment variable; no .env is changed.
Start-Process -FilePath 'powershell.exe' -WorkingDirectory $root -ArgumentList @(
    '-NoProfile', '-NoExit', '-ExecutionPolicy', 'Bypass', '-File', ('"' + $backend + '"')) | Out-Null
Start-Sleep -Seconds 3
Start-Process -FilePath 'powershell.exe' -WorkingDirectory $root -ArgumentList @(
    '-NoProfile', '-NoExit', '-ExecutionPolicy', 'Bypass', '-File', ('"' + $frontend + '"')) | Out-Null

Write-Host ''
Write-Host 'MAIN PC URL:  http://localhost:4173' -ForegroundColor Green
Write-Host "OTHER DEVICES: $lanOrigin" -ForegroundColor Green
Write-Host 'All devices must use the SAME trusted Private Wi-Fi/LAN.'
Write-Host 'Keep both new terminal windows and Docker Desktop running.'
Write-Host 'If another device cannot connect, use -AddFirewallRule in an ELEVATED PowerShell.'
Write-Host 'Do NOT port-forward 4173 or 8000. Only synthetic/demo documents; local HTTP is not encrypted.' -ForegroundColor Yellow
Write-Host 'Backend stays on 127.0.0.1:8000, PostgreSQL stays on 127.0.0.1:5432.'
