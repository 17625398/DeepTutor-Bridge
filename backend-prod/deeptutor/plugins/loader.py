from __future__ import annotations

from dataclasses import dataclass
import importlib
import importlib.util
import os
from pathlib import Path
import sys
from typing import Any, Iterable

import yaml

from deeptutor.core.capability_protocol import BaseCapability
from deeptutor.core.tool_protocol import BaseTool
from deeptutor.services.config import PROJECT_ROOT
from deeptutor.services.path_service import get_path_service


@dataclass(frozen=True)
class PluginManifest:
    name: str
    type: str
    description: str
    stages: list[str]
    version: str
    author: str
    entry: str
    root_dir: Path
    source: str
    raw: dict[str, Any]


@dataclass(frozen=True)
class IntegrationDevProcess:
    name: str
    cwd: Path
    command: list[str]
    env: dict[str, str]
    health_url: str | None


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base or {})
    for key, value in (override or {}).items():
        if value is None:
            merged.pop(key, None)
            continue
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _candidate_custom_roots() -> list[Path]:
    roots: list[Path] = []
    env_root = os.getenv("DEEPTUTOR_CUSTOM_ROOT", "").strip()
    if env_root:
        roots.append(Path(env_root))

    try:
        roots.append(get_path_service().get_user_root())
    except Exception:
        roots.append(PROJECT_ROOT / "data" / "user")

    normalized: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        try:
            resolved = root.resolve()
        except Exception:
            continue
        key = str(resolved).lower()
        if key in seen:
            continue
        seen.add(key)
        normalized.append(resolved)
    return normalized


def _integration_candidate_dirs(base: Path) -> Iterable[Path]:
    if not base.exists():
        return []

    candidates: list[Path] = []
    for item in base.iterdir():
        if not item.is_dir():
            continue
        candidates.append(item)
        try:
            for child in item.iterdir():
                if child.is_dir():
                    candidates.append(child)
        except OSError:
            continue
    return candidates


