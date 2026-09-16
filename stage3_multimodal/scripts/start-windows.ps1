[CmdletBinding()]
param(
    [ValidateSet("LocalCpu", "Existing")]
    [string]$Backend = "LocalCpu",
    [string]$BackendUrl = "http://127.0.0.1:18181",
    [string]$ModelId = ""
)

$ErrorActionPreference = "Stop"
$stageDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$repoDir = (Resolve-Path (Join-Path $stageDir "..")).Path
$python = Join-Path $stageDir ".venv\Scripts\python.exe"
$runDir = Join-Path $stageDir ".run"
$pidFile = Join-Path $runDir "pids.json"
$started = @()

function Assert-FreePort([int]$port) {
    $listener = Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue
    if ($listener) { throw "端口 $port 已被占用，请先停止已有服务或修改端口。" }
}

function Wait-Http([string]$url, [int]$timeoutSeconds) {
    $deadline = (Get-Date).AddSeconds($timeoutSeconds)
    do {
        try {
            $response = Invoke-WebRequest -UseBasicParsing -Uri $url -TimeoutSec 5
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) { return }
        } catch {}
        Start-Sleep -Seconds 2
    } while ((Get-Date) -lt $deadline)
    throw "等待 $url 超时。请查看 .run 目录日志。"
}

function Start-Tracked([string]$name, [string]$file, [string[]]$arguments, [string]$workDir) {
    $stdout = Join-Path $runDir "$name.out.log"
    $stderr = Join-Path $runDir "$name.err.log"
    $process = Start-Process -FilePath $file -ArgumentList $arguments -WorkingDirectory $workDir -RedirectStandardOutput $stdout -RedirectStandardError $stderr -WindowStyle Hidden -PassThru
    $script:started += $process
    return $process
}

New-Item -ItemType Directory -Force -Path $runDir | Out-Null
if (-not (Test-Path -LiteralPath $python)) { throw "未找到项目虚拟环境：$python。请先按 DELIVERY.md 安装依赖。" }
Assert-FreePort 9000
Assert-FreePort 8501

try {
    if ($Backend -eq "LocalCpu") {
        $server = Join-Path $repoDir "llama-server.exe"
        $model = Join-Path $repoDir "models\Qwen3.5-0.8B-Q4_K_M.gguf"
        $mmproj = Join-Path $repoDir "models\mmproj-BF16.gguf"
        foreach ($path in @($server, $model, $mmproj)) {
            if (-not (Test-Path -LiteralPath $path)) { throw "缺少本机模型运行文件：$path" }
        }
        if ([string]::IsNullOrWhiteSpace($ModelId)) { $ModelId = "Qwen3.5-0.8B-Q4_K_M.gguf" }
        $modelProcess = Start-Tracked "llama" $server @("-m", $model, "--mmproj", $mmproj, "--alias", $ModelId, "--host", "127.0.0.1", "--port", "8080", "--no-ui", "--log-colors", "off") $repoDir
        Wait-Http "http://127.0.0.1:8080/health" 180
        $BackendUrl = "http://127.0.0.1:8080"
    } else {
        if ([string]::IsNullOrWhiteSpace($ModelId)) { $ModelId = "unsloth/Qwen3.5-4B-GGUF-VLM:Q4_0" }
        Wait-Http (($BackendUrl.TrimEnd("/") + "/v1/models")) 15
    }

    $env:LLAMA_BASE_URL = $BackendUrl
    $env:LLAMA_MODEL = $ModelId
    $api = Start-Tracked "api" $python @("-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "9000") $stageDir
    Wait-Http "http://127.0.0.1:9000/health" 30

    $env:API_URL = "http://127.0.0.1:9000"
    $ui = Start-Tracked "ui" $python @("-m", "streamlit", "run", "streamlit_app.py", "--server.address=127.0.0.1", "--server.port=8501", "--server.headless=true") $stageDir
    Wait-Http "http://127.0.0.1:8501/" 45

    [PSCustomObject]@{ backend = $Backend; backend_url = $BackendUrl; model = $ModelId; llama_pid = if ($modelProcess) { $modelProcess.Id } else { $null }; api_pid = $api.Id; ui_pid = $ui.Id; started_at = (Get-Date).ToString("o") } | ConvertTo-Json | Set-Content -Path $pidFile -Encoding UTF8
    Write-Host "服务已启动："
    Write-Host "  UI : http://127.0.0.1:8501"
    Write-Host "  API: http://127.0.0.1:9000/docs"
    Write-Host "  停止: .\scripts\stop-windows.ps1"
} catch {
    foreach ($process in $started) {
        if (-not $process.HasExited) { Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue }
    }
    throw
}
