from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.responses import HTMLResponse, JSONResponse

from app.config import Settings, get_settings
from app.dify_schema import get_dify_openapi_schema
from app.docs import get_local_docs_html
from app.schemas import HealthCheckResult
from app.services.health import check_dify, check_docker, check_milvus, check_ollama


# 这个 app 对象就是整个 FastAPI 服务的“总入口”。
# 类比 Spring Boot：
# - FastAPI(...) 约等于创建 Spring Boot Application；
# - @app.get(...) 约等于 @GetMapping(...)；
# - response_model 约等于声明接口返回 DTO；
# - Depends(get_settings) 约等于从容器/配置中心拿配置对象。
#
# 这里关闭默认 docs_url，是因为 FastAPI 默认 Swagger UI 依赖外网 CDN。
# 你的浏览器访问不到 CDN 时，/docs 会变成空白页。
# 我们下面自己注册一个本地 /docs 页面，不依赖外网。
app = FastAPI(
    title="inner-ai-tools",
    version="0.1.0",
    description="Read-only internal AI operation tools that can be imported by Dify Tool.",
    docs_url=None,
    redoc_url=None,
)


@app.get("/docs", include_in_schema=False)
async def local_docs() -> HTMLResponse:
    """返回本地自包含 API 文档页面。

    调用入口：
    - 浏览器访问 http://192.168.1.103:8000/docs

    内部流程：
    1. FastAPI 根据路径 `/docs` 找到当前函数；
    2. 当前函数调用 `app.docs.get_local_docs_html()` 生成 HTML；
    3. HTMLResponse 把 HTML 返回给浏览器；
    4. 浏览器页面里的 JS 再请求 `/openapi.json`，渲染接口列表。
    """

    return HTMLResponse(get_local_docs_html())


@app.get("/dify-openapi.json", include_in_schema=False)
async def dify_openapi() -> JSONResponse:
    """Return the OpenAPI schema that should be imported into Dify.

    Why not use `/openapi.json` directly?
    - FastAPI's built-in schema is OpenAPI 3.1.0.
    - Some Dify custom-tool importers reject 3.1.0 as invalid.
    - This endpoint returns a smaller OpenAPI 3.0.3 document.
    """

    return JSONResponse(get_dify_openapi_schema())


@app.get("/", tags=["meta"])
async def root() -> dict[str, object]:
    """服务首页，告诉调用方这个服务有哪些入口。

    调用入口：
    - 浏览器或 curl 访问 http://192.168.1.103:8000/

    数据流转：
    - 这个接口不调用外部服务；
    - 直接返回一个 dict；
    - FastAPI 会自动把 dict 转成 JSON。
    """

    return {
        "name": "inner-ai-tools",
        "docs": "/docs",
        "openapi": "/openapi.json",
        "dify_openapi": "/dify-openapi.json",
        "health_endpoints": [
            "/health/docker",
            "/health/ollama",
            "/health/dify",
            "/health/milvus",
        ],
    }


@app.get("/health/docker", response_model=HealthCheckResult, tags=["health"])
async def docker_health(
    settings: Annotated[Settings, Depends(get_settings)],
) -> HealthCheckResult:
    """检查 Docker 是否健康。

    调用入口：
    - Dify Tool / 浏览器 / curl 调用 GET /health/docker

    参数来源：
    - settings 不是用户传的参数；
    - `Depends(get_settings)` 会让 FastAPI 调用 app.config.get_settings()；
    - get_settings() 从环境变量读取 Docker 检查方式、SSH 地址、超时时间等配置。

    内部调用：
    - 当前函数只做路由入口；
    - 真正检查逻辑交给 app.services.health.check_docker()。

    返回对象：
    - check_docker() 返回 HealthCheckResult；
    - FastAPI 根据 response_model 把它序列化成 JSON。
    """

    return await check_docker(settings)


@app.get("/health/ollama", response_model=HealthCheckResult, tags=["health"])
async def ollama_health(
    settings: Annotated[Settings, Depends(get_settings)],
) -> HealthCheckResult:
    """检查 Ollama 服务是否健康。

    调用入口：
    - GET /health/ollama

    内部调用：
    - 当前路由函数调用 app.services.health.check_ollama(settings)；
    - check_ollama 会请求 `OLLAMA_BASE_URL/api/tags`；
    - 如果返回 2xx，就认为 Ollama 可访问，并提取模型名称列表。
    """

    return await check_ollama(settings)


@app.get("/health/dify", response_model=HealthCheckResult, tags=["health"])
async def dify_health(
    settings: Annotated[Settings, Depends(get_settings)],
) -> HealthCheckResult:
    """检查 Dify Web 服务是否健康。

    调用入口：
    - GET /health/dify

    内部调用：
    - 当前路由函数调用 app.services.health.check_dify(settings)；
    - check_dify 会先访问 `DIFY_BASE_URL + DIFY_HEALTH_PATH`；
    - 如果健康检查路径不存在，会退回访问 Dify 首页地址；
    - 只要 HTTP 返回成功，就认为 Dify 基本可访问。
    """

    return await check_dify(settings)


@app.get("/health/milvus", response_model=HealthCheckResult, tags=["health"])
async def milvus_health(
    settings: Annotated[Settings, Depends(get_settings)],
) -> HealthCheckResult:
    """检查 Milvus 端口是否可连接。

    调用入口：
    - GET /health/milvus

    内部调用：
    - 当前路由函数调用 app.services.health.check_milvus(settings)；
    - check_milvus 不登录 Milvus，也不读写 collection；
    - 它只做 TCP 连接测试，确认 `MILVUS_HOST:MILVUS_PORT` 能连上。
    """

    return await check_milvus(settings)
