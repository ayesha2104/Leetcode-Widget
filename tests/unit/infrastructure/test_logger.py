from __future__ import annotations

import logging
import sys
from pathlib import Path

import pytest
from loguru import logger

from codepulse.infrastructure.config.settings import AppSettings
from codepulse.infrastructure.logging.logger import configure_logging


def test_configure_logging_creates_rotating_file_sink(tmp_path: Path) -> None:
    settings = AppSettings(data_dir=tmp_path)

    configure_logging(settings)
    logger.info("hello from test")
    logger.complete()  # enqueue=True sinks write on a background thread

    log_file = settings.log_dir / "codepulse.log"
    assert log_file.exists()
    assert "hello from test" in log_file.read_text(encoding="utf-8")


def test_stdlib_logging_is_routed_through_loguru(tmp_path: Path) -> None:
    settings = AppSettings(data_dir=tmp_path)

    configure_logging(settings)
    logging.getLogger("httpx").warning("stdlib warning message")
    logger.complete()

    log_file = settings.log_dir / "codepulse.log"
    assert "stdlib warning message" in log_file.read_text(encoding="utf-8")


def test_stdlib_logging_with_a_custom_level_falls_back_to_level_number(tmp_path: Path) -> None:
    settings = AppSettings(data_dir=tmp_path)
    configure_logging(settings)

    # 25 has no name in either stdlib or loguru (stdlib: INFO=20, WARNING=30),
    # so stdlib assigns it "Level 25", which logger.level() cannot resolve --
    # exercising the ValueError fallback to the raw level number. It must be
    # >= the sink's INFO threshold (20) or the message would be filtered
    # before ever reaching the fallback logic.
    custom_level_number = 25
    logging.getLogger("custom").log(custom_level_number, "custom level message")
    logger.complete()

    log_file = settings.log_dir / "codepulse.log"
    assert "custom level message" in log_file.read_text(encoding="utf-8")


def test_configure_logging_does_not_crash_when_stderr_is_none(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A windowed (console=False) PyInstaller build has sys.stderr set to
    None -- loguru.add(None, ...) raises TypeError, which previously crashed
    the packaged .exe on startup before any window could even open."""
    monkeypatch.setattr(sys, "stderr", None)
    settings = AppSettings(data_dir=tmp_path)

    configure_logging(settings)
    logger.info("hello with no console")
    logger.complete()

    log_file = settings.log_dir / "codepulse.log"
    assert "hello with no console" in log_file.read_text(encoding="utf-8")
