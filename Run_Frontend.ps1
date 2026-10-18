$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Join-Path $root 'frontend')
if (!(Get-Command npm -ErrorAction SilentlyContinue)) { throw 'Node.js/npm is missing; install Node.js LTS.' }
if (!(Test-Path 'node_modules\.bin\vite.cmd')) {
  Write-Host 'Installing Frontend dependencies...'
  npm install
  if ($LASTEXITCODE -ne 0) { throw 'npm install failed.' }
}
Write-Host 'Starting the website at http://localhost:4173 ...'
npm run dev
