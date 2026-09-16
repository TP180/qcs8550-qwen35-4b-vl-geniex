[CmdletBinding()]
param()
$ErrorActionPreference = "Stop"
$stageDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$pidFile = Join-Path $stageDir ".run\pids.json"
if (-not (Test-Path -LiteralPath $pidFile)) {
    Write-Host "没有找到运行记录，服务可能已经停止。"
    exit 0
}
$record = Get-Content -Raw -Encoding UTF8 $pidFile | ConvertFrom-Json
foreach ($property in @("ui_pid", "api_pid", "llama_pid")) {
    $value = $record.$property
    if ($value) {
        $process = Get-Process -Id ([int]$value) -ErrorAction SilentlyContinue
        if ($process) {
            Stop-Process -Id $process.Id -Force
            Write-Host "已停止 $property ($($process.Id))"
        }
    }
}
Remove-Item -LiteralPath $pidFile -Force
Write-Host "服务已停止。"
