"""Game logger: track player actions and game state for debugging and UX.

Provides a centralized logging system that can output to:
- In-game message log (shown on screen)
- Debug log file (for troubleshooting)
- Console stderr (for development)
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from pathlib import Path


class LogLevel(StrEnum):
    """Log message severity."""

    DEBUG = "debug"  # Detailed internal state
    INFO = "info"  # Normal actions (player moves, selects menu)
    ACTION = "action"  # Important player actions (use skill, extract data)
    WARNING = "warning"  # Unexpected but recoverable
    ERROR = "error"  # Errors


@dataclass
class GameLogger:
    """Centralized game logger."""

    # In-game message log (shown to player)
    messages: list[str] = field(default_factory=list)
    # Debug log file path (None = disabled)
    log_file: Path | None = None
    # Enable console output
    console_enabled: bool = True
    # Current log level filter
    level: LogLevel = LogLevel.INFO

    def log(self, level: LogLevel, message: str, context: str = "") -> None:
        """Log a message at the given level."""
        # Skip if below current level
        level_order = {
            LogLevel.DEBUG: 0,
            LogLevel.INFO: 1,
            LogLevel.ACTION: 2,
            LogLevel.WARNING: 3,
            LogLevel.ERROR: 4,
        }
        if level_order[level] < level_order[self.level]:
            return

        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = level.upper()
        full_message = f"[{timestamp}] {prefix}: {message}"
        if context:
            full_message += f" ({context})"

        # Console output (stderr)
        if self.console_enabled:
            sys.stderr.write(f"{full_message}\n")
            sys.stderr.flush()

        # Log file output
        if self.log_file:
            try:
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(f"{full_message}\n")
            except OSError:
                pass  # Ignore file errors

        # In-game messages (only INFO, ACTION, WARNING, ERROR)
        if level in (LogLevel.INFO, LogLevel.ACTION, LogLevel.WARNING, LogLevel.ERROR):
            self.messages.append(message)
            # Keep only last 20 messages
            if len(self.messages) > 20:
                self.messages.pop(0)

    def debug(self, message: str, context: str = "") -> None:
        """Log a debug message."""
        self.log(LogLevel.DEBUG, message, context)

    def info(self, message: str, context: str = "") -> None:
        """Log an info message."""
        self.log(LogLevel.INFO, message, context)

    def action(self, message: str, context: str = "") -> None:
        """Log an important player action."""
        self.log(LogLevel.ACTION, message, context)

    def warning(self, message: str, context: str = "") -> None:
        """Log a warning."""
        self.log(LogLevel.WARNING, message, context)

    def error(self, message: str, context: str = "") -> None:
        """Log an error."""
        self.log(LogLevel.ERROR, message, context)

    def get_recent(self, count: int = 5) -> list[str]:
        """Get the most recent N messages."""
        return self.messages[-count:]

    def clear(self) -> None:
        """Clear in-game messages."""
        self.messages.clear()


# Global logger instance
_logger: GameLogger | None = None


def get_logger() -> GameLogger:
    """Get the global logger instance."""
    global _logger
    if _logger is None:
        _logger = GameLogger()
    return _logger


def init_logger(
    log_file: Path | None = None,
    console_enabled: bool = True,
    level: LogLevel = LogLevel.INFO,
) -> GameLogger:
    """Initialize the global logger with custom settings."""
    global _logger
    _logger = GameLogger(log_file=log_file, console_enabled=console_enabled, level=level)
    return _logger
