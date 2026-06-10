from dataclasses import dataclass
from functools import lru_cache
import os


# 这个文件专门负责“读取配置”。
# 对你从 Java 转 Python 来说，可以把它类比成 Spring Boot 里的配置类：
# - Java: application.yml + @ConfigurationProperties
# - 这里: 环境变量 + Settings dataclass


def _get_float(name: str, default: float) -> float:
    """从环境变量读取 float。

    为什么不直接 float(os.getenv(...))？
    - 因为用户可能没有配置这个环境变量；
    - 也可能配置成了非法字符串，比如 abc；
    - 这里统一兜底，避免服务启动时因为配置格式错误直接崩掉。
    """

    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        return float(raw_value)
    except ValueError:
        return default


def _get_int(name: str, default: int) -> int:
    """从环境变量读取 int，读取失败时返回默认值。"""

    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        return int(raw_value)
    except ValueError:
        return default


def _strip_trailing_slash(url: str) -> str:
    """去掉 URL 末尾的 /。

    例子：
    - http://192.168.1.106:11434/ -> http://192.168.1.106:11434

    这样后面拼接 `/api/tags` 时不会出现双斜杠。
    """

    return url.rstrip("/")


def _normalize_path(path: str) -> str:
    """把路径统一成以 / 开头。

    例子：
    - health -> /health
    - /health -> /health
    - 空字符串 -> /
    """

    if not path:
        return "/"
    return path if path.startswith("/") else f"/{path}"


@dataclass(frozen=True)
class Settings:
    """项目运行配置。

    数据来源：
    - 所有字段都由 get_settings() 从环境变量读取；
    - 如果环境变量不存在，就使用项目里的默认值。

    为什么用 frozen=True？
    - 配置对象创建后不应该在业务代码里被随便修改；
    - 这样能减少排查问题时的不确定性。
    """

    docker_check_mode: str
    ollama_base_url: str
    dify_base_url: str
    dify_health_path: str
    milvus_host: str
    milvus_port: int
    http_timeout_seconds: float
    docker_timeout_seconds: float
    socket_timeout_seconds: float
    docker_command: str
    docker_ssh_host: str
    docker_ssh_port: int
    docker_ssh_username: str
    docker_ssh_password: str | None
    docker_ssh_key_path: str | None
    docker_ssh_command: str

    @property
    def dify_health_url(self) -> str:
        """拼出 Dify 健康检查完整 URL。"""

        return f"{self.dify_base_url}{self.dify_health_path}"


@lru_cache
def get_settings() -> Settings:
    """读取并缓存配置。

    调用方：
    - app.main 里的每个路由函数都会通过 Depends(get_settings) 获取配置。

    为什么加 @lru_cache？
    - FastAPI 每次请求都会解析依赖；
    - 配置通常不需要每个请求都重新读取环境变量；
    - 加缓存后，同一个进程里只创建一次 Settings 对象。

    注意：
    - 如果你改了环境变量，需要重启 uvicorn，配置才会重新读取。
    """

    return Settings(
        docker_check_mode=os.getenv("DOCKER_CHECK_MODE", "cli").lower(),
        ollama_base_url=_strip_trailing_slash(
            os.getenv("OLLAMA_BASE_URL", "http://192.168.1.106:11434")
        ),
        dify_base_url=_strip_trailing_slash(
            os.getenv("DIFY_BASE_URL", "http://192.168.1.102")
        ),
        dify_health_path=_normalize_path(os.getenv("DIFY_HEALTH_PATH", "/health")),
        milvus_host=os.getenv("MILVUS_HOST", "192.168.1.102"),
        milvus_port=_get_int("MILVUS_PORT", 19530),
        http_timeout_seconds=_get_float("HTTP_TIMEOUT_SECONDS", 3.0),
        docker_timeout_seconds=_get_float("DOCKER_TIMEOUT_SECONDS", 5.0),
        socket_timeout_seconds=_get_float("SOCKET_TIMEOUT_SECONDS", 3.0),
        docker_command=os.getenv("DOCKER_COMMAND", "docker"),
        docker_ssh_host=os.getenv("DOCKER_SSH_HOST", "192.168.1.102"),
        docker_ssh_port=_get_int("DOCKER_SSH_PORT", 22),
        docker_ssh_username=os.getenv("DOCKER_SSH_USERNAME", "root"),
        docker_ssh_password=os.getenv("DOCKER_SSH_PASSWORD") or None,
        docker_ssh_key_path=os.getenv("DOCKER_SSH_KEY_PATH") or None,
        docker_ssh_command=os.getenv(
            "DOCKER_SSH_COMMAND",
            "docker info --format '{{.ServerVersion}}'",
        ),
    )