def _load_yaml(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _manifest_from_dir(root_dir: Path, *, source: str) -> PluginManifest | None:
    manifest_path = root_dir / "manifest.yaml"
    if not manifest_path.exists():
        return None

    raw = _load_yaml(manifest_path)
    name = str(raw.get("name") or root_dir.name).strip()
    if not name:
        return None
    return PluginManifest(
        name=name,
        type=str(raw.get("type") or "integration").strip() or "integration",
        description=str(raw.get("description") or "").strip(),
        stages=list(raw.get("stages") or []),
        version=str(raw.get("version") or "").strip(),
        author=str(raw.get("author") or "").strip(),
        entry=str(raw.get("entry") or raw.get("backend", {}).get("entry") or "").strip(),
        root_dir=root_dir,
        source=source,
        raw=raw,
    )


def discover_plugins() -> list[PluginManifest]:
    manifests: list[PluginManifest] = []
    seen: set[str] = set()

    for custom_root in _candidate_custom_roots():
        integrations_dir = custom_root / "integrations"
        extensions_dir = custom_root / "extensions"

        for candidate in _integration_candidate_dirs(integrations_dir):
            manifest = _manifest_from_dir(candidate, source=str(integrations_dir))
            if not manifest:
                continue
            key = f"{manifest.name}:{manifest.source}"
            if key in seen:
                continue
            seen.add(key)
            manifests.append(manifest)

        for candidate in _integration_candidate_dirs(extensions_dir):
            manifest = _manifest_from_dir(candidate, source=str(extensions_dir))
            if not manifest:
                continue
            key = f"{manifest.name}:{manifest.source}"
            if key in seen:
                continue
            seen.add(key)
            manifests.append(manifest)

    return manifests


def discover_integrations() -> list[PluginManifest]:
    return [m for m in discover_plugins() if m.type in {"integration", "app", "service"}]


def _load_from_module(entry: str) -> Any:
    module_path, attr = entry.rsplit(":", 1)
    module = importlib.import_module(module_path)
    return getattr(module, attr)


def _module_name_for_file(path: Path, *, prefix: str) -> str:
    stem = path.stem.replace("-", "_")
    return f"{prefix}_{stem}_{abs(hash(str(path)))}"


def _load_from_file(path: Path, attr: str, *, prefix: str) -> Any:
    module_name = _module_name_for_file(path, prefix=prefix)
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to import module from file: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return getattr(module, attr)


def _load_entry_object(entry: str, root_dir: Path) -> Any:
    if not entry:
        raise ValueError("Missing manifest.entry")

    if ".py:" in entry or entry.endswith(".py"):
        file_part, attr = entry.split(":", 1) if ":" in entry else (entry, "")
        if not attr:
            raise ValueError("File entry must include ':<ClassName>' suffix")
        file_path = (root_dir / file_part).resolve()
        return _load_from_file(file_path, attr, prefix=f"dt_plugin_{root_dir.name}")

    return _load_from_module(entry)


def _with_sys_path(path: Path):
    class _PathContext:
        def __init__(self, p: Path):
            self.p = str(p)
            self.added = False

        def __enter__(self):
            if self.p not in sys.path:
                sys.path.insert(0, self.p)
                self.added = True

        def __exit__(self, exc_type, exc, tb):
            if self.added and self.p in sys.path:
                sys.path.remove(self.p)

    return _PathContext(path)


def load_plugin_capability(manifest: PluginManifest) -> BaseCapability | None:
    if not manifest.entry:
        return None
    backend_dir = manifest.root_dir / "backend"
    with _with_sys_path(backend_dir if backend_dir.exists() else manifest.root_dir):
        obj = _load_entry_object(manifest.entry, manifest.root_dir)
    if isinstance(obj, type) and issubclass(obj, BaseCapability):
        return obj()
    raise TypeError(f"Plugin entry is not a BaseCapability: {manifest.name}")


def load_plugin_tool(manifest: PluginManifest) -> BaseTool | None:
    if not manifest.entry:
        return None
    backend_dir = manifest.root_dir / "backend"
    with _with_sys_path(backend_dir if backend_dir.exists() else manifest.root_dir):
        obj = _load_entry_object(manifest.entry, manifest.root_dir)
    if isinstance(obj, type) and issubclass(obj, BaseTool):
        return obj()
    raise TypeError(f"Plugin entry is not a BaseTool: {manifest.name}")


def resolve_ui(manifest: PluginManifest, overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    base = dict((manifest.raw.get("ui") or {}) if isinstance(manifest.raw, dict) else {})
    if overrides:
        return _deep_merge(base, overrides)
    return base


def integration_dev_processes(manifest: PluginManifest) -> list[IntegrationDevProcess]:
    dev = manifest.raw.get("dev") if isinstance(manifest.raw, dict) else None
    if not isinstance(dev, dict):
        return []
    processes = dev.get("processes")
    if not isinstance(processes, list):
        return []

    specs: list[IntegrationDevProcess] = []
    for item in processes:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or manifest.name).strip()
        command = item.get("command")
        if not isinstance(command, list) or not all(isinstance(x, str) and x.strip() for x in command):
            continue
        cwd_raw = str(item.get("cwd") or ".")
        cwd = (manifest.root_dir / cwd_raw).resolve()
        env_raw = item.get("env") or {}
        env: dict[str, str] = {}
        if isinstance(env_raw, dict):
            for k, v in env_raw.items():
                if k is None:
                    continue
                env[str(k)] = str(v) if v is not None else ""
        health_url = item.get("health_url")
        health_url_str = str(health_url).strip() if health_url is not None else None
        specs.append(
            IntegrationDevProcess(
                name=name,
                cwd=cwd,
                command=[str(x) for x in command],
                env=env,
                health_url=health_url_str or None,
            )
        )
    return specs


def integration_auto_start(manifest: PluginManifest) -> bool:
    dev = manifest.raw.get("dev") if isinstance(manifest.raw, dict) else None
    if not isinstance(dev, dict):
        return False
    return bool(dev.get("auto_start", False))
