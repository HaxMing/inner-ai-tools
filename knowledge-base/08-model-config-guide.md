# 模型配置说明

## 文档用途

本文记录 Dify 中 LLM、Embedding、Rerank 的配置关系和排查方式。适合回答：

```text
LLM、Embedding、Rerank 分别是什么？
Dify 里模型怎么配？
为什么知识库需要 embedding？
为什么回答需要 LLM？
```

## 当前模型清单

```text
LLM：
  模型：qwen3.6:27b
  服务：Ollama
  地址：http://192.168.1.106:11434

Embedding：
  模型：bge-m3
  服务：Ollama
  地址：http://192.168.1.101:11434

Rerank：
  模型：bge-reranker-v2-m3
  服务：vLLM
  地址：192.168.1.101，端口以实际部署为准
```

## 三类模型的职责

### LLM

LLM 负责生成最终回答。

输入通常包括：

```text
用户问题
知识库召回内容
工具调用结果
系统提示词
```

输出：

```text
中文解释
操作步骤
验证命令
风险提醒
```

### Embedding

Embedding 负责把文本转成向量。

用在两个地方：

```text
1. 知识库导入时，把文档片段向量化。
2. 用户提问时，把问题向量化，用于检索相似片段。
```

### Rerank

Rerank 负责对检索出来的候选片段重新排序。

作用：

```text
把真正能回答问题的片段排到前面
减少无关上下文进入 LLM
提升引用来源准确性
```

## Dify 应用中的推荐组合

用于“内网 Docker/Dify 故障排查助手”：

```text
应用类型：Chatflow
LLM：qwen3.6:27b
知识库：内网 Docker/Dify 运维知识库
检索方式：混合检索
Embedding：bge-m3
Rerank：bge-reranker-v2-m3
工具：inner-ai-tools
```

推荐流程：

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

## 模型配置排查

### 检查 LLM

```bash
curl http://192.168.1.106:11434/api/tags
```

应看到：

```text
qwen3.6:27b
```

### 检查 Embedding

```bash
curl http://192.168.1.101:11434/api/tags
```

应看到：

```text
bge-m3
```

### 检查 Rerank

按 vLLM 实际启动端口检查。常见思路：

```bash
curl http://192.168.1.101:<rerank-port>/health
```

如果没有 health 接口，就用实际 OpenAI-compatible endpoint 测试。

## 常见配置错误

### 模型名写错

现象：

```text
Dify 提示模型不存在或调用失败。
```

解决：

```bash
curl http://模型服务器:11434/api/tags
```

以返回的 `name` 为准填写。

### Base URL 写错

错误示例：

```text
http://192.168.1.106
```

正确示例：

```text
http://192.168.1.106:11434
```

### Embedding 和 LLM 配反

表现：

```text
知识库导入失败
模型调用异常
检索没有结果
```

修复：

```text
LLM 使用 qwen3.6:27b
Embedding 使用 bge-m3
Rerank 使用 bge-reranker-v2-m3
```

## 调优建议

如果回答事实错误：

```text
检查知识库召回片段
启用 Rerank
降低无关文档数量
提示词要求引用工具结果和知识库依据
```

如果回答太慢：

```text
减少 Top K
减少工具调用数量
缩短上下文
检查 qwen3.6:27b 推理速度
```

如果回答说不知道：

```text
降低 Score 阈值
增加常见问法
补充 FAQ 文档
重新索引知识库
```
