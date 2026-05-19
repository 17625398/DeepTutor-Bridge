"""Application config endpoint — serves runtime configuration to the frontend."""

from __future__ import annotations

import os

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class AppConfigResponse(BaseModel):
    app_name: str


@router.get("/app", response_model=AppConfigResponse)
async def get_app_config() -> AppConfigResponse:
    """Return application-level configuration for the frontend."""
    return AppConfigResponse(
        app_name=os.environ.get("NEXT_PUBLIC_APP_NAME", "DeepTutor"),
    )
