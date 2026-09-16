[CmdletBinding()]
param(
    [switch]$Run
)

$ErrorActionPreference = "Stop"
if (-not $Run) {
    Write-Host "这是本机故障恢复演练。默认不执行任何停止或重启。"
    Write-Host "确认没有其他实验占用 8080/9000/8501 后，再加 -Run 执行。"
    exit 0
}

$stageDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$stop = Join-Path $PSScriptRoot "stop-windows.ps1"
$start = Join-Path $PSScriptRoot "start-windows.ps1"
$verify = Join-Path $PSScriptRoot "verify-delivery.ps1"

Write-Host "将停止本机交付脚本记录的 llama/API/UI，随后从零重启并执行在线验收。"
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $stop
if ($LASTEXITCODE -ne 0) { throw "停止阶段失败" }
$apiStillReady = $false
try {
    Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:9000/ready" -TimeoutSec 5 | Out-Null
    $apiStillReady = $true
} catch {
    Write-Host "故障状态已确认：API 不再 ready。"
}
if ($apiStillReady) { throw "API 仍可访问，未形成故障状态" }
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $start
if ($LASTEXITCODE -ne 0) { throw "重启阶段失败" }
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $verify -Live
if ($LASTEXITCODE -ne 0) { throw "恢复后的在线验收失败" }
Write-Host "RECOVERY PASS"
