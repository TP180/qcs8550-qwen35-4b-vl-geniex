# 阶段三：图片问答和 OCR

本目录是阶段二 `llama-server` 之上的业务层。流程为：浏览器上传图片 -> FastAPI 校验和转发 -> llama-server 的 `/v1/chat/completions` -> 返回答案；OCR 则在本机通过 Tesseract 执行，不把图片发送到外部服务。

## 启动

在已启动 Qwen3.5-0.8B-VL 的 llama-server（默认 `http://127.0.0.1:8080`）后执行：

```powershell
cd stage3_multimodal
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 9000
```

另开终端启动网页：

```powershell
streamlit run streamlit_app.py --server.port 8501
```

打开 `http://127.0.0.1:8501`。模型地址、模型名、超时和大小限制可通过 `LLAMA_BASE_URL`、`LLAMA_MODEL`、`LLAMA_TIMEOUT`、`MAX_IMAGE_MB`、`OCR_LANG` 配置。

## 接口

`GET /health` 检查业务服务和 llama-server；`POST /v1/image/qa` 使用 multipart 字段 `image`、`question`；`POST /v1/ocr` 使用 multipart 字段 `image`。自动生成的 Swagger 位于 `http://127.0.0.1:9000/docs`。

命令行验证示例：

```powershell
curl.exe http://127.0.0.1:9000/health
curl.exe -X POST http://127.0.0.1:9000/v1/image/qa `
  -F "question=图中有哪些物体？" -F "image=@path/to/demo.jpg"
curl.exe -X POST http://127.0.0.1:9000/v1/ocr `
  -F "image=@path/to/document.png"
```

## 工作拆解

阶段三可按以下顺序实施：

1. **图片接入**：前端限制扩展名，后端同时检查 MIME、文件大小和 Pillow 解码结果，防止只改扩展名的无效文件进入模型。
2. **视觉问答**：将图片编码为 data URL，和问题一起放入 OpenAI 风格的 multimodal message；低温度保证回答稳定，超时和上游错误映射为 502。
3. **OCR**：先使用 Tesseract 完成离线中英文识别；通过 `OCR_LANG` 切换语言包。生产环境可将 `extract_text` 替换为 PaddleOCR 适配器，接口无需改变。
4. **交互和状态**：Streamlit 展示原图、问答历史和 OCR 文本；服务端不持久化图片，适合先做本地隐私闭环。
5. **验收和观测**：用 `/health`、Swagger 和三条 curl 命令验证链路，再补充耗时、图片尺寸和上游状态码日志。

### 常见问题

- **返回 502**：确认 llama-server 监听地址和端口，并检查其启动参数已加载视觉 projector；可设置 `LLAMA_BASE_URL` 指向实际地址。
- **返回 503（OCR）**：安装 Tesseract 主程序及对应 `chi_sim` 语言包，再安装 `pytesseract`。Windows 下如未加入 PATH，应设置 `pytesseract.pytesseract.tesseract_cmd`。
- **模型不识别图片**：确认 llama-server 版本支持 OpenAI multimodal 格式，并使用与 Qwen3.5-VL 匹配的 mmproj 文件。

## 阶段三验收

1. `/health` 返回 `service: ok` 且 `llama_server: true`。
2. 上传 JPG/PNG/WEBP 后，图片问答能返回模型文本；超过大小或伪造扩展名会得到 413/400。
3. OCR 能返回中英文文字；未安装 Tesseract 时明确返回 503，不影响图片问答。
4. llama-server 停止时图片问答返回 502，网页显示可读错误而不是堆栈。
