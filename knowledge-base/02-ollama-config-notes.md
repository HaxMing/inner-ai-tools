# Ollama 配置笔记

## 文档用途

本文记录内网 Ollama 的服务地址、模型用途、检查命令和 Dify 接入注意事项。适合回答：

```text
Ollama 服务是否正常？
Dify 里怎么配置 Ollama？
Ollama 模型列表怎么查？
LLM 和 Embedding 为什么要分开？
```

## 当前环境

```text
LLM 服务器：192.168.1.106:11434
LLM 服务：Ollama
主用 LLM：qwen3.6:27b

Embedding 服务器：192.168.1.101:11434
Embedding 服务：Ollama
Embedding 模型：bge-m3
```

注意：LLM 和 Embedding 可以部署在不同机器上。Dify 配置时要分别填写对应地址。

## Ollama 在系统中的角色

Ollama 负责提供本地大模型推理服务。当前项目中有两类模型：

```text
1. Chat LLM：负责理解用户问题、组织答案、解释工具返回结果。
2. Embedding 模型：负责把知识库文档和用户问题转成向量，用于 RAG 检索。
```

LLM 和 Embedding 的调用链：

```text
用户问题
-> Dify
-> Embedding 模型把问题向量化
-> 知识库检索
-> Rerank 重新排序
-> LLM 根据上下文生成答案
```

## 检查 Ollama 服务

### 检查 LLM 服务器

```bash
curl http://192.168.1.106:11434/api/tags
```

正常返回中应包含模型列表，例如：

```json
{
  "models": [
    {
      "name": "qwen3.6:27b"
    }
  ]
}
```

### 检查 Embedding 服务器

```bash
curl http://192.168.1.101:11434/api/tags
```

应能看到：

```text
bge-m3
```

如果模型列表为空，说明模型未拉取、服务未启动或访问到了错误机器。

## Dify 中配置 Ollama

在 Dify 模型供应商中配置：

```text
模型类型：LLM
Provider：Ollama 或 OpenAI-API-compatible，按 Dify 当前页面支持选择
Base URL：http://192.168.1.106:11434
模型名：qwen3.6:27b
```

Embedding 配置：

```text
模型类型：Text Embedding
Base URL：http://192.168.1.101:11434
模型名：bge-m3
```

如果 Dify 容器访问 Ollama 失败，要从 Dify 服务器 `192.168.1.102` 上测试：

```bash
curl http://192.168.1.106:11434/api/tags
curl http://192.168.1.101:11434/api/tags
```

如果服务器上通，但 Dify 页面不通，继续检查 Dify 容器内部网络或模型供应商配置。

## 常见问题

### Dify 提示模型不可用

可能原因：

```text
1. Base URL 填错。
2. 模型名和 Ollama 中实际模型名不一致。
3. Dify 服务器无法访问 Ollama 服务器。
4. Ollama 未监听 0.0.0.0，只监听 127.0.0.1。
5. 防火墙未开放 11434。
```

验证命令：

```bash
curl http://192.168.1.106:11434/api/tags
curl http://192.168.1.101:11434/api/tags
```

### 知识库导入很慢

可能原因：

```text
1. Embedding 模型响应慢。
2. 文档太大，分段过多。
3. Dify worker 资源不足。
4. Embedding 服务器显存或 CPU 压力高。
```

排查命令：

```bash
curl http://192.168.1.101:11434/api/tags
nvidia-smi
docker compose logs --tail=200 worker
```

### 回答慢

可能原因：

```text
1. LLM 模型较大，例如 qwen3.6:27b。
2. 上下文太长。
3. Top K 太大。
4. Rerank 和工具调用增加了整体耗时。
```

优化方向：

```text
降低 Top K
缩短文档分段
减少无关知识库
只在需要时调用工具
```

## 安全提醒

Ollama API 默认没有复杂权限控制。内网使用时建议：

```text
1. 只在可信内网开放。
2. 不要直接暴露到公网。
3. 通过防火墙限制访问来源。
4. Dify 中不要把服务器密码写入提示词或知识库。
```

## 验证命令

```bash
curl http://192.168.1.106:11434/api/tags
curl http://192.168.1.101:11434/api/tags
```

Windows PowerShell：

```powershell
Invoke-RestMethod http://192.168.1.106:11434/api/tags
Invoke-RestMethod http://192.168.1.101:11434/api/tags
```
