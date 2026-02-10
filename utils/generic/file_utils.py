import os
import re
import subprocess
import json
import gzip
from typing import Any, Optional, Union
import yaml  # type: ignore
from utils.generic.logger import initialize_colorized_logger

# Initialize module-level logger
logger = initialize_colorized_logger(log_level="INFO")


def to_snake_case(name: str) -> str:
    """Convert a CamelCase or PascalCase string to snake_case.

    Rules:
    1. If the input string is entirely uppercase (e.g., an acronym like "MET"),
       it is converted to lowercase (e.g., "met").
    2. For standard CamelCase or PascalCase strings (e.g., "GenBosonFinder"),
       underscores are inserted before each uppercase letter (except the first),
       and the entire string is converted to lowercase.
    3. If the input contains consecutive uppercase letters followed by lowercase letters
       (e.g., "EGMPhoTnp"), the second and subsequent uppercase letters in the sequence
       are converted to lowercase, preserving the first and last letters.
       The resulting string is then converted to snake_case.
    """
    if name.isupper():
        return name.lower()
    name = re.sub(r"(?<=[A-Z])([A-Z]+)(?=[A-Z][a-z])", lambda match: match.group(1).lower(), name)
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def execute_command(command: str, description: Optional[str] = None) -> None:
    """Execute a system command safely with logging.

    Args:
        command (str): The shell command to execute.
        description (Optional[str]): A human-readable description of the command's purpose.

    Raises:
        subprocess.CalledProcessError: If the command fails during execution.
    """
    description_text = f" ({description})" if description else ""
    logger.debug(f"Executing command: `{command}`{description_text}")
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
        )
        logger.debug(f"Command output: {result.stdout.strip()}")
    except subprocess.CalledProcessError as exception:
        error_message = exception.stderr.strip() if exception.stderr else str(exception)
        logger.critical(
            f"Command failed{description_text} with error: {error_message}",
            exception_cls=subprocess.CalledProcessError,
        )


def copy_and_remove_tmp_output(source_path: str, dest_path: str, copy_command: str = "cp", remove_command: str = "rm") -> None:
    """Copy a temporary file to a final location and remove the temporary file.

    Args:
        source_path (str): The input file location.
        dest_path (str): The output file location.
        copy_command (str): The command to copy the file. Defaults to "cp".
        remove_command (str): The command to remove the file. Defaults to "rm".

    Raises:
        subprocess.CalledProcessError: If the copy or remove commands fail.
    """
    execute_command(
        command=f"{copy_command} {source_path} {dest_path}",
        description="Copy temporary file to final destination",
    )
    execute_command(
        command=f"{remove_command} {source_path}",
        description="Remove temporary file",
    )


def load_yaml(file_path: str) -> dict[str, Any]:
    """Loads and returns the contents of a YAML file as a dict[str, Any]."""
    logger.debug(f"Loading YAML from: {file_path}")
    try:
        with open(file_path, "r", encoding="utf-8") as file_:
            content = yaml.safe_load(file_)
    except FileNotFoundError:
        logger.critical(f"File not found: {file_path}", exception_cls=FileNotFoundError)
    except yaml.YAMLError:
        logger.critical(f"Failed to parse YAML file: {file_path}", exception_cls=yaml.YAMLError)
    return content


def save_yaml(file_path: str, content: dict[str, Any]) -> None:
    """Save a dictionary as a YAML file.

    Args:
        file_path (str): The path to save the YAML file.
        content (dict[str, Any]): The dictionary to save.
    """
    logger.debug(f"Saving YAML to: {file_path}")
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as file_:
        yaml.dump(content, file_, sort_keys=False)


def load_json(file_path: str) -> dict[str, Any]:
    """Load and returns the contents of a JSON fileas a dict[str, Any]."""
    logger.debug(f"Loading JSON from: {file_path}")
    try:

        def open_func(path: str) -> Any:
            """Open a file, supporting both plain text and gzip-compressed JSON files."""
            if path.endswith(".json.gz"):
                return gzip.open(path, "rt", encoding="utf-8")  # Text mode with UTF-8 encoding
            return open(path, "r", encoding="utf-8")

        with open_func(file_path) as file_:
            content = json.load(file_)
    except FileNotFoundError:
        logger.critical(f"File not found: {file_path}", exception_cls=FileNotFoundError)
    except json.JSONDecodeError:
        logger.critical(f"Failed to parse JSON file: {file_path}", exception_cls=json.JSONDecodeError)
    return content


def save_json(file_path: str, content: dict[str, Any], sort_keys: bool, indent: int = 4) -> None:
    """Save a dictionary as a JSON file.

    Args:
        file_path (str): The path to save the JSON file.
        content (dict[str, Any]): The dictionary to save.
        sort_keys (bool): Whether to sort keys in the JSON file. Defaults to False.
        indent (int): Indentation level for formatting. Defaults to 4.
    """
    logger.debug(f"Saving JSON to: {file_path}")
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as file_:
        json.dump(content, file_, sort_keys=sort_keys, indent=indent)


def merge_dictionaries(dictionaries: list[dict[str, Any]]) -> dict[str, Any]:
    """Merge a list of dictionaries into a single one.

    Args:
        dictionaries (list[dict[str, Any]]): A list of dictionaries to merge.

    Returns:
        dict[str, Any]: A single dictionary containing all keys and values from the input dictionaries.
    """
    merged_dict: dict[str, Any] = {}
    for dictionary in dictionaries:
        merged_dict.update(dictionary)
    return merged_dict


def update_dict_recursively(original_dict: dict[str, Any], new_info: dict[str, Union[dict[str, Any], Any]]) -> None:
    """Recursively updates the original dictionary with new information.

    Args:
        original_dict (dict[str, Any]): The dictionary to be updated.
        new_info (dict[str,  Union[dict[str, Any], Any]]): The dictionary containing new information to update.
    """
    if new_info is None:
        return
    for key, sub_dict in new_info.items():
        if key in original_dict:
            if isinstance(sub_dict, dict):
                for sub_key, sub_sub_dict in sub_dict.items():
                    if isinstance(original_dict[key].get(sub_key), dict):
                        update_dict_recursively(original_dict[key][sub_key], sub_sub_dict)
                    else:
                        original_dict[key][sub_key] = sub_sub_dict
            else:
                original_dict[key] = sub_dict
        else:
            original_dict[key] = sub_dict
