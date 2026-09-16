# 基于 QCS8550 和 GenieX 的 Qwen3.5-4B-VL 端侧多模态推理部署

本仓库记录在 Qualcomm QCS8550 开发板上，使用 GenieX 的 llama_cpp 插件加载
Qwen3.5-4B-VL（语言模型 Q4_0、视觉投影组件 F16），通过 HTTP 完成图片加文本推理。
同时提供 PC 主机侧 FastAPI/Streamlit 验证应用、制品登记、性能测试和故障恢复脚本。

> 本仓库不重新分发模型权重、Qualcomm 专有 SDK、驱动或固件。它们必须从官方或授权来源获取并遵守各自许可证。

## 当前验证状态

| 项目 | 状态 |
| --- | --- |
| QCS8550 + GenieX 真实图片 HTTP 推理 | 已验证 |
| 30 分钟串行稳定性 | 38/38，100%，平均 17.78 s，P95 18.10 s |
| PC API/UI/RAG 单元测试 | 已验证，8 tests passed |
| 4 小时以上 soak、并发上限、板端重启恢复 | 待在目标环境执行 |
| GenieX、QTI Linux build、核心板端制品 SHA-256 | 已于 2026-09-16 核验 |

证据边界见 EXPERIMENT_REPORT_20260915.md 和 stage3_multimodal/EVIDENCE_PLAN.md。

## 目录结构

~~~text
.
├── README.md
├── LICENSE
├── requirements.txt
├── config.yaml
├── run.sh
├── demo/test_image.jpg
├── scripts/
│   ├── convert_model.py
│   ├── quantize.py
│   ├── benchmark.py
│   └── run_infer.sh
├── docs/
│   ├── BOARD_BUILD.md
│   ├── GENIEX.md
│   └── TROUBLESHOOTING.md
├── stage3_multimodal/
├── MODEL_MANIFEST.json
└── EXPERIMENT_REPORT_20260915.md
~~~

## 硬件和软件要求

QCS8550 最小配置：ARM64/aarch64、QTI Linux、建议至少 16 GiB 系统内存、
至少 8 GiB 可用存储、稳定供电和主动散热，以及可访问板端的 SSH/ADB 通道。
本次实验板端可见内存约 22 GiB。

板端已核验 GenieX CLI v0.3.14、QAIRT Runtime v2.45.0.260326、llama_cpp 提交
be4a6a63e，以及 QTI Linux build e9cc40a3ea。详细证据见 docs/BOARD_ARTIFACTS_20260916.md。PC 快照为 Python 3.13.2、FastAPI 0.141.1、
Uvicorn 0.52.4、Streamlit 1.63.0，完整版本在 stage3_multimodal/constraints.txt。

## 快速开始：PC API/UI

~~~bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt -c stage3_multimodal/constraints.txt
python stage3_multimodal/scripts/build_index.py
export LLAMA_BASE_URL=http://127.0.0.1:8080
export LLAMA_MODEL=Qwen3.5-0.8B-Q4_K_M.gguf
./run.sh
~~~

浏览器访问 http://127.0.0.1:8501，API 文档访问 http://127.0.0.1:9000/docs。
Windows 用户可用 stage3_multimodal/scripts/start-windows.ps1。

## 模型获取

模型权重不提交到 Git。按发布者页面固定 revision 后下载：

~~~bash
python -m pip install -U huggingface_hub
hf download unsloth/Qwen3.5-4B-GGUF-VLM \
  --include '*Q4_0*' 'mmproj*' \
  --local-dir models/qwen35-4b-vl
~~~

将实际文件复制到板端模型目录，确认语言模型和 mmproj 来自同一版本。下载后记录：

~~~bash
sha256sum models/qwen35-4b-vl/Qwen3.5-4B-Q4_0.gguf
sha256sum models/qwen35-4b-vl/mmproj-F16.gguf
~~~

如果发布者的文件名或仓库布局不同，以该版本页面为准，不要仅靠重命名伪造制品来源。

