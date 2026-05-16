#!/usr/bin/env python
"""DeepTutor production launcher for source / VM deployments."""

from __future__ import annotations

import argparse
import atexit
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from start_web import (  # noqa: E402
    BACKEND_READY_TIMEOUT,
    FRONTEND_READY_TIMEOUT,
    PYTHON_EXE,
    ManagedProcess,
    _ensure_ports_available,
    _ensure_npm_deps,
    _ensure_pnpm_deps,
    _ensure_python_server_deps,
    _install_signal_handlers,
    _probe_http,
    _probe_tcp_from_url,
    _remove_state,
    _resolve_integration_command,
    _spawn,
    _terminate,
    _wait_for_http,
    _write_state,
    banner,
    bold,
    discover_integrations,
    integration_auto_start,
    integration_dev_processes,
    load_launch_settings,
    log_error,
    log_info,
    log_success,
    log_warn,
)

PROD_STATE_PATH = PROJECT_ROOT / "data" / "user" / "settings" / "start_web_prod_state.json"
WEB_ROOT = PROJECT_ROOT / "web"

MESSAGES = {
    "en": {
        "backend": "Backend",
        "frontend": "Frontend",
        "config_source": "Config source: {source}",
        "build_mode": "Frontend mode: {mode}",
        "npm_missing": "npm not found. Install Node.js and npm first.",
        "node_missing": "node not found. Install Node.js and add it to PATH.",
        "pnpm_missing": "pnpm not found. Install pnpm (corepack) or add it to PATH.",
        "cargo_missing": "cargo not found. Install Rust (rustup) and add it to PATH.",
        "installing_frontend_deps": "Frontend dependencies missing; installing them first ...",
        "building_frontend": "Building frontend production assets ...",
        "build_failed": "Frontend build failed with exit code {code}.",
        "build_complete": "Frontend production build is ready.",
        "starting_backend": "Starting backend in production mode ...",
        "starting_frontend": "Starting frontend in production mode ...",
        "starting_integrations": "Starting integrations ...",
        "starting_integration": "Starting integration: {name}",
        "integration_failed": "Integration failed to start: {name}",
        "using_standalone": "Using Next.js standalone server.",
        "using_next_start": "Using `next start` server.",
        "missing_build": "Frontend build output is missing. Run without `--skip-build` first.",
        "open_url": "Open {url} in your browser.",
        "shutdown_signal": "Received {signal}; shutting down ...",
        "shutdown": "Shutting down ...",
    },
    "zh": {
        "backend": "后端",
        "frontend": "前端",
        "config_source": "配置来源：{source}",
        "build_mode": "前端模式：{mode}",
        "npm_missing": "未找到 npm。请先安装 Node.js 与 npm。",
        "node_missing": "未找到 node。请先安装 Node.js 并加入 PATH。",
        "pnpm_missing": "未找到 pnpm。请安装 pnpm（建议用 corepack）或将其加入 PATH。",
        "cargo_missing": "未找到 cargo。请安装 Rust（rustup）并将其加入 PATH。",
        "installing_frontend_deps": "检测到前端依赖缺失，正在先安装依赖 ...",
        "building_frontend": "正在构建前端生产资源 ...",
        "build_failed": "前端构建失败，退出码 {code}。",
        "build_complete": "前端生产构建已完成。",
        "starting_backend": "正在以生产模式启动后端 ...",
        "starting_frontend": "正在以生产模式启动前端 ...",
        "starting_integrations": "正在启动集成 ...",
        "starting_integration": "正在启动集成：{name}",
        "integration_failed": "集成启动失败：{name}",
        "using_standalone": "前端将使用 Next.js standalone 服务。",
        "using_next_start": "前端将使用 `next start` 服务。",
        "missing_build": "未找到前端构建产物。请先不要使用 `--skip-build`，完成一次构建。",
        "open_url": "请在浏览器中打开 {url}。",
        "shutdown_signal": "收到 {signal}，正在关闭 ...",
        "shutdown": "正在关闭 ...",
    },
}


def _t(language: str, key: str, **kwargs: Any) -> str:
    catalog = MESSAGES.get(language, MESSAGES["en"])
    template = catalog.get(key, MESSAGES["en"][key])
    return template.format(**kwargs)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Start DeepTutor backend and frontend in non-Docker production mode.",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Bind host for both backend and frontend servers (default: 0.0.0.0).",
    )
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="Skip `npm run build` and reuse the existing frontend build output.",
    )
    parser.add_argument(
        "--frontend-mode",
        choices=("auto", "standalone", "next-start"),
        default="auto",
        help="How to run the frontend after build (default: auto).",
    )
    return parser.parse_args()


