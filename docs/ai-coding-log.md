# AI Coding 使用记录

本文档记录 `inner-ai-tools` 学习过程中的 AI Coding 使用方式、人工判断和交付结果。

## 使用目标

本项目不是单纯让 AI 生成代码，而是练习岗位要求里的能力：

- 需求拆解。
- 代码生成。
- 代码重构。
- 测试用例生成。
- Bug 修复。
- 技术文档编写。
- AI 生成代码审查。
- Dify Tool / Agent / RAG 应用落地。

## 阶段记录

### 第 2 阶段：FastAPI 工具服务

目标：实现一个能被 Dify Tool 调用的 FastAPI 服务。

产出：

- `GET /health/docker`
- `GET /health/ollama`
- `GET /health/dify`
- `GET /health/milvus`
- `HealthCheckResult` 统一返回结构。
- `.env.example` 环境变量示例。

AI 辅助点：

- 拆分 FastAPI 路由层、配置层、service 层、schema 层。
- 生成接口注释，帮助理解调用链。
- 生成 pytest 测试用例。

人工校验点：

- 确认接口只读，不包含删除、重启、清理等命令。
- 确认 Windows 本机和远程 Linux 服务的网络关系。
- 确认 Docker 检查需要支持 `cli` 和 `ssh` 两种模式。

### 第 3 阶段：Dify RAG 知识库

目标：整理内网 Dify 运维知识库，用于故障问答。

产出：

- `knowledge-base/01-dify-deployment-notes.md`
- `knowledge-base/02-ollama-config-notes.md`
- `knowledge-base/03-docker-image-offline-import.md`
- `knowledge-base/04-rerank-deployment-notes.md`
- `knowledge-base/05-milvus-guide.md`
- `knowledge-base/06-common-errors-faq.md`
- `knowledge-base/07-dify-containers-guide.md`
- `knowledge-base/08-model-config-guide.md`
- `knowledge-base/09-rag-tuning-log.md`
- `knowledge-base/10-ops-command-handbook.md`

AI 辅助点：

- 把真实部署过程整理成 Markdown。
- 把常见故障整理成 FAQ。
- 生成知识库调参记录模板。

人工校验点：

- 使用 Dify 召回测试验证 RAG 是否能召回正确文档。
- 启动 rerank 模型后，对比召回分数和排序变化。
- 根据测试结果调整 Top K、Score 阈值和混合检索。

### 第 4 阶段：Chatflow / Workflow

目标：从普通问答升级成流程化 AI 应用。

产出：

- Docker/Dify/Ollama/Milvus 故障排查 Chatflow。
- 内网服务部署方案生成 Workflow。
- 参数校验分支，参数错误时直接输出修正建议。

AI 辅助点：

- 设计分类器提示词。
- 设计参数校验提示词和结构化输出。
- 设计部署方案生成提示词。

人工校验点：

- 检查模型是否输出 `<think>`，并用结构化输出减少解析风险。
- 检查 Workflow 在错误参数下是否进入错误输出分支。
- 检查部署方案是否包含风险提醒、验证命令和配置说明。

### 第 5 阶段：Dify Tool + Agent

目标：把 FastAPI 健康检查工具接入 Dify Agent。

产出：

- `checkDockerHealth`
- `checkOllamaHealth`
- `checkDifyHealth`
- `checkMilvusHealth`
- 内网运维 Agent 提示词。

AI 辅助点：

- 生成 Agent 安全限制。
- 生成工具调用规则。
- 根据 Dify 报错调整提示词，例如工具参数必须是 `{}`。

人工校验点：

- 实测单个服务检查。
- 实测全部服务检查。
- 实测高危请求，例如“删除 Dify volume 并重启”，确认 Agent 不会直接执行。
- 控制工具调用次数，避免 Agent 重复检索知识库和长时间卡住。

### 第 6 阶段：Dify API 集成

目标：在代码里调用 Dify，不只是在页面里点。

产出：

- Spring Boot demo 调用 Dify 应用 API。
- 处理 API Key、conversationId、错误响应和 streaming 模式。

AI 辅助点：

- 生成 Spring Boot controller/service/config 结构。
- 排查 PowerShell `curl` 和 `Invoke-RestMethod` 差异。
- 排查 Dify API 参数缺失、blocking mode 不支持等错误。

人工校验点：

- 用 Postman 调用本地 Spring Boot 接口。
- 确认 Dify 返回 `answer`、`conversationId`、`messageId`、`taskId`。
- 确认 API Key 不写死在代码里。

## 典型问题和修复记录

| 问题 | 原因 | 修复 |
| --- | --- | --- |
| `/docs` 打开空白 | FastAPI 默认 Swagger UI 依赖外网 CDN | 使用 `app/docs.py` 提供本地自包含页面 |
| Dify Tool 导入 `invalid schema` | Dify 对 OpenAPI 3.1.0 兼容性不好 | 新增 `/dify-openapi.json`，返回 OpenAPI 3.0.3 |
| Docker 返回 `Docker CLI was not found in PATH` | FastAPI 运行在 Windows，本机没有 Docker CLI | 支持 `DOCKER_CHECK_MODE=ssh` 检查远程 Docker |
| Ollama 内网访问超时 | 可能受系统代理或网络影响 | httpx 请求使用 `trust_env=False`，并明确检查目标地址 |
| Agent 工具参数报错 | 无参工具被传入字符串 | 提示词中要求工具参数必须是空 JSON 对象 `{}` |
| Agent 思考过久 | ReAct 多轮工具调用和知识库重复检索 | 增加工具调用限制，healthy 时不检索知识库 |

## AI 生成内容审查原则

每次让 AI 生成代码或文档后，至少做这些检查：

1. 是否符合当前项目结构。
2. 是否引入了不必要的新依赖。
3. 是否把真实密码、API Key、Token 写进文件。
4. 是否包含删除、重启、清理、覆盖配置等高风险操作。
5. 是否能通过 `uv run pytest`。
6. 是否能被 Dify 实际导入和调用。
7. 是否有必要注释，方便后续复盘和面试讲解。

## 当前阶段交付物

第 7 阶段已补充：

- `README.md`
- `docs/api.md`
- `docs/deploy.md`
- `docs/test-report.md`
- `docs/security-review.md`
- `docs/ai-coding-log.md`

暂不处理：

- CI/CD 基础。
- Docker Compose。
