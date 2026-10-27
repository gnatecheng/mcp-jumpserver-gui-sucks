from __future__ import annotations

import logging

_CONFIGURED = False


def configure_logging(level: str) -> None:
    global _CONFIGURED

    if _CONFIGURED:
        return

    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    _CONFIGURED = True


def set_package_log_level(level: str) -> None:
    numeric = getattr(logging, level.upper(), logging.INFO)
    logging.getLogger("mcp_jumpserver_gui_sucks").setLevel(numeric)