## 转换和量化

GenieX SDK 不同版本的转换/量化 CLI 不兼容，仓库脚本只做输入检查并调用用户明确提供的 SDK 命令：

~~~bash
python scripts/convert_model.py --input path/to/source --output build/converted --dry-run
python scripts/quantize.py --input build/converted/model.gguf \
  --output build/Qwen3.5-4B-Q4_0.gguf --type Q4_0 --dry-run
~~~

执行时通过 --command 传入 SDK 文档中的实际命令，并保存 SDK 版本、完整命令和输出 SHA-256。
不要根据文件后缀推断已经使用了 NPU 或 QNN。

## QCS8550 板端运行

板端 GenieX 服务由 SDK 的 geniex 包装脚本启动；启动参数和运行库必须使用同一 SDK 发行版。
服务就绪后：

~~~bash
GENIEX_URL=http://127.0.0.1:18181 \
GENIEX_MODEL_ID='unsloth/Qwen3.5-4B-GGUF-VLM:Q4_0' \
./scripts/run_infer.sh demo/test_image.jpg '图中有什么？'
~~~

脚本只调用已验证的 GET /v1/models 和 POST /v1/chat/completions。

## HTTP API 示例

业务层 API：

~~~bash
curl http://127.0.0.1:9000/ready
curl -X POST http://127.0.0.1:9000/v1/image/qa \
  -F 'question=请描述图片中的主要内容' \
  -F 'image=@demo/test_image.jpg'
~~~

GenieX/OpenAI 兼容接口：

~~~bash
curl http://127.0.0.1:18181/v1/models
curl -X POST http://127.0.0.1:18181/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"unsloth/Qwen3.5-4B-GGUF-VLM:Q4_0","messages":[{"role":"user","content":[{"type":"text","text":"图中有什么？"},{"type":"image_url","image_url":{"url":"data:image/jpeg;base64,<BASE64>"}}]}],"max_tokens":32,"stream":false}'
~~~

## 性能结果

已完成的真实板端基线：

| 条件 | 请求 | 成功率 | 平均 | P95 | 输出上限 |
| --- | ---: | ---: | ---: | ---: | ---: |
| QCS8550 + GenieX，真实图片，串行，30 min | 38 | 100% | 17.78 s | 18.10 s | 32 token |

历史流式热请求 TTFT 约 11.35 s、总耗时约 18.85 s；不能替代非流式验收，也不能推出并发能力。

~~~bash
python scripts/benchmark.py --api-url http://127.0.0.1:9000 \
  --image demo/test_image.jpg --requests 10
python stage3_multimodal/scripts/concurrency_api.py \
  --api-url http://127.0.0.1:9000 --image demo/test_image.jpg \
  --requests 8 --concurrency 1
~~~

## 常见问题、复现和发布检查

重点排查模型与 mmproj 不匹配、HTP 缓冲区分配失败、/ready 503、图片 MIME/大小、
ABI/动态库、OCR 依赖和并发超过 n_seq_max=1。详见 docs/TROUBLESHOOTING.md。

~~~bash
python -m unittest discover -s stage3_multimodal/tests -v
python stage3_multimodal/scripts/artifact_report.py
~~~

板端核心版本和 SHA-256 已登记；正式稳定性交付仍需按
stage3_multimodal/EVIDENCE_PLAN.md 执行 soak、并发阶梯和恢复演练。模型、二进制、
日志、私钥和生成索引已由 .gitignore 排除。

## 参考链接和许可证

- Qwen 模型页：https://huggingface.co/Qwen
- Qualcomm GenieX：https://github.com/qualcomm/GenieX
- llama.cpp mtmd：https://github.com/ggml-org/llama.cpp/tree/master/tools/mtmd
- GGUF/ggml：https://github.com/ggml-org/ggml

源码采用 MIT。模型、GenieX SDK、驱动、固件和第三方运行库遵循各自许可证。
