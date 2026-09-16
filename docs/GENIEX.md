# GenieX 使用注意事项

## 组件边界

本项目实测的是 GenieX 的 llama_cpp 插件和 GGUF VLM 入口：

- GGUF 语言模型：Qwen3.5-4B-Q4_0.gguf
- 视觉组件：匹配的 mmproj-F16.gguf
- 模型 ID：unsloth/Qwen3.5-4B-GGUF-VLM:Q4_0
- HTTP：/v1/models、/v1/chat/completions

GenieX 的 QAIRT/QNN 路线是另一种构建和制品格式。本仓库不会因为设备是高通平台，
就把 GGUF + llama_cpp 误写成 QNN/DLC 部署。

## 输入格式

~~~json
{
  "model": "unsloth/Qwen3.5-4B-GGUF-VLM:Q4_0",
  "messages": [{
    "role": "user",
    "content": [
      {"type": "text", "text": "图中有什么？"},
      {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,<BASE64>"}}
    ]
  }],
  "max_tokens": 32,
  "stream": false
}
~~~

主模型和 mmproj 必须来自兼容版本，不能把 PC 的 0.8B mmproj 和板端 4B 权重混用。
流式和非流式属于不同的客户端行为，性能数据必须分别记录。

## 并发策略

历史板端日志包含 n_seq_max=1 和 HTP 缓冲区分配失败现象，因此默认策略是单请求串行队列。
只有完成并发阶梯测试并保存原始日志后，才能提高并发上限。并发请求不能与长时间 soak 同时进行。

## 量化口径

Q4_0 是权重存储格式，不等于所有算子都以 INT4 在 NPU 上计算；F16 mmproj 也不是 OCR 引擎。
量化收益必须用固定图片、输入长度、输出上限、冷/热启动条件和后端日志对照测量。
