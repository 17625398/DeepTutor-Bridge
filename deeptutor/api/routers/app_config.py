"""Application config endpoint — serves runtime configuration to the frontend."""

from __future__ import annotations

import os

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class AppConfigResponse(BaseModel):
    app_name: str
    logo_url: str
    background_url: str


@router.get("/app", response_model=AppConfigResponse)
async def get_app_config() -> AppConfigResponse:
    """Return application-level configuration for the frontend."""
    return AppConfigResponse(
        app_name=os.environ.get("NEXT_PUBLIC_APP_NAME", "DeepTutor"),
        logo_url=os.environ.get("NEXT_PUBLIC_APP_LOGO", "/logo-ver2.png"),
        background_url=os.environ.get("NEXT_PUBLIC_APP_BACKGROUND", ""),
    )
