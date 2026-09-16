# QCS8550 板端部署与交叉编译

## 1. 采集版本

在板端执行并保存脱敏输出：

~~~bash
uname -a
getprop 2>/dev/null | grep -Ei 'build|version' || true
/data/local/tmp/geniex/bin/geniex --version || true
sha256sum /data/local/tmp/geniex/bin/geniex.real
~~~

如果命令不存在，以板端 SDK 的实际路径为准。发布报告必须记录 GenieX 版本、插件版本、
动态库列表和启动参数；不能用 PC 上的 llama-server.exe 代替板端运行时。

## 2. 目录和制品

本次实验使用的逻辑目录：

~~~text
/data/local/tmp/geniex/
├── bin/geniex
├── libs/
├── runtime/
├── models/unsloth/Qwen3.5-4B-GGUF/
│   └── Qwen3.5-4B-Q4_0.gguf
└── models/unsloth/Qwen3.5-4B-GGUF-VLM/
    ├── Qwen3.5-4B-Q4_0.gguf
    └── mmproj-F16.gguf
~~~

实际路径以板端部署包为准。语言模型和 mmproj 必须来自兼容版本。部署后保存文件大小和
SHA-256，但不要把板端私钥、完整连接配置或受限制 SDK 二进制提交到公开仓库。

## 3. 交叉编译注意事项

- 在 SDK 提供的 aarch64 sysroot/toolchain 中编译；不要用 Windows exe 或主机 x86_64 库。
- 编译器、glibc/libstdc++、运行时插件和 GenieX 包必须来自兼容 SDK 版本。
- LD_LIBRARY_PATH 只指向本次服务需要的 SDK libs/ 和 runtime/，不要覆盖系统目录。
- 固定 git commit、编译器版本、CMake 参数和目标 ABI；输出二进制后计算 SHA-256。
- 只有看到模型加载日志、设备选择日志和真实图片请求，才能宣称对应后端参与推理。

## 4. 启动和 HTTP 验证

GenieX 的启动子命令随 SDK 版本变化，必须以板端自带 geniex --help 和 SDK 文档为准。
不要把下面示例当作未经核对的固定 CLI：

~~~bash
# 仅示意：用目标 SDK 文档中的实际 start_server.sh 替换
./scripts/start_server.sh
~~~

验证已经确认的兼容接口：

~~~bash
curl http://127.0.0.1:18181/v1/models
./scripts/run_infer.sh demo/test_image.jpg '请读取图片中的文字'
~~~

## 5. 资源和稳定性

串行请求是当前安全默认值。先执行 stage3_multimodal/scripts/soak_api.py，
再以并发 1、2、4 阶梯测试。独立采样 MemAvailable、进程 RSS/PSS、温度、频率和错误日志。
battery thermal zone 不能直接代表 NPU 温度。
