# 部署文档

本文档说明如何在 Windows 开发机上运行 `inner-ai-tools`，并让 Dify 能访问它。

## 部署目标

当前推荐部署方式：

```text
Windows 开发机 192.168.1.103
└── FastAPI inner-ai-tools: http://192.168.1.103:8000

远程服务器 192.168.1.102
├── Dify Web
├── Docker
└── Milvus: 19530

MacBook M1 192.168.1.106
└── Ollama: 11434
```

本阶段不提供 Docker Compose 部署方案，也不新增 CI/CD 配置。

## 前置条件

- Windows 已安装 Python 3.11+。
- Windows 已安装 `uv`。
- 当前机器能访问：
  - `http://192.168.1.102`
  - `http://192.168.1.106:11434`
  - `192.168.1.102:19530`
- 如果使用 `DOCKER_CHECK_MODE=ssh`，当前机器能 SSH 到 `192.168.1.102:22`。
- Windows 防火墙放行 TCP `8000`，否则 Dify 服务器访问不到本机 FastAPI。

## 安装依赖

在 PowerShell 中执行：

```powershell
cd F:\wtqcode\inner-ai-tools\inner-ai-tools
uv sync
```

## 配置环境变量

最小配置可以直接使用项目默认值。

如果要显式配置：

```powershell
$env:OLLAMA_BASE_URL="http://192.168.1.106:11434"
$env:DIFY_BASE_URL="http://192.168.1.102"
$env:DIFY_HEALTH_PATH="/health"
$env:MILVUS_HOST="192.168.1.102"
$env:MILVUS_PORT="19530"
```

如果 Windows 本机没有 Docker CLI，建议使用 SSH 模式检查远程 Docker：

```powershell
$env:DOCKER_CHECK_MODE="ssh"
$env:DOCKER_SSH_HOST="192.168.1.102"
$env:DOCKER_SSH_PORT="22"
$env:DOCKER_SSH_USERNAME="root"
$env:DOCKER_SSH_PASSWORD="你的服务器密码"
```

注意：真实密码只放在本机当前会话或本机 `.env` 中，不要提交到 Git，也不要写进知识库。

## 启动服务

开发模式启动：

```powershell
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

为什么要用 `--host 0.0.0.0`：

- `127.0.0.1` 只能本机访问。
- Dify 在 `192.168.1.102` 上，需要通过 `192.168.1.103:8000` 访问这个服务。

## 本机验证

```powershell
Invoke-RestMethod http://127.0.0.1:8000/
Invoke-RestMethod http://127.0.0.1:8000/health/docker
Invoke-RestMethod http://127.0.0.1:8000/health/ollama
Invoke-RestMethod http://127.0.0.1:8000/health/dify
Invoke-RestMethod http://127.0.0.1:8000/health/milvus
```

浏览器打开：

```text
http://127.0.0.1:8000/docs
```

## 从 Dify 服务器验证

在 `192.168.1.102` 服务器上执行：

```bash
curl http://192.168.1.103:8000/
curl http://192.168.1.103:8000/dify-openapi.json
```

如果这里访问失败，优先检查：

1. FastAPI 是否使用了 `--host 0.0.0.0`。
2. Windows 防火墙是否放行 `8000`。
3. `192.168.1.102` 和 `192.168.1.103` 是否在同一内网可互通。

## Dify Tool 导入

在 Dify 自定义工具中从 URL 导入：

```text
http://192.168.1.103:8000/dify-openapi.json
```

鉴权方法选择“无”。

导入成功后，工具列表应包含：

```text
checkDockerHealth
checkOllamaHealth
checkDifyHealth
checkMilvusHealth
```

## 常见问题

### /docs 打开空白

当前项目已经覆盖 FastAPI 默认 Swagger UI，`/docs` 是本地自包含页面。如果仍然空白：

1. 打开浏览器开发者工具查看是否请求 `/openapi.json` 失败。
2. 确认服务没有被浏览器代理拦截。
3. 直接访问 `http://127.0.0.1:8000/openapi.json` 验证 schema 是否返回。

### Dify Tool 导入 invalid schema

优先使用：

```text
http://192.168.1.103:8000/dify-openapi.json
```

不要优先使用：

```text
http://192.168.1.103:8000/openapi.json
```

原因是 `/openapi.json` 由 FastAPI 自动生成，可能是 OpenAPI 3.1.0；`/dify-openapi.json` 是项目手动维护的 OpenAPI 3.0.3，更适合 Dify 自定义工具导入。

### Docker 返回 Docker CLI was not found in PATH

如果 FastAPI 跑在 Windows 上，而 Docker 在远程 Linux 服务器上，这是正常方向上的配置问题。

解决方式：切换到 SSH 检查模式：

```powershell
$env:DOCKER_CHECK_MODE="ssh"
$env:DOCKER_SSH_HOST="192.168.1.102"
$env:DOCKER_SSH_USERNAME="root"
$env:DOCKER_SSH_PASSWORD="你的服务器密码"
```

然后重启 uvicorn。

### Ollama 或 Dify 在浏览器能访问，接口却 unhealthy

优先检查：

1. 环境变量中的地址是否写错。
2. FastAPI 所在机器是否能访问目标 IP 和端口。
3. 是否配置了系统代理。项目里的 HTTP 请求已经设置 `trust_env=False`，正常不会走系统代理。
4. 超时时间是否太短，可以临时调大 `HTTP_TIMEOUT_SECONDS`。

## 停止服务

开发模式下，在运行 uvicorn 的 PowerShell 窗口按：

```text
Ctrl + C
```

这只会停止 FastAPI 开发服务，不会影响 Dify、Ollama、Docker、Milvus。
