from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from deeptutor.multi_user.context import get_current_user
from deeptutor.utils.config_manager import ConfigManager


router = APIRouter()


def _require_admin() -> None:
    if not get_current_user().is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Integrations are managed by an administrator.",
        )


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


def _ui_overrides(config: dict[str, Any], integration_name: str) -> dict[str, Any] | None:
    ui_overrides = config.get("ui_overrides") or {}
    integrations = ui_overrides.get("integrations") or {}
    entry = integrations.get(integration_name)
    if entry is None:
        return None
    if isinstance(entry, dict):
        ui = entry.get("ui")
        return ui if isinstance(ui, dict) else None
    return None


def _integration_payload(manifest: Any, *, overrides: dict[str, Any] | None) -> dict[str, Any]:
    from deeptutor.plugins.loader import resolve_ui

    ui = resolve_ui(manifest, overrides=overrides)
    nav = ui.get("nav") if isinstance(ui, dict) else None
    order = 100
    visible = True
    group = "workspace"
    if isinstance(nav, dict):
        try:
            order = int(nav.get("order", order))
        except Exception:
            order = 100
        visible = bool(nav.get("visible", True))
        group = str(nav.get("group") or group)

    return {
        "name": manifest.name,
        "type": manifest.type,
        "description": manifest.description,
        "version": manifest.version,
        "author": manifest.author,
        "ui": ui,
        "nav": {"group": group, "order": order, "visible": visible},
    }


def _resolve_integration_name(name: str, manifests: list[Any]) -> Any | None:
    raw = (name or "").strip()
    if not raw:
        return None
    wanted = raw.lower()

    for manifest in manifests:
        if str(getattr(manifest, "name", "")).lower() == wanted:
            return manifest

    def _norm(value: str) -> str:
        return (
            (value or "")
            .strip()
            .lower()
            .replace("_", "-")
        )

    wanted_norm = _norm(raw)
    for manifest in manifests:
        if _norm(str(getattr(manifest, "name", ""))) == wanted_norm:
            return manifest

    prefix_matches = [
        m
        for m in manifests
        if _norm(str(getattr(m, "name", ""))).startswith(wanted_norm)
    ]
    if len(prefix_matches) == 1:
        return prefix_matches[0]
    return None



@router.get("/integrations")
async def list_integrations():
    from deeptutor.plugins.loader import discover_integrations

    cfg = ConfigManager().load_config()
    items: list[dict[str, Any]] = []
    for manifest in discover_integrations():
        overrides = _ui_overrides(cfg, manifest.name)
        payload = _integration_payload(manifest, overrides=overrides)
        if payload["nav"]["visible"]:
            items.append(payload)

    items.sort(key=lambda item: (item["nav"]["group"], item["nav"]["order"], item["name"]))
    return {"integrations": items}


@router.get("/integrations/{name}")
async def get_integration(name: str):
    from deeptutor.plugins.loader import discover_integrations

    cfg = ConfigManager().load_config()
    manifests = discover_integrations()
    manifest = _resolve_integration_name(name, manifests)
    if not manifest:
        raise HTTPException(status_code=404, detail=f"Integration '{name}' not found")
    overrides = _ui_overrides(cfg, manifest.name)
    return _integration_payload(manifest, overrides=overrides)


class UiUpdateRequest(BaseModel):
    ui: dict[str, Any] | None = None
    reset: bool = False


@router.patch("/integrations/{name}/ui")
async def patch_integration_ui(name: str, body: UiUpdateRequest):
    _require_admin()

    from deeptutor.plugins.loader import discover_integrations

    manifests = discover_integrations()
    manifest = _resolve_integration_name(name, manifests)
    if not manifest:
        raise HTTPException(status_code=404, detail=f"Integration '{name}' not found")

    name = manifest.name
    if body.reset:
        update: dict[str, Any] = {"ui_overrides": {"integrations": {name: None}}}
    else:
        update = {"ui_overrides": {"integrations": {name: {"ui": body.ui or {}}}}}

    ConfigManager().save_config(update)
    return {"success": True}


@router.get("/integrations/{name}/probe")
async def probe_integration(name: str):
    from deeptutor.plugins.loader import discover_integrations
    import httpx

    cfg = ConfigManager().load_config()
    manifests = discover_integrations()
    manifest = _resolve_integration_name(name, manifests)
    if not manifest:
        raise HTTPException(status_code=404, detail=f"Integration '{name}' not found")
    overrides = _ui_overrides(cfg, manifest.name)
    payload = _integration_payload(manifest, overrides=overrides)
    entry = (payload.get("ui") or {}).get("entry") if isinstance(payload.get("ui"), dict) else None
    url = entry.get("url") if isinstance(entry, dict) else None
    if not url:
        return {"ok": False, "reason": "no_url"}
    try:
        async with httpx.AsyncClient(timeout=3.5, follow_redirects=True) as client:
            resp = await client.get(url)
            return {"ok": True, "status_code": resp.status_code}
    except Exception as exc:
        return {"ok": False, "reason": "unreachable", "error": str(exc)}
