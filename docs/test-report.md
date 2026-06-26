# 测试报告

报告日期：2026-06-26

## 测试目标

本次测试覆盖 `inner-ai-tools` 的核心工程质量要求：

- FastAPI 路由能正常注册。
- 首页能返回 Dify Tool 需要的入口信息。
- `/docs` 页面不依赖外网 CDN。
- `/dify-openapi.json` 使用 Dify 更容易接受的 OpenAPI 3.0.3。
- 4 个健康检查接口能正确调用 service 层函数。

## 测试环境

| 项目 | 值 |
| --- | --- |
| 操作系统 | Windows |
| Python | 3.11.9 |
| 包管理器 | uv |
| 测试框架 | pytest |
| 项目路径 | `F:\wtqcode\inner-ai-tools\inner-ai-tools` |

## 执行命令

```powershell
cd F:\wtqcode\inner-ai-tools\inner-ai-tools
uv run pytest
```

## 自动化测试结果

最近一次执行结果：

```text
collected 7 items
tests\test_health_endpoints.py ....... [100%]
7 passed, 1 warning in 0.53s
```

警告信息：

```text
StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.
```

这个 warning 来自第三方测试依赖链，不影响当前业务逻辑。后续如果 FastAPI / Starlette 升级，可以再观察是否需要调整测试客户端依赖。

## 测试用例清单

| 用例 | 覆盖点 |
| --- | --- |
| `test_root_lists_dify_tool_metadata` | `/` 能返回 `/openapi.json`、`/dify-openapi.json` 和健康检查入口 |
| `test_docs_page_is_local_and_does_not_use_cdn` | `/docs` 返回本地页面，且不包含 `https://cdn.jsdelivr.net` |
| `test_dify_openapi_schema_is_compatible_with_dify` | `/dify-openapi.json` 为 OpenAPI 3.0.3，且只暴露健康检查工具 |
| `test_health_endpoint_routes` | 4 个健康检查路由能调用对应 service 函数，并返回统一结构 |

## 手动验证建议

自动化测试使用 monkeypatch 替换了真实健康检查函数，目的是验证路由和数据结构。上线前还需要手动验证真实内网连通性：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health/docker
Invoke-RestMethod http://127.0.0.1:8000/health/ollama
Invoke-RestMethod http://127.0.0.1:8000/health/dify
Invoke-RestMethod http://127.0.0.1:8000/health/milvus
```

从 Dify 服务器验证：

```bash
curl http://192.168.1.103:8000/dify-openapi.json
curl http://192.168.1.103:8000/health/dify
```

## 当前测试缺口

- 还没有对 SSH Docker 检查做 mock 单元测试。
- 还没有对 httpx 超时、连接失败、非 JSON 响应做完整异常测试。
- 还没有对 Milvus TCP 连接失败场景做专门测试。
- 还没有覆盖环境变量非法值的测试，例如端口不是数字、超时时间不是数字。

这些缺口不影响当前学习阶段交付，但如果后续准备放到团队内长期使用，建议补齐。
