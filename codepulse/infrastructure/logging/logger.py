"""Application-wide logging setup.

Call :func:`configure_logging` exactly once, at startup, before any other
CodePulse module logs. Every module then does ``from loguru import logger``
directly rather than requesting a per-module logger instance.
"""

from __future__ import annotations

import logging
import sys
from types import FrameType

from loguru import logger

from codepulse.infrastructure.config.settings import AppSettings

_LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)


class _InterceptHandler(logging.Handler):
    """Routes stdlib ``logging`` records (e.g. from httpx) into loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level: str | int = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame: FrameType | None = logging.currentframe()
        depth = 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def configure_logging(settings: AppSettings) -> None:
    """Configure loguru sinks and redirect stdlib logging into loguru.

    Sets up a colorized console sink and a rotating, compressed file sink
    under ``settings.log_dir``. Safe to call once at process startup.
    """
    settings.log_dir.mkdir(parents=True, exist_ok=True)

    logger.remove()
    logger.add(sys.stderr, level=settings.log_level, format=_LOG_FORMAT, colorize=True)
    logger.add(
        settings.log_dir / "codepulse.log",
        level=settings.log_level,
        format=_LOG_FORMAT,
        rotation="10 MB",
        retention="14 days",
        compression="zip",
        enqueue=True,
        backtrace=False,
        diagnose=False,
    )

    logging.basicConfig(handlers=[_InterceptHandler()], level=0, force=True)

    logger.info("Logging configured (level={}, dir={})", settings.log_level, settings.log_dir)
