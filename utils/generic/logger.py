import logging
from typing import Any, Optional, Union, NoReturn
from utils.generic.colors import ColorFormatter, blue, green


class ColorizedLogger:
    """Singleton logger configuration with colorized output for enhanced readability."""

    _instance: Optional["ColorizedLogger"] = None
    _initialized: bool = False
    stacklevel: int = 2

    def __new__(cls, *args: Any, **kwargs: Any) -> "ColorizedLogger":
        """Create an instance IFF it does not exist yet."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, level: int = logging.INFO) -> None:
        """Initialize a colorized logger with a custom console handler.

        Args:
            level (int): Initial logging level (e.g., logging.INFO, logging.DEBUG).
        """
        if isinstance(level, str):
            level = get_logging_level(level_name=level)
        if not self._initialized:
            self._root_logger = logging.getLogger()
            # Remove existing handlers to avoid duplicate logs
            for handler in self._root_logger.handlers[:]:
                self._root_logger.removeHandler(handler)
            # Set up the console handler with color formatting
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(ColorFormatter())
            console_handler.setLevel(level)

            self._root_logger.addHandler(console_handler)
            self._root_logger.setLevel(level)
            self._initialized = True

    def get_logger(self) -> logging.Logger:
        """Retrieve the underlying root logger instance."""
        return self._root_logger

    def set_level(self, log_level: int) -> None:
        """Set the logging level."""
        if isinstance(log_level, str):
            log_level = get_logging_level(level_name=log_level)
        self.get_logger().setLevel(log_level)

    def get_level(self) -> int:
        """Get the effective logging level."""
        return self.get_logger().getEffectiveLevel()

    def debug(self, message: str) -> None:
        """Log a debug message."""
        self.get_logger().debug(message, stacklevel=self.stacklevel)

    def info(self, message: str) -> None:
        """Log an informational message."""
        self.get_logger().info(message, stacklevel=self.stacklevel)

    def warning(self, message: str) -> None:
        """Log a warning message."""
        self.get_logger().warning(message, stacklevel=self.stacklevel)

    def error(self, message: str, exception_cls: Optional[type[Exception]] = None) -> None:
        """Log an error message and optionally raise an exception.

        Args:
            message (str): The error message to log.
            exception_cls (Optional[type[Exception]]): The exception class to raise, if any.
        """
        self.get_logger().error(message, stacklevel=self.stacklevel)
        if exception_cls is not None:
            raise exception_cls(message)

    def critical(self, message: str, exception_cls: type[Exception]) -> NoReturn:
        """Log a critical error message and raise an exception.

        Args:
            message (str): The critical error message to log.
            exception_cls (type[Exception]): The exception class to raise.
        """
        self.get_logger().critical(message, stacklevel=self.stacklevel)
        raise exception_cls(message)


def get_logging_level(level_name: Union[int, str]) -> int:
    """Convert a logging level string to its corresponding logging constant.

    Args:
        level_name (str): Logging level as a string (e.g., "DEBUG", "INFO").

    Returns:
        int: Corresponding logging level constant (e.g., logging.DEBUG).

    Raises:
        ValueError: If the level_name is not a valid logging level.
    """
    try:
        return getattr(logging, level_name.upper()) if isinstance(level_name, str) else level_name
    except AttributeError as exception:
        raise ValueError(f"Invalid logging level: {level_name}") from exception


def initialize_colorized_logger(log_level: Union[str, int]) -> ColorizedLogger:
    """Initialize and configure an instance of ColorizedLogger.

    Args:
        log_level (Union[str, int]): Desired logging level as a string (e.g., "DEBUG", "INFO") or int (e.g., 10, 20).

    Returns:
        ColorizedLogger: The configured ColorizedLogger instance.
    """
    colorized_logger = ColorizedLogger(level=logging.DEBUG)
    colorized_logger.set_level(get_logging_level(level_name=log_level))
    return colorized_logger


if __name__ == "__main__":
    test_message = "test"
    logger = initialize_colorized_logger("DEBUG")
    logger.debug("Verbose debug message")
    logger.info(test_message)
    logger.info(blue(test_message))
    logger.info(green(test_message))
    logger.warning("This is a warning message.")
    logger.error("This is an error message, not critical enough to interrupt the execution. Optionally raises an exception.")
    logger.critical("This is a critical error message, therefore the execution is stopped.", exception_cls=ValueError)
