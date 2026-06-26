# 接口文档

本文档说明 `inner-ai-tools` 当前暴露的 HTTP 接口，以及如何把接口导入 Dify Tool。

## 基础地址

本地调试：

```text
http://127.0.0.1:8000
```

Dify 所在服务器访问 Windows 主机：

```text
http://192.168.1.103:8000
```

## 元信息接口

### GET /

作用：返回服务名称、文档地址和健康检查接口列表。

示例：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/
```

返回字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `name` | string | 服务名称 |
| `docs` | string | 本地文档页面地址 |
| `openapi` | string | FastAPI 自动生成 schema 地址 |
| `dify_openapi` | string | Dify Tool 推荐导入 schema 地址 |
| `health_endpoints` | array | 健康检查接口列表 |

### GET /docs

作用：返回本地自包含 API 文档页面。

这个页面由 `app/docs.py` 生成，不依赖外网 CDN。之前默认 Swagger UI 空白的问题，通常就是浏览器无法加载 CDN 里的 JS/CSS。

### GET /dify-openapi.json

作用：返回 Dify Tool 推荐导入的 OpenAPI 3.0.3 schema。

调用链：

1. Dify 请求 `/dify-openapi.json`。
2. `app/main.py` 中的 `dify_openapi()` 接收请求。
3. `dify_openapi()` 调用 `app/dify_schema.py` 中的 `get_dify_openapi_schema()`。
4. FastAPI 把 Python dict 序列化为 JSON 返回给 Dify。

## 健康检查返回结构

4 个健康检查接口统一返回 `HealthCheckResult`。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `service` | string | 被检查的服务名，例如 `docker`、`ollama` |
| `ok` | boolean | 程序判断用，`true` 表示检查通过 |
| `status` | string | 人类阅读用，只会是 `healthy` 或 `unhealthy` |
| `checked_at` | string | UTC 检查时间 |
| `response_time_ms` | number | 检查耗时，单位毫秒 |
| `details` | object | 各服务自己的诊断细节 |

健康示例：

```json
{
  "service": "ollama",
  "ok": true,
  "status": "healthy",
  "checked_at": "2026-06-26T08:32:02Z",
  "response_time_ms": 312.38,
  "details": {
    "url": "http://192.168.1.106:11434/api/tags",
    "status_code": 200,
    "model_count": 1,
    "models": ["qwen3.6:27b"]
  }
}
```

异常示例：

```json
{
  "service": "docker",
  "ok": false,
  "status": "unhealthy",
  "checked_at": "2026-06-26T08:32:02Z",
  "response_time_ms": 10.25,
  "details": {
    "check_mode": "cli",
    "command": "docker info --format {{.ServerVersion}}",
    "error": "Docker CLI was not found in PATH."
  }
}
```

## 健康检查接口

### GET /health/docker

作用：检查 Docker 是否可访问。

内部调用：

1. `app/main.py` 的 `docker_health()` 接收请求。
2. FastAPI 通过 `Depends(get_settings)` 读取配置。
3. `docker_health()` 调用 `app/services/health.py` 的 `check_docker(settings)`。
4. `check_docker()` 根据 `DOCKER_CHECK_MODE` 分支：
   - `cli`：检查运行 FastAPI 的机器上是否有 Docker CLI。
   - `ssh`：通过 SSH 登录远程服务器执行只读 Docker 命令。
5. 返回 `HealthCheckResult`。

常见 `details` 字段：

| 字段 | 说明 |
| --- | --- |
| `check_mode` | `cli` 或 `ssh` |
| `server_version` | Docker Server 版本 |
| `error` | 异常原因 |
| `stderr` | Docker 命令错误输出 |

### GET /health/ollama

作用：检查 Ollama API 是否可访问，并列出模型数量和模型名。

内部请求：

```text
{OLLAMA_BASE_URL}/api/tags
```

默认地址：

```text
http://192.168.1.106:11434/api/tags
```

常见 `details` 字段：

| 字段 | 说明 |
| --- | --- |
| `url` | 实际请求地址 |
| `status_code` | HTTP 状态码 |
| `model_count` | 模型数量 |
| `models` | 最多返回前 20 个模型名 |
| `error` | 请求失败原因 |

### GET /health/dify

作用：检查 Dify Web 入口是否可访问。

默认策略：

1. 先请求 `DIFY_BASE_URL + DIFY_HEALTH_PATH`，默认是 `http://192.168.1.102/health`。
2. 如果返回 404，再回退请求 `DIFY_BASE_URL`。
3. 如果最终 HTTP 响应成功，就认为 Dify Web 基本可访问。

这个接口只检查 Web 入口，不完整检查 Dify worker、PostgreSQL、Redis、对象存储等内部组件。

### GET /health/milvus

作用：检查 Milvus TCP 端口是否可连接。

默认目标：

```text
192.168.1.102:19530
```

这个接口只做 TCP 连接测试，不使用 Milvus SDK，不读取 collection，也不写入向量数据。

## Dify Tool 导入步骤

1. 确认 FastAPI 服务启动：

```powershell
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

2. 在浏览器确认 schema 可访问：

```text
http://192.168.1.103:8000/dify-openapi.json
```

3. 在 Dify 进入“工具”或“自定义工具”页面。
4. 选择“从 URL 导入”。
5. 输入：

```text
http://192.168.1.103:8000/dify-openapi.json
```

6. 鉴权方式选择“无”。
7. 导入成功后应看到：

```text
checkDockerHealth
checkOllamaHealth
checkDifyHealth
checkMilvusHealth
```

## Agent 调用注意事项

4 个工具都没有输入参数。Agent 提示词中要明确：

```text
checkDockerHealth、checkOllamaHealth、checkDifyHealth、checkMilvusHealth 都没有输入参数。
调用这些工具时，工具参数必须是空 JSON 对象 {}，不要传字符串、null 或用户问题文本。
```

否则 Dify Agent 可能会报：

```text
tool_parameters should be a dict, but got a string
```
