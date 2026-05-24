from __future__ import annotations

import os

from fastapi import Header, HTTPException, status


def require_agent_token(x_skillbridge_agent_token: str | None = Header(default=None)) -> None:
    expected = os.getenv("SKILLBRIDGE_AGENT_TOKEN")
    if not expected:
        return
    if x_skillbridge_agent_token != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid agent token",
        )

