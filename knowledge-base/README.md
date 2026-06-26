# 内网 Dify 运维知识库

这个目录用于第三阶段学习：把内网 Docker、Dify、Ollama、Milvus、Rerank、模型配置和常见故障整理成 Markdown 文档，然后上传到 Dify 知识库，练习 RAG 检索、混合检索、Rerank、Top K、Score 阈值和引用来源。

## 推荐导入方式

在 Dify 知识库中创建一个新知识库，例如：

```text
内网 Docker/Dify 运维知识库
```

然后上传本目录下的 10 篇 Markdown：

```text
01-dify-deployment-notes.md
02-ollama-config-notes.md
03-docker-image-offline-import.md
04-rerank-deployment-notes.md
05-milvus-guide.md
06-common-errors-faq.md
07-dify-containers-guide.md
08-model-config-guide.md
09-rag-tuning-log.md
10-ops-command-handbook.md
```

## 推荐检索配置

初始配置建议：

```text
Embedding 模型：bge-m3
检索方式：混合检索
Rerank 模型：bge-reranker-v2-m3
Top K：5
Score 阈值：0.35
分段方式：按标题自动分段，必要时手动调整
分段长度：约 600-900 tokens
分段重叠：约 80-120 tokens
```

如果回答经常漏掉关键信息：

```text
Top K 调到 8
Score 阈值降到 0.25-0.3
检查文档标题和问题关键词是否一致
```

如果回答引用太多无关内容：

```text
Top K 降到 3-5
Score 阈值调到 0.45-0.6
检查是否有多篇文档写了重复但不一致的内容
```

## 推荐测试问题

上传完成后，在 Dify 应用中测试：

```text
Dify 页面打不开应该怎么排查？
Ollama 连接失败应该检查哪些配置？
Docker 镜像如何离线导入？
Rerank 服务不可用会影响什么？
Milvus 19530 端口通但 Dify 用不了该怎么办？
帮我检查 Docker、Ollama、Dify、Milvus 当前状态并给出排查建议。
```

## 文档维护规则

1. 每次解决一个真实故障，都追加到 `06-common-errors-faq.md`。
2. 每次调整知识库参数，都追加到 `09-rag-tuning-log.md`。
3. 涉及删除、重启、清理、覆盖配置的命令，必须写清楚影响。
4. 不要把服务器密码、数据库密码、API Key 写入知识库。
5. 命令尽量给出可复制版本，并标明是在 Windows PowerShell 还是 Linux Bash 执行。
