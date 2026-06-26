import asyncio
from datetime import datetime, timezone
import shutil
import socket
import subprocess
import time
from typing import Any

import httpx
import paramiko

from app.config import Settings
from app.schemas import HealthCheckResult


# 这个文件是“业务服务层”。
# app.main 只负责 HTTP 路由入口，真正的健康检查逻辑都放在这里。
#
# 整体调用链：
# 1. 用户或 Dify 调用 GET /health/xxx；
# 2. app.main 里的路由函数收到请求；
# 3. 路由函数调用本文件里的 check_xxx(settings)；
# 4. check_xxx 访问 Docker/Ollama/Dify/Milvus；
# 5. 本文件把检查结果封装成 HealthCheckResult；
# 6. FastAPI 把 HealthCheckResult 转成 JSON 返回。


def _now_utc() -> datetime:
    """返回当前 UTC 时间。

    健康检查结果最好用统一时区，避免 Windows 本机、Linux 服务器、
    Docker 容器之间的时区不同导致排查日志时混乱。
    """

    return datetime.now(timezone.utc)


def _elapsed_ms(started_at: float) -> float:
    """计算从 started_at 到现在经过了多少毫秒。"""

    return round((time.perf_counter() - started_at) * 1000, 2)


def _result(
    service: str,
    ok: bool,
    started_at: float,
    details: dict[str, Any] | None = None,
) -> HealthCheckResult:
    """统一组装健康检查返回对象。

    参数说明：
    - service：服务名，比如 docker；
    - ok：检查是否成功；
    - started_at：检查开始时间，用来计算耗时；
    - details：每个服务自己的细节。

    这个函数的价值：
    - 所有接口返回结构一致；
    - 不用在 check_docker/check_ollama 等函数里重复写 status、时间、耗时逻辑。
    """

    return HealthCheckResult(
        service=service,
        ok=ok,
        status="healthy" if ok else "unhealthy",
        checked_at=_now_utc(),
        response_time_ms=_elapsed_ms(started_at),
        details=details or {},
    )


async def check_docker(settings: Settings) -> HealthCheckResult:
    """Docker 健康检查的总入口。

    调用方：
    - app.main.docker_health()

    分支逻辑：
    - DOCKER_CHECK_MODE=cli：检查运行 FastAPI 这台机器上的 Docker；
    - DOCKER_CHECK_MODE=ssh：SSH 到远程服务器检查 Docker；
    - 其他值：直接返回 unhealthy，提示配置错误。

    为什么支持 ssh？
    - 你的 FastAPI 跑在 Windows `192.168.1.103`；
    - Docker/Dify/Milvus 很多服务在远程 Linux `192.168.1.102`；
    - Windows 本机可能没有 docker 命令，所以需要 SSH 到远程服务器查。
    """

    if settings.docker_check_mode == "ssh":
        return await _check_docker_via_ssh(settings)
    if settings.docker_check_mode != "cli":
        started_at = time.perf_counter()
        return _result(
            "docker",
            False,
            started_at,
            {
                "check_mode": settings.docker_check_mode,
                "error": "Unsupported DOCKER_CHECK_MODE. Use cli or ssh.",
            },
        )

    return await _check_docker_via_cli(settings)


