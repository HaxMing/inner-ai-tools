# inner-ai-tools

`inner-ai-tools` 是一个内网 AI 运维工具服务。它用 FastAPI 暴露只读健康检查接口，让 Dify Tool、Chatflow、Workflow 或 Agent 可以查询 Docker、Ollama、Dify、Milvus 的当前状态。

这个项目对应学习路线里的第 2、3、4、5、7 阶段：

- 第 2 阶段：FastAPI 后端服务和健康检查接口。
- 第 3 阶段：内网 Dify 运维 RAG 知识库。
- 第 4 阶段：Chatflow / Workflow 编排。
- 第 5 阶段：Dify Tool + Agent 只读工具调用。
- 第 7 阶段：README、接口文档、部署文档、测试报告、安全检查、AI Coding 使用记录。

本次第 7 阶段暂不包含 CI/CD 和 Docker Compose。

## 功能

| Method | Path | 作用 |
| --- | --- | --- |
| GET | `/` | 服务首页，列出文档和健康检查入口 |
| GET | `/docs` | 本地自包含 API 文档页面，不依赖外网 CDN |
| GET | `/openapi.json` | FastAPI 自动生成的 OpenAPI schema |
| GET | `/dify-openapi.json` | Dify Tool 推荐导入的 OpenAPI 3.0.3 schema |
| GET | `/health/docker` | 检查 Docker 是否可用，支持本机 CLI 或远程 SSH 模式 |
| GET | `/health/ollama` | 检查 Ollama 是否可访问，并返回模型数量和模型名 |
| GET | `/health/dify` | 检查 Dify Web 服务是否可访问 |
| GET | `/health/milvus` | 检查 Milvus TCP 端口是否可连接 |

这些接口只做读取和连通性探测，不会重启服务、删除容器、清理 volume 或修改配置。

## 技术栈

- Python 3.11+
- FastAPI
- Pydantic
- httpx
- paramiko
- pytest
- uv

## 快速启动

在 Windows PowerShell 中执行：

```powershell
cd F:\wtqcode\inner-ai-tools\inner-ai-tools
uv sync
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

浏览器访问：

```text
http://127.0.0.1:8000/docs
```

从 Dify 所在服务器访问时，使用 Windows 主机 IP：

```text
http://192.168.1.103:8000/docs
```

## Dify Tool 导入

Dify 自定义工具建议导入这个地址：

```text
http://192.168.1.103:8000/dify-openapi.json
```

不要优先导入 `/openapi.json`，因为 FastAPI 默认生成 OpenAPI 3.1.0，部分 Dify 版本会报 `invalid schema`。本项目的 `/dify-openapi.json` 已经手动整理成 OpenAPI 3.0.3。

导入后会得到 4 个只读工具：

```text
checkDockerHealth
checkOllamaHealth
checkDifyHealth
checkMilvusHealth
```

这 4 个工具都没有输入参数。Agent 调用时应传空 JSON 对象 `{}`。

## 配置

可以参考 `.env.example` 设置环境变量：

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `OLLAMA_BASE_URL` | `http://192.168.1.106:11434` | Ollama 服务地址 |
| `DIFY_BASE_URL` | `http://192.168.1.102` | Dify Web 服务地址 |
| `DIFY_HEALTH_PATH` | `/health` | Dify 健康检查路径，不存在时会回退到首页 |
| `MILVUS_HOST` | `192.168.1.102` | Milvus 主机 |
| `MILVUS_PORT` | `19530` | Milvus TCP 端口 |
| `HTTP_TIMEOUT_SECONDS` | `3` | HTTP 检查超时时间 |
| `DOCKER_TIMEOUT_SECONDS` | `5` | Docker 检查超时时间 |
| `SOCKET_TIMEOUT_SECONDS` | `3` | TCP 检查超时时间 |
| `DOCKER_CHECK_MODE` | `cli` | `cli` 检查本机 Docker，`ssh` 检查远程 Docker |
| `DOCKER_COMMAND` | `docker` | Docker CLI 命令 |
| `DOCKER_SSH_HOST` | `192.168.1.102` | 远程 Docker 服务器 |
| `DOCKER_SSH_PORT` | `22` | 远程 SSH 端口 |
| `DOCKER_SSH_USERNAME` | `root` | 远程 SSH 用户 |
| `DOCKER_SSH_PASSWORD` | 空 | 远程 SSH 密码，只能放本机环境变量，不要提交到 Git |
| `DOCKER_SSH_KEY_PATH` | 空 | 远程 SSH 私钥路径，和密码二选一 |
| `DOCKER_SSH_COMMAND` | `docker info --format '{{.ServerVersion}}'` | 远程执行的只读 Docker 检查命令 |

远程 SSH 检查 Docker 的 PowerShell 示例：

```powershell
$env:DOCKER_CHECK_MODE="ssh"
$env:DOCKER_SSH_HOST="192.168.1.102"
$env:DOCKER_SSH_USERNAME="root"
$env:DOCKER_SSH_PASSWORD=""
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

真实密码不要写进 `.env.example`、README、知识库或提交记录。

## 测试

```powershell
uv run pytest
```

当前测试覆盖：

- 首页元信息。
- 本地 `/docs` 页面不依赖 CDN。
- Dify 专用 OpenAPI schema 为 3.0.3。
- 4 个健康检查路由能正确调用 service 层函数。

## 文档

| 文档 | 说明 |
| --- | --- |
| `docs/api.md` | 接口文档和 Dify Tool 导入说明 |
| `docs/deploy.md` | 本地运行、内网访问、环境变量配置和排障 |
| `docs/test-report.md` | 当前测试范围、测试命令和测试结果 |
| `docs/security-review.md` | 只读权限、安全边界和风险检查 |
| `docs/ai-coding-log.md` | AI Coding 使用记录和人工校验记录 |
| `knowledge-base/README.md` | 第 3 阶段 RAG 知识库导入和调优说明 |

## 项目结构

```text
inner-ai-tools/
├── app/
│   ├── main.py           # FastAPI 路由入口
│   ├── config.py         # 环境变量读取和 Settings 配置对象
│   ├── schemas.py        # 健康检查返回 DTO
│   ├── docs.py           # 本地自包含 /docs 页面
│   ├── dify_schema.py    # Dify Tool 专用 OpenAPI 3.0.3 schema
│   └── services/
│       └── health.py     # Docker/Ollama/Dify/Milvus 检查逻辑
├── docs/                 # 第 7 阶段工程化文档
├── knowledge-base/       # 第 3 阶段 Dify RAG 知识库文档
├── tests/                # pytest 测试
├── .env.example          # 环境变量示例
├── pyproject.toml        # Python 项目和依赖配置
└── README.md
```

## 安全边界

本项目目前定位为“只读检查工具”。如果后续要增加重启、删除、清理、修改配置等写操作，必须单独设计权限控制、操作确认、审计日志和回滚策略，不要直接把高风险命令暴露给 Agent。
