# 安全风险检查

本文档记录 `inner-ai-tools` 当前的安全边界、已控制风险和后续改进建议。

## 安全定位

当前项目定位是“只读内网健康检查工具”。

允许：

- 查询 Docker Server 版本。
- 查询 Ollama `/api/tags`。
- 查询 Dify Web 是否可访问。
- 检查 Milvus TCP 端口是否可连接。
- 给 Dify Tool / Agent 提供只读工具调用。

不允许：

- 删除容器。
- 清理 volume。
- 重启服务。
- 修改配置。
- 覆盖文件。
- 创建、删除或写入 Milvus collection。

## 已控制风险

| 风险 | 当前控制方式 |
| --- | --- |
| Agent 误执行高危命令 | FastAPI 只暴露健康检查接口，没有写操作接口 |
| Dify Tool 导入不兼容 | 单独提供 OpenAPI 3.0.3 的 `/dify-openapi.json` |
| 默认 `/docs` 依赖外网 CDN | 自定义本地 `/docs` 页面 |
| 内网请求被系统代理影响 | httpx 请求使用 `trust_env=False` |
| Docker 检查阻塞 FastAPI 事件循环 | 阻塞命令放到 `asyncio.to_thread()` 中执行 |
| 配置格式错误导致启动崩溃 | `config.py` 对 int/float 环境变量做了兜底 |
| 健康检查返回格式不一致 | 统一返回 `HealthCheckResult` |

## 敏感信息风险

### SSH 密码

`DOCKER_SSH_PASSWORD` 只应该放在本机环境变量或本机未提交的 `.env` 文件中。

不要写入：

- README。
- `docs/` 文档。
- `knowledge-base/` 文档。
- Git commit message。
- Dify 知识库。
- Dify Agent 提示词。

更推荐的方式是使用：

```text
DOCKER_SSH_KEY_PATH
```

也就是 SSH 私钥路径。

### 内网地址

项目文档里包含内网 IP，例如：

- `192.168.1.102`
- `192.168.1.103`
- `192.168.1.106`

如果仓库改成公开仓库，这些信息会暴露内网拓扑。建议正式发布前：

1. 把仓库设置为 private。
2. 或者把 IP 改成示例地址，例如 `192.168.x.x`。
3. 或者将真实地址移到本地 `.env`，文档只写变量名。

## 接口暴露风险

当前服务启动命令使用：

```powershell
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

这会让局域网内其他机器访问 `8000` 端口。

建议：

- 只在可信内网中使用。
- Windows 防火墙只允许 Dify 服务器 `192.168.1.102` 访问 `8000`。
- 不要把 `8000` 端口映射到公网。
- 如果后续部署到长期运行环境，要增加鉴权或反向代理访问控制。

## Dify Agent 风险

Dify Agent 提示词中必须明确：

```text
你只能进行只读检查。
不能自动执行删除容器、清理 volume、重启服务、修改配置、覆盖文件等高风险操作。
```

4 个工具没有输入参数，提示词中也要明确：

```text
调用 checkDockerHealth、checkOllamaHealth、checkDifyHealth、checkMilvusHealth 时，工具参数必须是空 JSON 对象 {}。
```

这样可以降低 Agent 把用户问题文本错误传给工具的概率。

## 代码层风险检查

| 检查项 | 当前状态 |
| --- | --- |
| 是否存在删除命令 | 未发现 |
| 是否存在重启命令 | 未发现 |
| 是否存在清理 volume 命令 | 未发现 |
| 是否存在写 Milvus 数据逻辑 | 未发现 |
| 是否把密码写死在代码里 | 未发现，`.env.example` 中密码为空 |
| 是否对外部 HTTP 请求设置超时 | 已设置 |
| 是否对 TCP 检查设置超时 | 已设置 |
| 是否统一错误返回 | 已通过 `HealthCheckResult.details.error` 返回 |

## 后续建议

如果项目从学习练习走向团队内长期使用，建议补充：

- API 鉴权，例如内网 token 或反向代理 Basic Auth。
- 请求日志和审计日志。
- 更完整的异常测试。
- SSH 私钥方式替代密码方式。
- 访问来源限制，只允许 Dify 服务器调用。
- 对 Agent 输出做更严格的高危操作拦截。

本阶段先保持只读工具边界，避免过早暴露写操作。
