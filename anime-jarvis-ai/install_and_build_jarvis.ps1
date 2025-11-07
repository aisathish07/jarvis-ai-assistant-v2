Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

$node = Get-Command node -ErrorAction SilentlyContinue
if (-not $node) {
  if (Get-Command winget -ErrorAction SilentlyContinue) {
    winget install -e --id OpenJS.NodeJS.LTS -h
    Start-Sleep -Seconds 3
  } else {
    exit 1
  }
}

npm install -g npm@latest | Out-Null

if (Test-Path "package-lock.json") {
  & npm ci
} else {
  & npm install
}

# Ollama block is already commented out

npm run build --if-present

if (Test-Path "tsconfig.node.json") {
  npx tsc -p tsconfig.node.json
}

if (Test-Path ".\\scripts\\create-dist-package.js") {
  node .\\scripts\\create-dist-package.js
}

npx electron-builder --win --x64

$releaseDir = Join-Path $ScriptDir "release"
$installer = Get-ChildItem -Path $releaseDir -Filter "*.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
if ($installer) {
  $desktopLnk = Join-Path ([Environment]::GetFolderPath("Desktop")) "Jarvis Installer.lnk"
  $ws = New-Object -ComObject WScript.Shell
  $s = $ws.CreateShortcut($desktopLnk)
  $s.TargetPath = $installer.FullName
  $s.WorkingDirectory = $releaseDir
  $s.Save()
}
