# Dify 容器说明

## 文档用途

本文解释 Dify Docker Compose 中常见容器的职责和排查方法。适合回答：

```text
Dify 有哪些容器？
api、worker、web、nginx 分别负责什么？
哪个容器异常会导致知识库失败？
```

## 常见容器角色

Dify 的实际容器名称会随版本和 compose 项目名变化，但常见角色包括：

```text
api：后端 API 服务，处理应用、知识库、工具、模型配置等请求。
worker：异步任务服务，处理知识库索引、队列任务、后台任务。
web：前端页面服务，提供浏览器访问界面。
nginx：反向代理入口，通常暴露 80/443。
db/postgres：关系型数据库，保存应用配置和业务数据。
redis：缓存和队列。
sandbox：代码执行沙箱，部分工具或节点会使用。
plugin-daemon：插件服务，负责 Dify 插件相关能力。
weaviate/milvus：向量数据库，保存知识库向量。
```

## 容器调用关系

简化关系：

```text
浏览器
-> nginx
-> web / api
-> db / redis / worker
-> model provider / embedding / vector database
```

知识库导入链路：

```text
上传文档
-> api 接收任务
-> redis 队列
-> worker 处理分段和 embedding
-> 向量库保存向量
-> Dify 页面显示处理完成
```

工具调用链路：

```text
用户提问
-> Chatflow
-> Tool 节点
-> inner-ai-tools FastAPI
-> 返回 text
-> LLM 节点总结
```

## 常用检查命令

进入部署目录：

```bash
cd /wtq/dify/dify-1.14.2/docker
```

查看容器状态：

```bash
docker compose ps
```

查看服务列表：

```bash
docker compose ps --services
```

查看资源占用：

```bash
docker stats --no-stream
```

查看日志：

```bash
docker compose logs --tail=200 api
docker compose logs --tail=200 worker
docker compose logs --tail=200 web
docker compose logs --tail=200 nginx
```

## 按故障现象定位容器

### 页面打不开

优先检查：

```text
nginx
web
api
```

命令：

```bash
curl -I http://192.168.1.102
docker compose ps nginx web api
docker compose logs --tail=100 nginx
```

### 页面能打开，但应用报错

优先检查：

```text
api
worker
模型服务
```

命令：

```bash
docker compose logs --tail=200 api
docker compose logs --tail=200 worker
curl http://192.168.1.106:11434/api/tags
```

### 知识库一直处理中

优先检查：

```text
worker
redis
embedding 模型
向量数据库
```

命令：

```bash
docker compose logs --tail=300 worker
docker compose logs --tail=200 redis
curl http://192.168.1.101:11434/api/tags
```

### 工具节点调用失败

优先检查：

```text
api
inner-ai-tools FastAPI
网络连通性
```

命令：

```bash
curl http://192.168.1.103:8000/dify-openapi.json
curl http://192.168.1.103:8000/health/docker
docker compose logs --tail=200 api
```

## 重启建议

低风险查看命令：

```bash
docker compose ps
docker compose logs --tail=200 api
docker stats --no-stream
```

相对可控的重启：

```bash
docker compose restart api
docker compose restart worker
```

执行前说明影响：

```text
重启 api 可能导致 Dify 页面短暂不可用。
重启 worker 可能中断正在处理的知识库索引任务。
```

高风险命令：

```bash
docker compose down
docker compose down -v
docker volume rm ...
```

这些命令可能造成服务中断或数据丢失，不能在未确认影响时执行。

## 验证命令

```bash
docker compose ps
curl -I http://192.168.1.102
docker compose logs --tail=50 api
docker compose logs --tail=50 worker
```
