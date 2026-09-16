# 阶段五：Docker/Linux 部署路线

## 当前先做什么

本机目前没有 Docker 和 WSL2，因此先安装 Docker Desktop（开启 WSL2 后端）。安装完成后，在 PowerShell 验证：

```powershell
docker --version
docker compose version
wsl --status
```

## 本地 Docker Desktop 验证

当前 `docker-compose.local.yml` 让容器中的 FastAPI 通过 `host.docker.internal:8080` 访问仍运行在 Windows 主机上的 llama-server。因此不需要把 Windows 的 `llama-server.exe` 放进 Linux 容器。

```powershell
cd stage3_multimodal
docker compose -f docker-compose.local.yml up --build
```

验证：

```powershell
curl.exe http://127.0.0.1:9000/health
```

网页地址：`http://127.0.0.1:8502`。停止容器：

```powershell
docker compose -f docker-compose.local.yml down
```

## 重要边界

Windows 的 `llama-server.exe` 和 DLL 不能直接放进 Linux 容器。真正迁移到 Linux 云服务器时，需要准备 Linux 版 llama-server（或在服务器上编译 llama.cpp），并把 `LLAMA_BASE_URL` 改成容器服务名，例如 `http://llama-server:8080`。这属于阶段五后半段，不能用当前 Windows 可执行文件替代。

## 阶段五验收

1. Docker 能构建 API/UI 镜像。
2. 容器内 `/health` 返回 `service: ok` 且能连接主机 llama-server。
3. 容器网页可以完成 RAG、图片问答和 OCR。
4. 停止并重新创建容器后，`data` 和 `documents` 数据仍保留。
5. Linux 云服务器上使用 Linux llama-server 完成同样验证。
