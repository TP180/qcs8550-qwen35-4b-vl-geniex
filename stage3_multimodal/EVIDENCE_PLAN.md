# 稳定交付证据计划

本文件定义发布前需要补齐的四类证据。每次实验保留原始 JSONL、summary.json、设备版本和参数；公开仓库只提交脱敏报告，不提交开发板私钥或受限 SDK 二进制。

## 1. 制品完整性

主机侧：

~~~powershell
cd stage3_multimodal
.\.venv\Scripts\python.exe scripts\artifact_report.py --output .run\artifact-report.json
Get-FileHash ..\llama-server.exe -Algorithm SHA256
.\.venv\Scripts\python.exe -m pip freeze > .run\pip-freeze.txt
~~~

板端通过 board-ssh-kit 的 Check 模式建立连接后，只读采集：

~~~bash
uname -a
getprop 2>/dev/null | grep -Ei 'build|version' || true
/data/local/tmp/geniex/bin/geniex --version || true
sha256sum /data/local/tmp/geniex/models/unsloth/Qwen3.5-4B-GGUF/Qwen3.5-4B-Q4_0.gguf /data/local/tmp/geniex/models/unsloth/Qwen3.5-4B-GGUF-VLM/mmproj-F16.gguf /data/local/tmp/geniex/bin/geniex.real
~~~

同时保存 GenieX 版本、插件版本、动态库清单和启动参数。没有这些信息时只能声称“运行证据”，不能声称“制品完全可复现”。

## 2. 长时间 soak

先启动稳定的非流式图片接口，再串行执行：

~~~powershell
.\.venv\Scripts\python.exe scripts\soak_api.py --api-url http://127.0.0.1:9000 --image ..\demo\test_image.jpg --duration-seconds 14400 --output .run\soak-4h.jsonl
~~~

建议正式门槛为 8 小时或 24 小时；至少记录成功率、p50/p95/p99、最大延迟、首尾请求延迟，以及 MemAvailable、进程 RSS/PSS、温度、频率和降频事件。对比前 10% 与后 10% 的延迟和内存，判断热降频或泄漏。HTTP 脚本不代表 NPU 内部资源，设备采样必须独立完成。

## 3. 并发策略

当前历史日志显示 n_seq_max=1，默认策略为单请求串行队列。按阶梯执行：

~~~powershell
.\.venv\Scripts\python.exe scripts\concurrency_api.py --api-url http://127.0.0.1:9000 --image ..\demo\test_image.jpg --requests 8 --concurrency 1 --output .run\conc-1.jsonl
.\.venv\Scripts\python.exe scripts\concurrency_api.py --api-url http://127.0.0.1:9000 --image ..\demo\test_image.jpg --requests 8 --concurrency 2 --output .run\conc-2.jsonl
.\.venv\Scripts\python.exe scripts\concurrency_api.py --api-url http://127.0.0.1:9000 --image ..\demo\test_image.jpg --requests 8 --concurrency 4 --output .run\conc-4.jsonl
~~~

记录第一个出现错误率、延迟异常或 HTP 分配失败的级别，并把它作为产品上限。并发测试不要与 soak 同时运行。

## 4. 故障恢复

本机可执行：

~~~powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\recovery-test.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\recovery-test.ps1 -Run
~~~

Run 模式会停止交付脚本记录的本机服务，确认 /ready 失效，再重启并执行在线验收。板端恢复需要操作者明确授权：先保存日志、PID、端口和资源，再重启 GenieX，确认 /v1/models，连续执行至少 10 次真实图片请求，最后比较重启前后指标。

## 5. 最终报告

至少包含：日期、设备、固件/运行时版本、模型和 mmproj SHA-256、启动参数、图片 SHA-256、输入输出参数、成功率、p50/p95/p99、错误分类、内存/温度曲线、并发上限和恢复结果。没有原始日志的数字不得写入结论。