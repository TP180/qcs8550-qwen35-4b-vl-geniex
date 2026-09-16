# QCS8550 / GenieX Qwen3.5-4B-VL 实验验收记录

记录日期：2026-09-15

## 第 6 步：多模态 HTTP 接口

已使用真实图片 test.jpg，通过 POST /v1/chat/completions 调用模型 unsloth/Qwen3.5-4B-GGUF-VLM:Q4_0。

结果：

- 图片识别成功，返回聊天截图中的文字和内容。
- HTTP 请求正常结束，finish_reason=stop。
- prompt_tokens=34。
- completion_tokens=27。

这证明的是：当前模型入口、mmproj、图片字段和 GenieX 多模态 HTTP 链路可以完成一次真实图片推理。

## 第 7 步：NPU 长时间稳定性

测试窗口：09:09:37 至 09:39:37。

| 指标 | 结果 |
|---|---:|
| 图片 HTTP 请求数 | 38 |
| 成功数 | 38 |
| 失败数 | 0 |
| 成功率 | 100% |
| 平均响应时间 | 17.78 秒 |
| 最短响应时间 | 17.17 秒 |
| 最长响应时间 | 22.36 秒 |
| P95 响应时间 | 18.10 秒 |
| 每次输出上限 | 32 token |

资源监控：

- MemAvailable 约 12.96–13.89 GiB。
- MemFree 约 5.02–5.05 GiB。
- 未观察到内存持续下降，暂未发现明显内存泄漏。
- 可读温度传感器范围约 32.2–81.0°C。
- thermal_zone0–40 读数约 32.2–55.5°C。
- thermal_zone101 类型为 battery，约 81.0°C，不能直接作为 NPU 温度。
- 返回 Invalid argument 的 thermal zone 已排除，不参与有效温度统计。

## 证据边界

本次结果可以支持：

1. 真实图片多模态 HTTP 推理已完成。
2. 在 30 分钟、38 次、串行请求条件下成功率为 100%。
3. 该测试窗口内没有明显内存泄漏迹象。
4. 响应时间基线约为 17.78 秒，P95 约为 18.10 秒。

本次结果不能单独支持：

1. 并发请求能力。历史日志显示当前部署更适合单请求串行。
2. NPU 的精确温度。battery 传感器需要硬件标定和散热确认。
3. 长时间持续运行超过本测试窗口时仍无热降频。
4. 尚未逐一核验全部 llama.cpp、mtmd、GGML/Hexagon 动态库；核心模型、mmproj、geniex.real 和 libgeniex.so 已于 2026-09-16 完成 SHA-256 登记。
5. 当前 SSH 在线状态只能代表采集时刻；已于 2026-09-16 复查为 kalama / root / aarch64。

对应原始记录：npu-stability-20260915.log；流式实验记录：vlm-streaming-warm-20260915.log；板端运行说明：board-connection/Qwen35-4B-GenieX-部署复盘与面试指南.md。
## 2026-09-16 板端版本与制品补录

已通过只读 SSH 重新连接开发板并核验：

- GenieX CLI：v0.3.14。
- QAIRT Runtime：v2.45.0.260326。
- llama_cpp 插件/运行时提交：be4a6a63e。
- QTI Linux 系统版本：e9cc40a3ea。
- Kernel：5.15.167-qki-consolidate。
- Qwen3.5-4B Q4_0、mmproj-F16、geniex.real、libgeniex.so 均已登记 SHA-256。
- VLM 目录中的主模型软链接已确认指向已哈希的语言模型文件。

详细路径、大小和哈希见 docs/BOARD_ARTIFACTS_20260916.md 和 MODEL_MANIFEST.json。