async def _check_docker_via_cli(settings: Settings) -> HealthCheckResult:
    """通过本机 Docker CLI 检查 Docker。

    数据流转：
    1. 从 settings.docker_command 拿到命令名，默认是 docker；
    2. 用 shutil.which(...) 判断当前 PATH 里有没有 docker 命令；
    3. 执行 `docker info --format {{.ServerVersion}}`；
    4. 如果退出码是 0，说明 Docker daemon 可访问；
    5. 把 Docker 版本、退出码、错误输出封装进 HealthCheckResult.details。

    这个函数只读，不会重启、删除、清理任何 Docker 资源。
    """

    started_at = time.perf_counter()
    docker_path = shutil.which(settings.docker_command)
    command = [settings.docker_command, "info", "--format", "{{.ServerVersion}}"]

    if docker_path is None:
        return _result(
            "docker",
            False,
            started_at,
            {
                "command": " ".join(command),
                "check_mode": "cli",
                "error": "Docker CLI was not found in PATH.",
            },
        )

    try:
        # subprocess.run 是同步阻塞函数。
        # FastAPI 的路由是 async，如果直接调用阻塞函数，会占住事件循环。
        # asyncio.to_thread 会把阻塞调用丢到线程池里执行，不影响其他请求。
        completed = await asyncio.to_thread(
            subprocess.run,
            command,
            capture_output=True,
            text=True,
            timeout=settings.docker_timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return _result(
            "docker",
            False,
            started_at,
            {
                "command": " ".join(command),
                "check_mode": "cli",
                "error": f"Docker command timed out after {settings.docker_timeout_seconds} seconds.",
            },
        )

    stdout = completed.stdout.strip()
    stderr = completed.stderr.strip()
    ok = completed.returncode == 0
    details: dict[str, Any] = {
        "check_mode": "cli",
        "command": " ".join(command),
        "exit_code": completed.returncode,
    }
    if stdout:
        details["server_version"] = stdout
    if stderr:
        details["stderr"] = stderr

    return _result("docker", ok, started_at, details)


def _run_docker_info_over_ssh(settings: Settings) -> tuple[int, str, str]:
    """通过 SSH 登录远程服务器并执行 Docker 只读命令。

    调用方：
    - _check_docker_via_ssh()

    为什么这个函数不是 async？
    - paramiko 是同步库；
    - 它连接 SSH、执行命令时会阻塞线程；
    - 外层 _check_docker_via_ssh 会用 asyncio.to_thread 调它。

    返回值：
    - exit_code：远程命令退出码；
    - stdout：远程命令标准输出；
    - stderr：远程命令错误输出。
    """

    if not settings.docker_ssh_password and not settings.docker_ssh_key_path:
        raise ValueError("Set DOCKER_SSH_PASSWORD or DOCKER_SSH_KEY_PATH for ssh mode.")

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    connect_kwargs: dict[str, Any] = {
        "hostname": settings.docker_ssh_host,
        "port": settings.docker_ssh_port,
        "username": settings.docker_ssh_username,
        "timeout": settings.docker_timeout_seconds,
        "banner_timeout": settings.docker_timeout_seconds,
        "auth_timeout": settings.docker_timeout_seconds,
    }
    if settings.docker_ssh_key_path:
        # 生产环境更推荐 SSH 私钥方式，不需要在环境变量里放密码。
        connect_kwargs["key_filename"] = settings.docker_ssh_key_path
    else:
        # 学习和内网练习时可以用密码方式，但不要提交到 Git。
        connect_kwargs["password"] = settings.docker_ssh_password

    try:
        client.connect(**connect_kwargs)
        # 默认命令是：
        # docker info --format '{{.ServerVersion}}'
        # 它只读取 Docker server version，不修改任何容器、镜像、volume。
        _stdin, stdout, stderr = client.exec_command(
            settings.docker_ssh_command,
            timeout=settings.docker_timeout_seconds,
        )
        exit_code = stdout.channel.recv_exit_status()
        stdout_text = stdout.read().decode("utf-8", errors="replace").strip()
        stderr_text = stderr.read().decode("utf-8", errors="replace").strip()
        return exit_code, stdout_text, stderr_text
    finally:
        client.close()


async def _check_docker_via_ssh(settings: Settings) -> HealthCheckResult:
    """通过 SSH 模式检查远程 Docker。

    数据流转：
    1. app.main.docker_health() -> check_docker()；
    2. check_docker() 根据 DOCKER_CHECK_MODE=ssh 调用当前函数；
    3. 当前函数用 asyncio.to_thread 调用 _run_docker_info_over_ssh()；
    4. _run_docker_info_over_ssh() 通过 paramiko SSH 登录远程服务器；
    5. 远程执行 docker info；
    6. 当前函数把 exit_code/stdout/stderr 包装成 HealthCheckResult。
    """

    started_at = time.perf_counter()

    try:
        exit_code, stdout, stderr = await asyncio.to_thread(_run_docker_info_over_ssh, settings)
    except (OSError, ValueError, paramiko.SSHException) as exc:
        return _result(
            "docker",
            False,
            started_at,
            {
                "check_mode": "ssh",
                "host": settings.docker_ssh_host,
                "port": settings.docker_ssh_port,
                "username": settings.docker_ssh_username,
                "command": settings.docker_ssh_command,
                "error": str(exc),
            },
        )

    details: dict[str, Any] = {
        "check_mode": "ssh",
        "host": settings.docker_ssh_host,
        "port": settings.docker_ssh_port,
        "username": settings.docker_ssh_username,
        "command": settings.docker_ssh_command,
        "exit_code": exit_code,
    }
    if stdout:
        details["server_version"] = stdout
    if stderr:
        details["stderr"] = stderr

    return _result("docker", exit_code == 0, started_at, details)


async def check_ollama(settings: Settings) -> HealthCheckResult:
    """检查 Ollama 服务。

    调用方：
    - app.main.ollama_health()

    请求目标：
    - `{OLLAMA_BASE_URL}/api/tags`
    - 这是 Ollama 官方接口，用来列出当前服务上已有模型。

    数据流转：
    1. 从 settings.ollama_base_url 读取 Ollama 地址；
    2. 用 httpx.AsyncClient 发起 HTTP GET；
    3. 如果请求失败，返回 unhealthy；
    4. 如果请求成功，解析 JSON 里的 models；
    5. 返回模型数量和前 20 个模型名。
    """

    started_at = time.perf_counter()
    url = f"{settings.ollama_base_url}/api/tags"

    try:
        # httpx.AsyncClient 是异步 HTTP 客户端，适合在 FastAPI async 路由里使用。
        # 内网 IP 不应该走系统代理；httpx 默认会读取代理环境，可能导致内网超时。
        async with httpx.AsyncClient(timeout=settings.http_timeout_seconds, trust_env=False) as client:
            response = await client.get(url)
        payload = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
    except (httpx.HTTPError, ValueError) as exc:
        return _result(
            "ollama",
            False,
            started_at,
            {
                "url": url,
                "error": str(exc),
            },
        )

    models = payload.get("models", []) if isinstance(payload, dict) else []
    model_names = [model.get("name") for model in models if isinstance(model, dict)]
    return _result(
        "ollama",
        response.is_success,
        started_at,
        {
            "url": url,
            "status_code": response.status_code,
            "model_count": len(model_names),
            "models": model_names[:20],
        },
    )


async def check_dify(settings: Settings) -> HealthCheckResult:
    """检查 Dify Web 服务。

    调用方：
    - app.main.dify_health()

    默认策略：
    1. 先请求 `DIFY_BASE_URL + DIFY_HEALTH_PATH`，默认是 http://192.168.1.102/health；
    2. 如果这个路径返回 404，说明 Dify 可能没有暴露 /health；
    3. 再退回请求 Dify 首页 `DIFY_BASE_URL`；
    4. 只要最终 HTTP 响应是成功状态，就认为 Dify Web 基本可访问。

    注意：
    - 这里只检查 Web 入口是否可访问；
    - 不检查 Dify 内部 worker、数据库、Redis 的完整状态。
    """

    started_at = time.perf_counter()

    try:
        async with httpx.AsyncClient(
            timeout=settings.http_timeout_seconds,
            follow_redirects=True,
            trust_env=False,
        ) as client:
            response = await client.get(settings.dify_health_url)
            checked_url = settings.dify_health_url

            if response.status_code == 404 and settings.dify_health_path != "/":
                response = await client.get(settings.dify_base_url)
                checked_url = settings.dify_base_url
    except httpx.HTTPError as exc:
        return _result(
            "dify",
            False,
            started_at,
            {
                "url": settings.dify_health_url,
                "error": str(exc),
            },
        )

    return _result(
        "dify",
        response.is_success or response.is_redirect,
        started_at,
        {
            "url": checked_url,
            "status_code": response.status_code,
            "final_url": str(response.url),
        },
    )


def _can_open_tcp_connection(host: str, port: int, timeout_seconds: float) -> None:
    """尝试打开一个 TCP 连接。

    调用方：
    - check_milvus()

    这里不使用 Milvus SDK，是为了保持依赖简单：
    - 当前阶段只需要知道端口是否通；
    - 还不需要查询 collection、索引、向量数据。
    """

    with socket.create_connection((host, port), timeout=timeout_seconds):
        return None


async def check_milvus(settings: Settings) -> HealthCheckResult:
    """检查 Milvus 端口连通性。

    调用方：
    - app.main.milvus_health()

    数据流转：
    1. 从 settings 读取 MILVUS_HOST 和 MILVUS_PORT；
    2. 调用 _can_open_tcp_connection() 尝试 TCP 连接；
    3. 能连接上就返回 healthy；
    4. 连接超时、拒绝、网络不可达就返回 unhealthy。

    这个检查是只读的，不会创建 collection，也不会写入向量数据。
    """

    started_at = time.perf_counter()

    try:
        await asyncio.to_thread(
            _can_open_tcp_connection,
            settings.milvus_host,
            settings.milvus_port,
            settings.socket_timeout_seconds,
        )
    except OSError as exc:
        return _result(
            "milvus",
            False,
            started_at,
            {
                "host": settings.milvus_host,
                "port": settings.milvus_port,
                "check_type": "tcp_connect",
                "error": str(exc),
            },
        )

    return _result(
        "milvus",
        True,
        started_at,
        {
            "host": settings.milvus_host,
            "port": settings.milvus_port,
            "check_type": "tcp_connect",
        },
    )
