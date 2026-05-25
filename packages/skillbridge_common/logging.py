from __future__ import annotations

import logging
import os
from typing import Any

from pythonjsonlogger import jsonlogger

from skillbridge_common.privacy import redact_dict


RESERVED_LOG_RECORD_KEYS = set(
    logging.LogRecord(
        name="reserved",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="",
        args=(),
        exc_info=None,
    ).__dict__.keys()
) | {"message", "asctime"}


def configure_logging() -> None:
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s %(agent)s %(task_id)s %(trace_id)s "
        "%(workflow_id)s %(step_id)s %(event_type)s %(status)s %(duration_ms)s"
    )
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)


class SkillBridgeLoggerAdapter(logging.LoggerAdapter[logging.Logger]):
    def process(self, msg: str, kwargs: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        supplied = kwargs.get("extra", {})
        kwargs["extra"] = {**self.extra, **supplied}
        return msg, kwargs


def agent_logger(agent_name: str) -> logging.LoggerAdapter[logging.Logger]:
    logger = logging.getLogger(agent_name)
    return SkillBridgeLoggerAdapter(
        logger,
        {
            "agent": agent_name,
            "task_id": None,
            "trace_id": None,
            "workflow_id": None,
            "step_id": None,
            "event_type": None,
            "status": None,
            "duration_ms": None,
        },
    )


def log_task_event(
    logger: logging.LoggerAdapter[logging.Logger],
    message: str,
    *,
    task_id: str,
    trace_id: str,
    **fields: Any,
) -> None:
    extra = _safe_extra(redact_dict({"task_id": task_id, "trace_id": trace_id, **fields}))
    logger.info(message, extra=extra)


def log_workflow_event(
    logger: logging.LoggerAdapter[logging.Logger],
    event_type: str,
    *,
    workflow_id: str,
    trace_id: str,
    step_id: str | None = None,
    status: str | None = None,
    duration_ms: int | None = None,
    **fields: Any,
) -> None:
    extra = _safe_extra(redact_dict(
        {
            "workflow_id": workflow_id,
            "trace_id": trace_id,
            "step_id": step_id,
            "event_type": event_type,
            "status": status,
            "duration_ms": duration_ms,
            **fields,
        }
    ))
    logger.info(event_type, extra=extra)


def _safe_extra(extra: dict[str, Any]) -> dict[str, Any]:
    return {
        (f"field_{key}" if key in RESERVED_LOG_RECORD_KEYS else key): value
        for key, value in extra.items()
    }
