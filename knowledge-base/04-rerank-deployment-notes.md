# Rerank 部署笔记

## 文档用途

本文记录 Rerank 在 Dify RAG 流程中的作用、部署位置、检查方法和调优方式。适合回答：

```text
Rerank 是什么？
为什么混合检索后还要 Rerank？
Rerank 服务不可用会怎样？
Top K 和 Rerank 怎么配？
```

## 当前环境

```text
Rerank 服务器：192.168.1.101
部署方式：vLLM
Rerank 模型：bge-reranker-v2-m3
```

具体端口以实际 vLLM 启动参数为准。不要在知识库中记录服务密钥。

## Rerank 在 RAG 中的角色

RAG 检索通常分为两层：

```text
第一层：召回
第二层：重排
```

第一层召回负责从大量文档片段中找出可能相关的内容。召回方式可以是：

```text
向量检索
关键词检索
混合检索
```

第二层 Rerank 负责重新判断“用户问题”和“候选片段”的相关性，把最相关的内容排到前面。

典型流程：

```text
用户问题
-> Embedding
-> 混合检索召回 Top N
-> Rerank 重新排序
-> 取 Top K
-> 拼接上下文
-> LLM 生成答案
```

## 为什么需要 Rerank

Embedding 更擅长语义相似，关键词检索更擅长精确匹配。两者都可能召回一些“看起来相关但并不真正回答问题”的片段。

Rerank 的价值：

```text
1. 提升最终上下文的准确性。
2. 减少无关片段进入 LLM。
3. 提升引用来源的可信度。
4. 降低模型编造答案的概率。
```

## Dify 中的推荐配置

初始建议：

```text
检索方式：混合检索
Embedding：bge-m3
Rerank：bge-reranker-v2-m3
Top K：5
Score 阈值：0.35
```

如果知识库文档比较少，可以：

```text
Top K：3-5
Score 阈值：0.35-0.5
```

如果知识库文档很多，可以：

```text
候选召回数量适当增加
启用 Rerank
最终 Top K 保持 5-8
```

## 检查 Rerank 是否生效

在 Dify 页面观察：

```text
知识库召回结果是否更贴近问题
引用来源是否集中在正确文档
回答是否减少无关片段
```

测试问题：

```text
Dify Tool 导入 invalid schema 怎么处理？
Ollama 模型不可用怎么排查？
Docker 镜像离线导入后 compose 仍然拉取怎么办？
```

如果没有 Rerank，可能会召回泛泛的 Docker 或 Dify 文档；启用 Rerank 后，应优先召回对应 FAQ 或专项文档。

## 常见问题

### Rerank 服务不可用

影响：

```text
1. 知识库仍可能通过向量或关键词检索返回结果。
2. 结果排序可能变差。
3. LLM 更容易拿到不相关上下文。
```

排查：

```bash
curl http://192.168.1.101:<rerank-port>/health
```

如果没有 health 接口，按实际 vLLM OpenAI-compatible 接口测试。

### 回答引用不准确

可能原因：

```text
1. Top K 太大，无关片段进入上下文。
2. Score 阈值太低。
3. 文档分段太长，一个 chunk 里混入多个主题。
4. 多篇文档重复写了相似但不一致的信息。
```

优化：

```text
降低 Top K
提高 Score 阈值
按主题拆分文档
让标题包含问题关键词
```

### 回答说知识库没有记录，但明明有

可能原因：

```text
1. Score 阈值太高，相关片段被过滤。
2. 用户问法和文档关键词差异太大。
3. 文档没有重新索引。
4. Rerank 模型配置错误。
```

优化：

```text
降低 Score 阈值到 0.25-0.35
增加同义词和常见问法
重新处理知识库
检查 Rerank 服务日志
```

## 风险提醒

Rerank 调优不会修改业务数据，但会影响回答质量。每次调整参数后，建议记录在：

```text
09-rag-tuning-log.md
```

记录内容：

```text
调整前参数
调整后参数
测试问题
回答变化
是否保留
```
