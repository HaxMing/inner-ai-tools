# Dify 部署笔记

## 文档用途

本文记录内网 Dify 的部署位置、访问方式、常用检查命令和排障顺序。适合回答：

```text
Dify 页面打不开怎么办？
Dify 容器是否正常怎么查？
Dify 部署目录在哪里？
Dify 更新或重启前要注意什么？
```

## 当前环境

```text
Dify 服务器：192.168.1.102
Dify 访问地址：http://192.168.1.102
常见访问结果：http://192.168.1.102/apps
部署方式：Docker / Docker Compose
示例部署目录：/wtq/dify/dify-1.14.2/docker
```

注意：部署目录以实际服务器为准。如果目录不同，先用 `find` 或历史部署记录确认。

## Dify 在系统中的角色

Dify 是当前内网 AI 应用编排平台，负责：

```text
1. 管理应用，例如 Chatbot、Agent、Chatflow、Workflow。
2. 管理知识库，用于 RAG 检索。
3. 管理模型供应商，例如 Ollama、OpenAI compatible API。
4. 调用工具，例如 inner-ai-tools FastAPI 自定义工具。
5. 把用户输入、知识库、工具结果和 LLM 输出串成应用流程。
```

## 基础检查顺序

### 1. 检查 Web 是否可访问

在任意能访问内网的机器执行：

```bash
curl -I http://192.168.1.102
```

正常情况下应返回 `200`、`302` 或其他可解释的 HTTP 状态码。浏览器访问时可能跳转到：

```text
http://192.168.1.102/apps
```

### 2. 检查服务器端口

在 Windows PowerShell 中：

```powershell
Test-NetConnection 192.168.1.102 -Port 80
```

在 Linux Bash 中：

```bash
nc -zv 192.168.1.102 80
```

如果端口不通，优先检查防火墙、Nginx、Docker 端口映射和容器状态。

### 3. 检查 Docker Compose 服务

登录 Dify 服务器：

```bash
ssh root@192.168.1.102
```

进入部署目录：

```bash
cd /wtq/dify/dify-1.14.2/docker
docker compose ps
```

重点观察：

```text
容器是否 running
是否 unhealthy
端口是否正确映射
api、web、worker、db、redis、nginx 是否都在
```

### 4. 查看异常容器日志

```bash
docker compose logs --tail=200 api
docker compose logs --tail=200 worker
docker compose logs --tail=200 web
docker compose logs --tail=200 nginx
```

如果不确定容器名：

```bash
docker compose ps --services
```

## 常见故障和判断

### Dify 页面打不开

可能原因：

```text
1. 服务器 192.168.1.102 不通。
2. 80 端口未开放。
3. Nginx 容器未启动。
4. Web/API 容器异常。
5. Docker daemon 异常。
```

建议命令：

```bash
curl -I http://192.168.1.102
cd /wtq/dify/dify-1.14.2/docker
docker compose ps
docker compose logs --tail=100 nginx
```

### Dify 页面能打开，但应用回答失败

可能原因：

```text
1. LLM 模型服务不可访问。
2. Embedding 模型配置错误。
3. 知识库索引未完成。
4. Worker 容器异常。
5. 工具节点调用失败。
```

建议检查：

```bash
docker compose logs --tail=200 worker
docker compose logs --tail=200 api
curl http://192.168.1.106:11434/api/tags
```

### Dify Tool 导入失败

如果导入 FastAPI 的 `/openapi.json` 报 `invalid schema`，可能是 Dify 不兼容 FastAPI 默认的 OpenAPI 3.1.0。

本项目提供 Dify 专用 schema：

```text
http://192.168.1.103:8000/dify-openapi.json
```

在 Dify 自定义工具中使用这个 URL 导入。

## 高风险操作提醒

以下操作会影响正在运行的应用，执行前必须说明影响并确认：

```bash
docker compose down
docker compose down -v
docker volume rm ...
docker system prune -a
覆盖 .env
覆盖 docker-compose.yml
重建数据库容器
```

相对低风险的只读命令：

```bash
docker compose ps
docker compose logs --tail=200 api
docker stats --no-stream
curl -I http://192.168.1.102
```

## 验证命令

```bash
curl -I http://192.168.1.102
cd /wtq/dify/dify-1.14.2/docker
docker compose ps
docker compose logs --tail=50 api
```

## 关联文档

```text
07-dify-containers-guide.md
08-model-config-guide.md
06-common-errors-faq.md
10-ops-command-handbook.md
```
