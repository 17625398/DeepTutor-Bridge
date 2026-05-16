#!/usr/bin/env python
"""Build and launch LinkMind for DeepTutor integration."""

from __future__ import annotations

from pathlib import Path
import os
import shutil
import subprocess
import sys
from typing import NoReturn

ROOT_DIR = Path(__file__).resolve().parent.parent
JAR_CANDIDATES = [
    ROOT_DIR / "LinkMind.jar",
    ROOT_DIR / "lagi-web" / "target" / "LinkMind.jar",
]
DEFAULT_HOST = os.getenv("LINKMIND_HOST", "127.0.0.1").strip() or "127.0.0.1"
DEFAULT_PORT = os.getenv("LINKMIND_PORT", "8080").strip() or "8080"


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
    java = _which("java")
    jar_path = _build_if_needed()
    command = [
        java,
        "-jar",
        str(jar_path),
        f"--host={DEFAULT_HOST}",
        f"--port={DEFAULT_PORT}",
        "--runtime-choice=server",
        "--enable-sync=false",
    ]
    print(f"[linkmind] Starting LinkMind on http://{DEFAULT_HOST}:{DEFAULT_PORT} ...", flush=True)
    process = subprocess.Popen(command, cwd=str(ROOT_DIR))
    try:
        raise SystemExit(process.wait())
    except KeyboardInterrupt:
        process.terminate()
        raise


if __name__ == "__main__":
    main()
