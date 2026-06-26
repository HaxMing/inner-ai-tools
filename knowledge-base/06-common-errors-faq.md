# 常见报错 FAQ

## 文档用途

本文收集内网 Docker、Dify、Ollama、Milvus、Rerank、FastAPI Tool 常见报错。适合回答：

```text
invalid schema 怎么处理？
Docker CLI was not found in PATH 怎么处理？
Dify 工具节点没有输出怎么办？
知识库没有召回怎么办？
```

## FAQ 1：Dify Tool 导入报 invalid schema

### 现象

在 Dify 自定义工具中使用：

```text
http://192.168.1.103:8000/openapi.json
```

报错：

```text
invalid schema, please check the url you provided
```

### 原因

FastAPI 默认生成的 OpenAPI 版本可能是：

```text
OpenAPI 3.1.0
```

某些 Dify 版本对 OpenAPI 3.1.0 支持不好，更适合使用 OpenAPI 3.0.x。

### 解决

本项目提供 Dify 专用 schema：

```text
http://192.168.1.103:8000/dify-openapi.json
```

在 Dify 的“从 URL 导入”中使用这个地址。

### 验证

```powershell
Invoke-RestMethod http://192.168.1.103:8000/dify-openapi.json
```

在 Linux 服务器上验证 Dify 能访问：

```bash
curl http://192.168.1.103:8000/dify-openapi.json
```

## FAQ 2：Docker CLI was not found in PATH

### 现象

工具返回：

```text
Docker CLI was not found in PATH.
```

### 原因

FastAPI 默认检查本机 Docker CLI。如果 FastAPI 跑在 Windows `192.168.1.103`，但 Docker 实际在 Linux `192.168.1.102`，就会检查错机器。

### 解决

使用 SSH 模式启动 FastAPI：

```powershell
$env:DOCKER_CHECK_MODE="ssh"
$env:DOCKER_SSH_HOST="192.168.1.102"
$env:DOCKER_SSH_USERNAME="root"
$env:DOCKER_SSH_PASSWORD="你的服务器密码"
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

不要把真实密码写入 Git 或知识库。

### 验证

```powershell
curl http://127.0.0.1:8000/health/docker
```

期望看到：

```text
ok: true
status: healthy
server_version: 29.4.1
```

## FAQ 3：Dify 工具节点只有 text，没有 json

### 现象

在 LLM 节点输入 `/` 选择变量时，工具节点只有：

```text
text
files
```

没有：

```text
json
```

### 原因

Dify 自定义工具会把 HTTP JSON 响应包装成 `text` 字符串输出。

### 解决

在 LLM 提示词中选择：

```text
CHECKDOCKERHEALTH / text
CHECKOLLAMAHEALTH / text
CHECKDIFYHEALTH / text
CHECKMILVUSHEALTH / text
```

不要选择 `files`。

## FAQ 4：Chatflow 里工具节点放了但没有生效

### 原因

工具节点只是放在画布上，不代表已经执行。必须接入主链路。

正确链路：

```text
START
-> KNOWLEDGE RETRIEVAL
-> CHECKDOCKERHEALTH
-> CHECKOLLAMAHEALTH
-> CHECKDIFYHEALTH
-> CHECKMILVUSHEALTH
-> LLM
-> ANSWER
```

LLM 提示词中也要插入工具节点的 `text` 输出变量。

## FAQ 5：/docs 是空白页面

### 原因

FastAPI 默认 `/docs` 使用外网 CDN 加载 Swagger UI 的 JS/CSS。如果浏览器访问不到 CDN，页面就会空白。

### 解决

当前项目已经改成本地自包含 `/docs`，不依赖外网。

访问：

```text
http://192.168.1.103:8000/docs
```

如果仍然空白，先强制刷新浏览器：

```text
Ctrl + F5
```

如果 uvicorn 没有启用 reload，需要重启服务。

## FAQ 6：知识库没有召回

### 可能原因

```text
1. 文档还在处理中。
2. Embedding 服务不可用。
3. Score 阈值太高。
4. 问题关键词和文档关键词差异太大。
5. 文档分段过长或过短。
```

### 调整建议

```text
Top K：先用 5
Score 阈值：先用 0.35
检索方式：混合检索
Rerank：启用
```

如果仍没有结果：

```text
Score 阈值降到 0.25
Top K 提到 8
给文档增加明确标题和常见问法
```

## FAQ 7：回答引用了无关文档

### 可能原因

```text
1. Top K 太大。
2. Score 阈值太低。
3. 多篇文档重复写了相似内容。
4. 文档标题不清晰。
```

### 调整建议

```text
Top K 降到 3-5
Score 阈值提高到 0.45
拆分重复内容
让每篇文档标题和段落标题更具体
```

## FAQ 8：Ollama 能 curl 通，但 Dify 里不可用

### 可能原因

```text
1. Dify 配置的 Base URL 不对。
2. 模型名不一致。
3. Dify 容器内部访问不到 Ollama。
4. Ollama 只监听 127.0.0.1。
```

### 验证

从 Dify 服务器执行：

```bash
curl http://192.168.1.106:11434/api/tags
curl http://192.168.1.101:11434/api/tags
```

如果服务器上能通，但 Dify 不通，继续看 Dify `api` 和 `worker` 日志。
