# 交付说明（2026-09-15）

## 结论

项目已经从“模型能运行”推进到“本机功能闭环可复现”的交付候选版本，但还不是生产服务。Windows 0.8B CPU 方案有固定模型哈希、依赖快照、API/UI/RAG 测试和一键启动；QCS8550 GenieX 4B NPU 已完成第 6 步真实图片接口和第 7 步 30 分钟稳定性：38/38、100%；今天 SSH 复查仍被远端主动断开。Docker/Linux 尚未真实验收。生产化还缺认证、限流、监控、持久化、并发隔离和备份。

## 入口和模型

主入口是 stage3_multimodal。FastAPI 在 app/main.py，网页在 streamlit_app.py，索引脚本在 scripts/build_index.py，启停脚本在 scripts/start-windows.ps1 和 stop-windows.ps1，验收脚本在 scripts/verify-delivery.ps1。根目录 api_server.py 是早期文本示例，不是主入口。

本机模型：

~~~text
models/Qwen3.5-0.8B-Q4_K_M.gguf
models/mmproj-BF16.gguf
~~~

哈希和大小登记在 MODEL_MANIFEST.json：主模型 532517120 bytes，SHA-256 BD258782E35F7F458F8ACED1ADC053E6E92E89BC735BA3BE89D38A06121DC517；mmproj 207346528 bytes，SHA-256 D312C4D02FD46EEA7A16E4F3BBB58840E6222209322CA1E33CA03247AD8935D6。二者必须匹配使用。已验证 llama-server 0.3.0-dev build 10632 commit 11cd98842。

开发板模型：

~~~text
/data/local/tmp/geniex/models/unsloth/Qwen3.5-4B-GGUF/Qwen3.5-4B-Q4_0.gguf
/data/local/tmp/geniex/models/unsloth/Qwen3.5-4B-GGUF-VLM/mmproj-F16.gguf
model id: unsloth/Qwen3.5-4B-GGUF-VLM:Q4_0
port: 18181
~~~

板端权重和二进制来源、SHA-256 尚未登记，详见 board-connection/Qwen35-4B-GenieX-部署复盘与面试指南.md。

## 首次安装

~~~powershell
cd stage3_multimodal
py -3.13 -m venv .venv
.\\.venv\\Scripts\\python.exe -m pip install --upgrade pip
.\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt -c constraints.txt
.\\.venv\\Scripts\\python.exe scripts\\build_index.py
~~~

已验证 Python 3.13.2、FastAPI 0.141.1、uvicorn 0.52.4、Streamlit 1.63.0，pip check 通过。OCR 另需系统 Tesseract 和 chi_sim 语言包。

## 启动和 API

~~~powershell
cd stage3_multimodal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\\scripts\\start-windows.ps1
~~~

启动后 UI 为 http://127.0.0.1:8501，API 文档为 http://127.0.0.1:9000/docs，模型为 http://127.0.0.1:8080。停止使用 stop-windows.ps1。脚本只绑定回环地址，不要直接暴露公网。

~~~powershell
curl.exe http://127.0.0.1:9000/health
curl.exe http://127.0.0.1:9000/ready
curl.exe -X POST http://127.0.0.1:9000/v1/image/qa -F "question=请描述图片" -F "image=@path/to/image.jpg"
curl.exe -X POST http://127.0.0.1:9000/v1/ocr -F "image=@path/to/document.png"
curl.exe -X POST http://127.0.0.1:9000/v1/rag/query -F "question=项目使用了哪些技术？" -F "top_k=3"
~~~

/health 报告服务和模型连通性；/ready 在模型不可达时返回 503。API 对非 JPEG/PNG/WEBP 返回 415，损坏图片 400，超大图片 413，非法 top_k 422。

## 开发板后端

先在 board-connection/board-ssh-kit 执行 board-ssh.ps1 -Mode Check，必须实际得到 kalama、uid=0(root)、aarch64。通过 SSH 隧道让本机访问 18181 后运行：

~~~powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\\scripts\\start-windows.ps1 -Backend Existing -BackendUrl http://127.0.0.1:18181 -ModelId unsloth/Qwen3.5-4B-GGUF-VLM:Q4_0
~~~

最新验收已完成：真实图片 HTTP 请求 38/38 成功，平均 17.78 秒，P95 18.10 秒；详细记录见 EXPERIMENT_REPORT_20260915.md。此前流式热请求 TTFT 约 11.35 秒、总响应约 18.85 秒，底层 CLI Decode 约 6.7 tok/s；快速连续切换曾触发约 1.073 GB HTP 缓冲区分配失败，当前按单请求串行。开发板私钥不得上传、打印或提交。

## 验收和错误处理

静态验收：

~~~powershell
cd stage3_multimodal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\\scripts\\verify-delivery.ps1
~~~

在线验收追加 -Live，会调用 /ready、RAG 和 images/gg.jpg 的真实图片问答。失败日志在 .run/。常见处理：/ready 503 或图片 502 时检查模型、mmproj 和端口；OCR 503 时安装 Tesseract；RAG 503 时重新 build_index；Streamlit 无法连接时检查 API_URL 和 9000；SSH 255 时检查 Tailscale、共享邀请、对方 Linux/ADB 和供电；GenieX 图片流式 500 时改用非流式、串行请求；Docker 不能直接使用 Windows llama-server.exe，应使用 host.docker.internal 或 Linux 后端。

## 证据补齐

详细执行顺序见 stage3_multimodal/EVIDENCE_PLAN.md；artifact_report.py、soak_api.py、concurrency_api.py 和 recovery-test.ps1 分别覆盖制品、长稳、并发和本机恢复。

## 交付门槛

交给别人前必须通过静态验收和真实图片冒烟，记录模型/依赖版本与 SHA-256，并将 RAG、OCR、Docker、开发板分别标注验证状态。当前历史日志不能替代今天的板端在线验收；下次恢复连接后补板端权重和二进制哈希、当前服务日志、真实图片原始响应和资源采样。
