[CmdletBinding()]
param(
    [switch]$Live,
    [string]$ApiUrl = "http://127.0.0.1:9000"
)
$ErrorActionPreference = "Stop"
$stageDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$repoDir = (Resolve-Path (Join-Path $stageDir "..")).Path
$python = Join-Path $stageDir ".venv\Scripts\python.exe"
$manifest = Get-Content -Raw -Encoding UTF8 (Join-Path $repoDir "MODEL_MANIFEST.json") | ConvertFrom-Json
foreach ($entry in @($manifest.local_cpu.model, $manifest.local_cpu.mmproj)) {
    $path = Join-Path $repoDir $entry.path
    if (-not (Test-Path -LiteralPath $path)) { throw "缺少模型文件：$path" }
    $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash
    if ($hash -ne $entry.sha256) { throw "模型 SHA-256 不匹配：$path" }
}
& $python scripts\artifact_report.py
if ($LASTEXITCODE -ne 0) { throw "制品完整性检查失败" }
& $python -m pip check
if ($LASTEXITCODE -ne 0) { throw "pip check 失败" }
& $python -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw "自动测试失败" }
Write-Host "STATIC PASS: model hashes, dependencies, unit/API/UI tests"
if ($Live) {
    & $python scripts\smoke_api.py --api-url $ApiUrl --image (Join-Path $repoDir "images\gg.jpg")
    if ($LASTEXITCODE -ne 0) { throw "在线冒烟测试失败" }
}
