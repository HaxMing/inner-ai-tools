# Milvus 说明

## 文档用途

本文记录 Milvus 的作用、当前部署地址、连通性检查方法和在 RAG 系统中的位置。适合回答：

```text
Milvus 是什么？
Milvus 19530 端口通不通怎么查？
Dify 是否一定要用 Milvus？
向量数据库异常怎么排查？
```

## 当前环境

```text
Milvus 服务器：192.168.1.102
Milvus 端口：19530
部署方式：Docker
```

当前 FastAPI 工具 `checkMilvusHealth` 做的是 TCP 端口连通性检查，不会读写 collection。

## Milvus 在 RAG 中的角色

Milvus 是向量数据库，用于保存文档片段的向量。典型流程：

```text
Markdown 文档
-> 分段
-> Embedding 模型生成向量
-> 向量写入 Milvus
-> 用户问题生成向量
-> Milvus 检索相似片段
-> Rerank 排序
-> LLM 生成答案
```

如果 Dify 当前使用其他向量库，Milvus 可能只是已经部署但尚未接入。是否接入要以 Dify 的实际 `.env` 和容器配置为准。

## 基础连通性检查

Windows PowerShell：

```powershell
Test-NetConnection 192.168.1.102 -Port 19530
```

Linux Bash：

```bash
nc -zv 192.168.1.102 19530
```

如果端口不通，检查：

```text
1. Milvus 容器是否启动。
2. 19530 是否映射到宿主机。
3. 防火墙是否放行。
4. Milvus 是否只监听容器内部网络。
```

## Docker 检查命令

登录服务器：

```bash
ssh root@192.168.1.102
```

查看 Milvus 相关容器：

```bash
docker ps | grep -i milvus
```

查看端口：

```bash
docker ps --format "table {{.Names}}\t{{.Ports}}" | grep -i milvus
```

查看日志：

```bash
docker logs --tail=200 <milvus-container-name>
```

## 常见问题

### 19530 端口不通

可能原因：

```text
1. Milvus 容器未启动。
2. Docker 端口未映射。
3. 防火墙拦截。
4. Milvus 启动失败。
```

排查命令：

```bash
docker ps | grep -i milvus
docker logs --tail=200 <milvus-container-name>
ss -lntp | grep 19530
```

### 端口通，但 Dify 用不了

可能原因：

```text
1. Dify 没有配置使用 Milvus。
2. Dify 容器内部访问地址写错。
3. Milvus collection 或索引异常。
4. Dify worker 没有完成知识库索引。
```

排查方向：

```bash
cd /wtq/dify/dify-1.14.2/docker
grep -i milvus .env
docker compose logs --tail=200 worker
docker compose logs --tail=200 api
```

### 知识库检索没有结果

可能原因：

```text
1. 文档还没有完成向量化。
2. Embedding 模型调用失败。
3. 向量库配置不匹配。
4. Score 阈值过高。
5. 用户问题和文档关键词差异太大。
```

排查步骤：

```text
1. 先看 Dify 知识库处理状态。
2. 再看 worker 日志。
3. 再检查 Embedding 服务。
4. 最后调整检索参数。
```

## 和 Weaviate、PostgreSQL 的区别

```text
Milvus：向量数据库，擅长大规模向量检索。
Weaviate：也可以做向量数据库，Dify 某些部署默认使用。
PostgreSQL：关系型数据库，保存用户、应用、配置等结构化数据。
```

不要把 PostgreSQL 当作向量库，也不要把 Milvus 当作业务数据库。

## 风险提醒

以下操作有高风险：

```bash
docker volume rm ...
删除 Milvus 数据目录
重建 Milvus collection
清空向量库
```

这些操作可能导致知识库索引丢失，需要重新导入和向量化文档。

## 验证命令

```bash
nc -zv 192.168.1.102 19530
docker ps | grep -i milvus
docker logs --tail=100 <milvus-container-name>
```
