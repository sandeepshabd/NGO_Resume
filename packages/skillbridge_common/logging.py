from __future__ import annotations

import logging
import os
from typing import Any

from pythonjsonlogger import jsonlogger


def configure_logging() -> None:
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s %(agent)s %(task_id)s %(trace_id)s"
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
    return SkillBridgeLoggerAdapter(logger, {"agent": agent_name, "task_id": None, "trace_id": None})


def log_task_event(
    logger: logging.LoggerAdapter[logging.Logger],
    message: str,
    *,
    task_id: str,
    trace_id: str,
    **fields: Any,
) -> None:
    extra = {"task_id": task_id, "trace_id": trace_id, **fields}
    logger.info(message, extra=extra)
