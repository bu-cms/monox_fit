import logging
from typing import Any
from functools import partial
from collections.abc import Callable


class Colors:
    """Class representing ANSI color codes for terminal output. Taken from blender."""

    # Reset and basic attributes
    reset: str = "\033[0m"
    bold: str = "\033[1m"

    # Standard colors
    white: str = "\033[0;97m"
    black: str = "\033[0;30m"
    red: str = "\033[0;91m"
    orange: str = "\033[38;5;208m"
    light_orange: str = "\033[38;5;214m"
    yellow: str = "\033[0;93m"
    green: str = "\033[0;92m"
    cyan: str = "\033[0;96m"
    blue: str = "\033[0;94m"
    light_purple: str = "\033[38;5;177m"
    magenta: str = "\033[0;95m"


def colorize_text(color: str, *args: str, sep: str = " ") -> str:
    """Applies color attribute to a string.

    Args:
        color (str): The ANSI escape code for the desired color or attribute.
        *args (str): The text components to format.
        sep (str): The separator to use when joining the components.

    Returns:
        str: The colorized string with the ANSI reset code appended.
    """
    text = sep.join(args)
    return f"{color}{text}{Colors.reset}"


# Partial functions for coloring strings
bold: Callable[..., str] = partial(colorize_text, Colors.white)
white: Callable[..., str] = partial(colorize_text, Colors.white)
black: Callable[..., str] = partial(colorize_text, Colors.black)
red: Callable[..., str] = partial(colorize_text, Colors.red)
orange: Callable[..., str] = partial(colorize_text, Colors.orange)
light_orange: Callable[..., str] = partial(colorize_text, Colors.light_orange)
yellow: Callable[..., str] = partial(colorize_text, Colors.yellow)
green: Callable[..., str] = partial(colorize_text, Colors.green)
cyan: Callable[..., str] = partial(colorize_text, Colors.cyan)
blue: Callable[..., str] = partial(colorize_text, Colors.blue)
light_purple: Callable[..., str] = partial(colorize_text, Colors.light_purple)
magenta: Callable[..., str] = partial(colorize_text, Colors.magenta)


def prettydict(data: dict[Any, Any], indent: int = 4, color: Callable[..., str] = blue) -> None:
    """Pretty-prints a dictionary with color formatting.

    Args:
        data (dict[Any, Any]): The dictionary to print.
        indent (int): Number of spaces for indentation.
        color (Callable[..., str]): Function to colorize the output.
    """
    space = max([0] + [len(str(x)) for x in data]) + 2
    print("")
    for key, value in data.items():
        print(color(" " * indent + str(key)), end="")
        if isinstance(value, dict):
            prettydict(value, indent=indent + 4, color=color)
        else:
            print(color(" " * (indent + space - len(str(key))) + str(value)))


class ColorFormatter(logging.Formatter):
    """Custom logging formatter that applies color formatting based on log level."""

    _log_format: str = "%(levelname)-8s | %(module)s::%(funcName)s: %(message)s"

    _formats: dict[int, str] = {
        logging.DEBUG: orange(_log_format),
        logging.INFO: cyan(_log_format),
        logging.WARNING: yellow(_log_format),
        logging.ERROR: red(_log_format),
        logging.CRITICAL: red(_log_format),
    }

    def format(self, record: logging.LogRecord) -> str:  # noqa A003
        """Formats a log record with color based on its log level.

        Args:
            record (logging.LogRecord): The log record to format.

        Returns:
            str: The formatted log message.
        """
        log_fmt = self._formats.get(record.levelno, self._log_format)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


if __name__ == "__main__":
    test_string = "test"
    print(f"{test_string} in normal")
    print(bold(f"{test_string} in bold"))
    print(white(f"{test_string} in white"))
    print(black(f"{test_string} in black"))
    print(red(f"{test_string} in red"))
    print(orange(f"{test_string} in orange"))
    print(light_orange(f"{test_string} in light_orange"))
    print(yellow(f"{test_string} in yellow"))
    print(green(f"{test_string} in green"))
    print(cyan(f"{test_string} in cyan"))
    print(blue(f"{test_string} in blue"))
    print(light_purple(f"{test_string} in light_purple"))
    print(magenta(f"{test_string} in magenta"))
