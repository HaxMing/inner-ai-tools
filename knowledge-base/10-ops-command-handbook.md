# 运维命令手册

## 文档用途

本文汇总内网 Docker、Dify、Ollama、Milvus、FastAPI Tool 的常用只读检查命令和低风险排障命令。适合回答：

```text
给我一组 Dify 排障命令。
怎么验证 Ollama 是否正常？
怎么检查 Milvus 端口？
怎么检查 FastAPI 工具是否能被 Dify 访问？
```

## 命令使用原则

优先执行只读命令：

```text
curl
docker ps
docker compose ps
docker logs --tail
docker stats --no-stream
Test-NetConnection
nc -zv
```

执行高风险命令前必须说明影响：

```text
docker compose down
docker compose down -v
docker volume rm
docker system prune -a
覆盖 .env
覆盖 docker-compose.yml
重启数据库
删除向量库数据
```

## Windows PowerShell 命令

### 检查 FastAPI 工具服务

```powershell
curl http://127.0.0.1:8000/health/docker
curl http://127.0.0.1:8000/health/ollama
curl http://127.0.0.1:8000/health/dify
curl http://127.0.0.1:8000/health/milvus
```

检查 Dify 能导入的 OpenAPI：

```powershell
curl http://192.168.1.103:8000/dify-openapi.json
```

### 启动 FastAPI

普通启动：

```powershell
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Docker 远程 SSH 检查模式：

```powershell
$env:DOCKER_CHECK_MODE="ssh"
$env:DOCKER_SSH_HOST="192.168.1.102"
$env:DOCKER_SSH_USERNAME="root"
$env:DOCKER_SSH_PASSWORD="你的服务器密码"
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

不要把真实密码写入 Git、README 或知识库。

### 检查端口

```powershell
Test-NetConnection 192.168.1.102 -Port 80
Test-NetConnection 192.168.1.102 -Port 19530
Test-NetConnection 192.168.1.106 -Port 11434
Test-NetConnection 192.168.1.101 -Port 11434
```

## Linux Bash 命令

### 检查 Dify

```bash
curl -I http://192.168.1.102
curl http://192.168.1.102
```

### 检查 Ollama

```bash
curl http://192.168.1.106:11434/api/tags
curl http://192.168.1.101:11434/api/tags
```

### 检查 Milvus

```bash
nc -zv 192.168.1.102 19530
```

### 检查 FastAPI Tool

从 Dify 服务器执行：

```bash
curl http://192.168.1.103:8000/dify-openapi.json
curl http://192.168.1.103:8000/health/docker
curl http://192.168.1.103:8000/health/ollama
curl http://192.168.1.103:8000/health/dify
curl http://192.168.1.103:8000/health/milvus
```

如果这里不通，Dify 工具节点也会失败。

## Docker Compose 命令

进入 Dify 部署目录：

```bash
cd /wtq/dify/dify-1.14.2/docker
```

查看状态：

```bash
docker compose ps
```

查看服务名：

```bash
docker compose ps --services
```

查看日志：

```bash
docker compose logs --tail=200 api
docker compose logs --tail=200 worker
docker compose logs --tail=200 web
docker compose logs --tail=200 nginx
```

查看资源：

```bash
docker stats --no-stream
```

## Docker 命令

查看 Docker 版本：

```bash
docker version
docker info --format '{{.ServerVersion}}'
```

查看容器：

```bash
docker ps
docker ps -a
```

查看镜像：

```bash
docker images
```

查看容器日志：

```bash
docker logs --tail=200 <container-name>
```

## 知识库排查命令

检查 worker：

```bash
cd /wtq/dify/dify-1.14.2/docker
docker compose logs --tail=300 worker
```

检查 Embedding：

```bash
curl http://192.168.1.101:11434/api/tags
```

检查 Rerank：

```bash
curl http://192.168.1.101:<rerank-port>/health
```

检查向量库端口：

```bash
nc -zv 192.168.1.102 19530
```

## 快速排障组合

### Dify 页面打不开

```bash
curl -I http://192.168.1.102
cd /wtq/dify/dify-1.14.2/docker
docker compose ps
docker compose logs --tail=100 nginx
docker compose logs --tail=100 web
```

### Dify 应用回答失败

```bash
cd /wtq/dify/dify-1.14.2/docker
docker compose logs --tail=200 api
docker compose logs --tail=200 worker
curl http://192.168.1.106:11434/api/tags
```

### 工具节点失败

```bash
curl http://192.168.1.103:8000/dify-openapi.json
curl http://192.168.1.103:8000/health/docker
curl http://192.168.1.103:8000/health/ollama
```

### 知识库召回失败

```bash
cd /wtq/dify/dify-1.14.2/docker
docker compose logs --tail=300 worker
curl http://192.168.1.101:11434/api/tags
nc -zv 192.168.1.102 19530
```
