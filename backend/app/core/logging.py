import sys

from loguru import logger

from ..config import get_settings


def setup_logging() -> None:
    """配置后端统一日志格式。"""
    settings = get_settings()
    logger.remove()
    logger.add(
        sys.stderr,
        level=settings.log_level.upper(),
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        enqueue=True,
        backtrace=settings.debug,
        diagnose=False,
    )
