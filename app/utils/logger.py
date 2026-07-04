"""Structured logging setup with request context."""
import logging
import os
from pathlib import Path
from typing import Optional
from app.config import settings


def setup_logger(name: str = "it_support_assistant") -> logging.Logger:
    """Set up and configure the application logger."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # File handler
    file_handler = logging.FileHandler(settings.LOG_DIR / "app.log")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger


def log_with_context(
    logger: logging.Logger,
    level: int,
    message: str,
    request_id: Optional[str] = None,
    intent: Optional[str] = None,
    confidence: Optional[float] = None,
    execution_time_ms: Optional[float] = None,
    ticket_id: Optional[str] = None,
    **kwargs
) -> None:
    """Log a message with structured context."""
    context_parts = []
    if request_id:
        context_parts.append(f"request_id={request_id}")
    if intent:
        context_parts.append(f"intent={intent}")
    if confidence is not None:
        context_parts.append(f"confidence={confidence:.2f}")
    if execution_time_ms is not None:
        context_parts.append(f"execution_time={execution_time_ms:.2f}ms")
    if ticket_id:
        context_parts.append(f"ticket_id={ticket_id}")
    for key, value in kwargs.items():
        context_parts.append(f"{key}={value}")
    
    full_message = message
    if context_parts:
        full_message += f" [{', '.join(context_parts)}]"
    
    logger.log(level, full_message)
