#!/usr/bin/env python
"""Build and launch LinkMind for DeepTutor integration."""

from __future__ import annotations

from pathlib import Path
import os
import shutil
import subprocess
import sys
from typing import NoReturn
from urllib.error import URLError
from urllib.request import urlopen

ROOT_DIR = Path(__file__).resolve().parent.parent
JAR_CANDIDATES = [
    ROOT_DIR / "LinkMind.jar",
    ROOT_DIR / "lagi-web" / "target" / "LinkMind.jar",
]
CONFIG_FILE = ROOT_DIR / "config" / "lagi.yml"
CONFIG_FALLBACK_CANDIDATES = [
    ROOT_DIR / "config" / "lagi - 副本.yml",
    ROOT_DIR / "lagi-web" / "src" / "main" / "resources" / "lagi.yml",
]
HEALTH_URL = os.getenv("LINKMIND_HEALTH_URL", "http://127.0.0.1:8080").strip() or "http://127.0.0.1:8080"
ENABLE_SYNC = os.getenv("LINKMIND_ENABLE_SYNC", "true").strip().lower() not in {"0", "false", "no", "off"}


def _die(message: str, code: int = 1) -> NoReturn:
    print(f"[linkmind] {message}", file=sys.stderr, flush=True)
    raise SystemExit(code)


def _which(binary: str) -> str:
    resolved = shutil.which(binary)
    if not resolved:
        _die(f"Missing required dependency: {binary}")
    return resolved


def _resolve_jar_path() -> Path | None:
    for jar_path in JAR_CANDIDATES:
        if jar_path.exists():
            return jar_path
    return None


def _probe_healthy(url: str) -> bool:
    try:
        with urlopen(url, timeout=3) as response:
            return 200 <= response.status < 500
    except (OSError, URLError):
        return False


def _looks_like_unsupported_config(config_text: str) -> bool:
    lowered = config_text.lower()
    return "runtime:" in lowered or "\nserver:" in lowered


def _resolve_config_path() -> Path:
    if CONFIG_FILE.exists():
        config_text = CONFIG_FILE.read_text(encoding="utf-8", errors="ignore")
        if not _looks_like_unsupported_config(config_text):
            return CONFIG_FILE
    for candidate in CONFIG_FALLBACK_CANDIDATES:
        if candidate.exists():
            return candidate
    _die(
        "No compatible lagi.yml found. "
        "Expected either config/lagi.yml or a fallback template under config/ or lagi-web resources."
    )


def _ensure_mate_mode(config_path: Path) -> None:
    config_text = config_path.read_text(encoding="utf-8", errors="ignore")
    if "rule: server" in config_text.lower():
        _die(
            f"LinkMind must run in mate mode, but {config_path} config sets skills.rule: server."
        )


def _build_if_needed() -> Path:
    jar_path = _resolve_jar_path()
    if jar_path is not None:
        return jar_path
    mvn = shutil.which("mvn")
    if not mvn:
        locations = ", ".join(str(path) for path in JAR_CANDIDATES)
        _die(
            "LinkMind.jar not found. Either place a prebuilt JAR in one of: "
            f"{locations} ; or install Maven (`mvn`) so DeepTutor can build it automatically."
        )
    print("[linkmind] LinkMind.jar not found, building from source ...", flush=True)
    result = subprocess.run(
        [mvn, "-B", "clean", "package", "-pl", "lagi-web", "-am", "-DskipTests", "-U"],
        cwd=str(ROOT_DIR),
        check=False,
    )
    if result.returncode != 0:
        _die(f"Maven build failed with exit code {result.returncode}.")
    jar_path = _resolve_jar_path()
    if jar_path is None:
        _die("Build completed but no LinkMind.jar was created.")
    return jar_path


def main() -> None:
    if _probe_healthy(HEALTH_URL):
        print(f"[linkmind] LinkMind is already reachable at {HEALTH_URL}", flush=True)
        return
    java = _which("java")
    jar_path = _build_if_needed()
    config_path = _resolve_config_path()
    _ensure_mate_mode(config_path)
    command = [
        java,
        f"-Dlinkmind.config={config_path}",
        "-jar",
        str(jar_path),
        f"--enable-sync={'true' if ENABLE_SYNC else 'false'}",
    ]
    print(
        "[linkmind] Starting LinkMind in mate mode with compatible config: "
        f"{config_path}",
        flush=True,
    )
    process = subprocess.Popen(command, cwd=str(ROOT_DIR))
    try:
        raise SystemExit(process.wait())
    except KeyboardInterrupt:
        process.terminate()
        raise


if __name__ == "__main__":
    main()
