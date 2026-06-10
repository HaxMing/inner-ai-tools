from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


# 这个文件专门放“接口数据结构”。
# 类比 Java/Spring Boot：
# - Pydantic BaseModel 约等于 DTO；
# - Field(...) 约等于字段说明、校验信息、Swagger/OpenAPI 文档信息。


# Literal 表示 status 字段只能取这两个字符串之一。
# 如果代码里写成 "ok" 或 "bad"，Pydantic 会认为不符合模型定义。
HealthStatus = Literal["healthy", "unhealthy"]


class HealthCheckResult(BaseModel):
    """所有健康检查接口统一返回这个对象。

    为什么统一返回结构？
    - Dify Tool 或前端调用时，不用为每个服务写一套解析逻辑；
    - 只要看 ok/status 就知道是否成功；
    - details 里再放每个服务自己的扩展信息。

    返回 JSON 大概长这样：
    {
      "service": "ollama",
      "ok": true,
      "status": "healthy",
      "checked_at": "2026-06-10T08:09:05Z",
      "response_time_ms": 1521.19,
      "details": {
        "url": "http://192.168.1.106:11434/api/tags",
        "model_count": 1
      }
    }
    """

    # 被检查的服务名称，例如 docker、ollama、dify、milvus。
    service: str = Field(..., examples=["ollama"])

    # 布尔值，给程序判断用：true 表示健康，false 表示异常。
    ok: bool = Field(..., description="Whether this health check passed.")

    # 字符串状态，给人阅读用：healthy / unhealthy。
    status: HealthStatus

    # 检查发生的时间。service 层会统一使用 UTC 时间。
    checked_at: datetime

    # 本次检查耗时，单位毫秒。用于观察哪个服务响应慢。
    response_time_ms: float

    # 每个服务自己的细节信息。
    # 例如 Ollama 会放模型列表，Docker 会放 server_version，Milvus 会放 host/port。
    details: dict[str, Any] = Field(default_factory=dict)
