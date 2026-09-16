# 常见错误排查

## HTTP 层

| 现象 | 排查 |
| --- | --- |
| /ready 返回 503 | 访问模型后端 /health 或 /v1/models，确认端口、进程和模型加载日志。 |
| 图片返回 415/400/413 | 检查 MIME、文件内容、损坏情况和 MAX_IMAGE_MB。扩展名不能代替真实格式。 |
| 图片返回 502 | 检查 GenieX 地址、模型 ID、mmproj 和超时；保存上游响应正文。 |
| 请求卡住 | 区分冷启动、图像编码、prefill、decode 和网络时间；不要只看总耗时。 |

## 模型和运行时

- mmproj load failed：确认主模型与 mmproj 来自同一模型版本，文件完整且架构匹配。
- HTP0-REPACK allocation failed：先停止并发和流式切换，恢复单请求串行，检查设备缓冲区和重复实例。
- symbol not found 或 GLIBCXX：检查 aarch64 ABI、动态库搜索路径、插件和 GenieX 版本是否混用。
- 能启动但无法识图：确认使用 VLM model ID、真实 image_url 字段和支持多模态的后端。
- 内存不足：先减少并发、上下文、图片分辨率和输出长度，再检查是否重复加载模型。
- 只有目录里存在 Hexagon/QNN 库：这不能证明本次请求实际走了该后端，以启动和算子日志为准。

## OCR 和 RAG

- OCR 503：安装系统 Tesseract 和对应语言包，再安装 pytesseract；OCR 不影响 VLM 图片问答。
- RAG 503：先将文档放入 stage3_multimodal/documents/，再运行 build_index.py。
- 索引重建后：保留向量器、分块参数和文档版本，避免用不同配置直接比较结果。

## 板端恢复

1. 保存服务日志、PID、端口、内存和温度采样。
2. 停止或重启 GenieX，等待模型加载完成。
3. 验证 /v1/models，再连续执行至少 10 次真实图片请求。
4. 记录恢复前后成功率、p50/p95/p99、内存和温度。
5. 未恢复时保留现场，不删除日志；将错误标记为未通过。
