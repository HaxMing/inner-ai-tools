# inner-ai-tools

一个练习用的内网 AI 工具服务：用 FastAPI 暴露只读健康检查接口，后续可以被 Dify Tool 通过 OpenAPI 导入调用。

## 接口

| Method | Path | 作用 |
| --- | --- | --- |
| GET | `/health/docker` | 检查 Docker 是否可用，支持本机 CLI 或远程 SSH 模式 |
| GET | `/health/ollama` | 检查 Ollama 服务是否可访问，并返回模型数量 |
| GET | `/health/dify` | 检查 Dify 服务是否可访问 |
| GET | `/health/milvus` | 检查 Milvus 端口是否可连接 |

这些接口只做读取和连通性探测，不会重启服务、删除容器、清理 volume 或修改配置。

## 启动

```powershell
uv sync
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

本机测试：

```powershell
curl http://127.0.0.1:8000/health/docker
curl http://127.0.0.1:8000/health/ollama
curl http://127.0.0.1:8000/health/dify
curl http://127.0.0.1:8000/health/milvus
```

如果 Dify 部署在 `192.168.1.102`，可以在 Dify Tool 中导入：

```text
http://192.168.1.103:8000/openapi.json
```

## 配置

可以参考 `.env.example` 设置环境变量：

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `OLLAMA_BASE_URL` | `http://192.168.1.106:11434` | Ollama 服务地址 |
| `DIFY_BASE_URL` | `http://192.168.1.102` | Dify 服务地址 |
| `DIFY_HEALTH_PATH` | `/health` | Dify 健康检查路径 |
| `MILVUS_HOST` | `192.168.1.102` | Milvus 主机 |
| `MILVUS_PORT` | `19530` | Milvus 端口 |
| `HTTP_TIMEOUT_SECONDS` | `3` | HTTP 检查超时时间 |
| `DOCKER_TIMEOUT_SECONDS` | `5` | Docker 命令超时时间 |
| `SOCKET_TIMEOUT_SECONDS` | `3` | TCP 检查超时时间 |
| `DOCKER_CHECK_MODE` | `cli` | `cli` 检查本机 Docker，`ssh` 检查远程 Docker |
| `DOCKER_COMMAND` | `docker` | Docker CLI 命令 |
| `DOCKER_SSH_HOST` | `192.168.1.102` | 远程 Docker 服务器 |
| `DOCKER_SSH_PORT` | `22` | 远程 SSH 端口 |
| `DOCKER_SSH_USERNAME` | `root` | 远程 SSH 用户 |
| `DOCKER_SSH_PASSWORD` | 空 | 远程 SSH 密码，建议只放在本机环境变量里 |
| `DOCKER_SSH_KEY_PATH` | 空 | 远程 SSH 私钥路径，和密码二选一 |
| `DOCKER_SSH_COMMAND` | `docker info --format '{{.ServerVersion}}'` | 远程执行的只读 Docker 检查命令 |

PowerShell 示例：

```powershell
$env:OLLAMA_BASE_URL="http://192.168.1.106:11434"
$env:DIFY_BASE_URL="http://192.168.1.102"
$env:MILVUS_HOST="192.168.1.102"
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

如果要检查 `192.168.1.102` 上的 Docker，可以用 SSH 模式。不要把真实密码提交到 Git：

```powershell
$env:DOCKER_CHECK_MODE="ssh"
$env:DOCKER_SSH_HOST="192.168.1.102"
$env:DOCKER_SSH_USERNAME="root"
$env:DOCKER_SSH_PASSWORD="你的服务器密码"
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 测试

```powershell
uv run pytest
```

## 给 Dify Tool 使用时的建议

1. FastAPI 服务启动时使用 `--host 0.0.0.0`，这样 Dify 所在机器才能访问你的 Windows 主机。
2. 在 Windows 防火墙中放行 `8000` 端口。
3. Dify Tool 导入地址使用 `http://192.168.1.103:8000/openapi.json`。
4. Agent 先只允许调用这些只读接口，等你熟悉权限控制后再考虑写操作。
