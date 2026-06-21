"""日志配置 — 使用 loguru"""

import sys
from pathlib import Path

from loguru import logger as _logger

from config.settings import settings


def setup_logger() -> None:
    """配置全局日志"""
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    _logger.remove()
    _logger.add(
        sys.stderr,
        level=settings.log_level,
        format=log_format,
    )

    log_file = settings.data_dir / "logs" / "app.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    _logger.add(
        log_file,
        rotation="10 MB",
        retention="30 days",
        level="DEBUG",
        format=log_format,
    )


logger = _logger
setup_logger()