def _read_root_env(env_path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not env_path.exists():
        return values
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("\"'")
    return values


def _truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _ensure_frontend_deps(*, npm: str, env: dict[str, str], language: str) -> None:
    package_json = WEB_ROOT / "package.json"
    node_modules = WEB_ROOT / "node_modules"
    if not package_json.exists() or node_modules.exists():
        return
    log_info(_t(language, "installing_frontend_deps"))
    lock_path = WEB_ROOT / "package-lock.json"
    cmd = [npm, "ci"] if lock_path.exists() else [npm, "install"]
    cmd += ["--no-fund", "--no-audit", "--legacy-peer-deps"]
    subprocess.run(cmd, cwd=str(WEB_ROOT), env=env, check=False)


def _standalone_server_path() -> Path:
    return WEB_ROOT / ".next" / "standalone" / "server.js"


def _frontend_build_exists() -> bool:
    return (WEB_ROOT / ".next" / "BUILD_ID").exists()


def _build_frontend(*, npm: str, env: dict[str, str], language: str) -> None:
    log_info(_t(language, "building_frontend"))
    result = subprocess.run(
        [npm, "run", "build"],
        cwd=str(WEB_ROOT),
        env=env,
        check=False,
    )
    if result.returncode != 0:
        log_error(_t(language, "build_failed", code=result.returncode))
        raise SystemExit(result.returncode or 1)
    log_success(_t(language, "build_complete"))


def _choose_frontend_command(
    *,
    mode: str,
    node: str,
    npm: str,
    host: str,
    frontend_port: int,
    language: str,
) -> list[str]:
    standalone_server = _standalone_server_path()
    use_standalone = mode == "standalone" or (
        mode == "auto" and standalone_server.exists()
    )
    if use_standalone:
        log_info(_t(language, "using_standalone"))
        return [node, str(standalone_server)]
    log_info(_t(language, "using_next_start"))
    return [npm, "run", "start", "--", "--hostname", host, "--port", str(frontend_port)]


def main() -> None:
    args = _parse_args()
    settings = load_launch_settings(PROJECT_ROOT)
    language = settings.language
    backend_port = settings.backend_port
    frontend_port = settings.frontend_port
    env_values = _read_root_env(settings.env_path)

    npm = shutil.which("npm")
    if not npm:
        log_error(_t(language, "npm_missing"))
        raise SystemExit(1)
    node = shutil.which("node")
    if not node:
        log_error(_t(language, "node_missing"))
        raise SystemExit(1)
    pnpm = shutil.which("pnpm")
    cargo = shutil.which("cargo")

    auth_enabled = _truthy(
        env_values.get("NEXT_PUBLIC_AUTH_ENABLED") or env_values.get("AUTH_ENABLED")
    )
    public_api_base = (
        env_values.get("NEXT_PUBLIC_API_BASE_EXTERNAL")
        or env_values.get("NEXT_PUBLIC_API_BASE")
        or f"http://127.0.0.1:{backend_port}"
    )

    backend_env = os.environ.copy()
    backend_env["BACKEND_PORT"] = str(backend_port)
    backend_env["FRONTEND_PORT"] = str(frontend_port)
    backend_env["PYTHONUNBUFFERED"] = "1"
    backend_env["PYTHONIOENCODING"] = "utf-8:replace"

    frontend_env = os.environ.copy()
    frontend_env["BACKEND_PORT"] = str(backend_port)
    frontend_env["FRONTEND_PORT"] = str(frontend_port)
    frontend_env["HOSTNAME"] = args.host
    frontend_env["PORT"] = str(frontend_port)
    frontend_env["NEXT_PUBLIC_API_BASE"] = public_api_base
    frontend_env["NEXT_PUBLIC_AUTH_ENABLED"] = "true" if auth_enabled else "false"
    frontend_env["AUTH_ENABLED"] = "true" if auth_enabled else "false"
    frontend_env["PYTHONIOENCODING"] = "utf-8:replace"
    if env_values.get("NEXT_PUBLIC_API_BASE_EXTERNAL"):
        frontend_env["NEXT_PUBLIC_API_BASE_EXTERNAL"] = env_values["NEXT_PUBLIC_API_BASE_EXTERNAL"]

    banner(
        "DeepTutor Production",
        [
            f"{_t(language, 'backend')}   http://{args.host}:{backend_port}",
            f"{_t(language, 'frontend')}  http://{args.host}:{frontend_port}",
        ],
    )
    log_info(_t(language, "config_source", source=settings.source))
    log_info(_t(language, "build_mode", mode=args.frontend_mode))

    _ensure_ports_available(
        backend_port,
        frontend_port,
        language,
        state_path=PROD_STATE_PATH,
    )

    _ensure_python_server_deps(python_exe=PYTHON_EXE, language=language)
    _ensure_frontend_deps(npm=npm, env=frontend_env, language=language)

    if not args.skip_build:
        _build_frontend(npm=npm, env=frontend_env, language=language)
    elif not _frontend_build_exists():
        log_error(_t(language, "missing_build"))
        raise SystemExit(1)

    frontend_cmd = _choose_frontend_command(
        mode=args.frontend_mode,
        node=node,
        npm=npm,
        host=args.host,
        frontend_port=frontend_port,
        language=language,
    )
    if args.frontend_mode == "standalone" and not _standalone_server_path().exists():
        log_error(_t(language, "missing_build"))
        raise SystemExit(1)

    backend_cmd = [
        PYTHON_EXE,
        "-m",
        "uvicorn",
        "deeptutor.api.main:app",
        "--host",
        args.host,
        "--port",
        str(backend_port),
        "--log-level",
        "info",
        "--no-access-log",
    ]

    processes: list[ManagedProcess] = []
    backend: ManagedProcess | None = None
    frontend: ManagedProcess | None = None
    integrations: list[ManagedProcess] = []
    shutdown_requested = False
    cleanup_started = False
    exit_code = 0

    def request_shutdown(signal_name: str | None = None) -> None:
        nonlocal shutdown_requested
        if shutdown_requested:
            return
        shutdown_requested = True
        if signal_name:
            print()
            log_info(_t(language, "shutdown_signal", signal=signal_name))

    def cleanup() -> None:
        nonlocal cleanup_started
        if cleanup_started:
            return
        cleanup_started = True
        for proc in reversed(integrations):
            _terminate(proc, language)
        _terminate(frontend, language)
        _terminate(backend, language)
        _remove_state(PROD_STATE_PATH)

    _install_signal_handlers(request_shutdown)
    atexit.register(cleanup)

    try:
        log_info(_t(language, "starting_backend"))
        backend = _spawn(backend_cmd, cwd=PROJECT_ROOT, env=backend_env, name="backend-prod")
        processes.append(backend)
        _write_state(
            processes,
            backend_port=backend_port,
            frontend_port=frontend_port,
            path=PROD_STATE_PATH,
        )
        _wait_for_http(
            name=_t(language, "backend"),
            url=f"http://127.0.0.1:{backend_port}/",
            process=backend,
            timeout=BACKEND_READY_TIMEOUT,
            language=language,
            waiting_key="waiting_backend",
            ready_key="ready_backend",
            should_stop=lambda: shutdown_requested,
        )

        log_info(_t(language, "starting_frontend"))
        frontend = _spawn(frontend_cmd, cwd=WEB_ROOT, env=frontend_env, name="frontend-prod")
        processes.append(frontend)
        _write_state(
            processes,
            backend_port=backend_port,
            frontend_port=frontend_port,
            path=PROD_STATE_PATH,
        )
        _wait_for_http(
            name=_t(language, "frontend"),
            url=f"http://127.0.0.1:{frontend_port}/",
            process=frontend,
            timeout=FRONTEND_READY_TIMEOUT,
            language=language,
            waiting_key="waiting_frontend",
            ready_key="ready_frontend",
            should_stop=lambda: shutdown_requested,
        )

        log_success(_t(language, "open_url", url=bold(f"http://localhost:{frontend_port}")))
        print()

        log_info(_t(language, "starting_integrations"))
        for manifest in discover_integrations():
            if not integration_auto_start(manifest):
                continue
            for spec in integration_dev_processes(manifest):
                log_info(_t(language, "starting_integration", name=spec.name))
                try:
                    if spec.health_url:
                        if _probe_http(spec.health_url) or _probe_tcp_from_url(spec.health_url):
                            continue
                    env = os.environ.copy()
                    env.update(spec.env)
                    if spec.command and spec.command[0] == "pnpm" and not pnpm:
                        log_error(_t(language, "pnpm_missing"))
                        continue
                    if spec.command and spec.command[0] == "cargo" and not cargo:
                        log_error(_t(language, "cargo_missing"))
                        continue
                    cmd = _resolve_integration_command(spec.command, npm=npm, pnpm=pnpm, cargo=cargo)
                    if cmd and Path(cmd[0]).name.lower().startswith("npm"):
                        _ensure_npm_deps(spec.cwd, npm=npm, env=env, language=language)
                    if cmd and Path(cmd[0]).name.lower().startswith("pnpm"):
                        if not pnpm:
                            log_error(_t(language, "pnpm_missing"))
                            continue
                        _ensure_pnpm_deps(spec.cwd, pnpm=pnpm, env=env, language=language)
                    proc = _spawn(cmd, cwd=spec.cwd, env=env, name=f"integration:{spec.name}")
                    integrations.append(proc)
                    processes.append(proc)
                    _write_state(
                        processes,
                        backend_port=backend_port,
                        frontend_port=frontend_port,
                        path=PROD_STATE_PATH,
                    )
                except Exception:
                    log_warn(_t(language, "integration_failed", name=spec.name))

        while not shutdown_requested:
            if backend.process.poll() is not None:
                exit_code = backend.process.returncode or 1
                break
            if frontend.process.poll() is not None:
                exit_code = frontend.process.returncode or 1
                break
            for proc in integrations:
                if proc.process.poll() is not None:
                    exit_code = proc.process.returncode or 1
                    break
            if exit_code:
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print()
        log_info(_t(language, "shutdown"))
    finally:
        cleanup()

    if exit_code:
        raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
