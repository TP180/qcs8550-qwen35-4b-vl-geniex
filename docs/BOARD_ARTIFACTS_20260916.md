# QCS8550 板端版本与制品记录

采集日期：2026-09-16
采集方式：通过仓库 board-ssh.ps1 执行只读 SSH 命令。

## 设备与系统

| 项目 | 已确认值 |
| --- | --- |
| SoC | Qualcomm QCS8550 |
| 平台代号 | kalama |
| 架构 | aarch64 |
| SoC revision | 2.0 |
| 系统 ID | qti-distro-rb-debug |
| 系统版本 | e9cc40a3ea |
| Kernel | 5.15.167-qki-consolidate |
| Kernel build | #1 SMP PREEMPT Fri Dec 5 11:11:40 UTC 2025 |

这里的系统版本是 QTI Linux 发行版构建标识，不等于基带、DSP 或各独立固件分区的完整版本清单。

## GenieX 与插件

| 项目 | 已确认值 |
| --- | --- |
| GenieX CLI | v0.3.14 |
| QAIRT Runtime | v2.45.0.260326 |
| llama_cpp Runtime Hash | be4a6a63e |
| bridge_version | v0.0.0 |
| qairt plugin | v2.45.0.260326 |
| llama_cpp plugin | be4a6a63e |

模型清单确认 VLM 使用 PluginId=llama_cpp、ModelType=vlm，语言权重为 Q4_0，视觉组件为 mmproj-F16.gguf。

## 核心制品

| 制品 | 大小 | SHA-256 |
| --- | ---: | --- |
| Qwen3.5-4B-Q4_0.gguf | 2,583,221,408 bytes | 298fcb5fe7a77ccc79745ae24751560c5ac56874caff4bb39b1f2055bd72b8bb |
| mmproj-F16.gguf | 672,423,616 bytes | cd88edcf8d031894960bb0c9c5b9b7e1fea6ebee02b9f7ce925a00d12891f864 |
| geniex.real | 未单独记录大小 | 6bd503b1e8468057d1240d98305209e6bce3a4e08fe80153a45b25e65536c41d |
| libgeniex.so | 未单独记录大小 | 8f599982cc8c05cb22c2c62996369d8087bdcd839acb73b5491b750f5584a95a |

VLM 目录中的 Qwen3.5-4B-Q4_0.gguf 已通过 readlink 确认指向语言模型目录中的同一份文件，因此不会把软链接误当成第二份权重。

## 证据边界

以上信息足以标识本次实验使用的核心模型和 GenieX 运行环境。尚未逐一记录所有 libllama、libmtmd、GGML/Hexagon 动态库的 SHA-256，也没有盘点基带、DSP 等所有固件分区；这属于更严格的供应链或量产审计范围，不影响当前求职项目的复现说明。