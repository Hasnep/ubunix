import subprocess
from pathlib import Path
from typing import Any, List, Optional, TypeVar

from ruamel.yaml import YAML as Yaml

T = TypeVar("T")


def flatten(nested_list: List[List[T]]) -> List[T]:
    return [item for sublist in nested_list for item in sublist]


def enquote(s: str) -> str:
    return f'"{s}"'


def skip_nones(xs: List[Optional[T]]) -> List[T]:
    return [x for x in xs if x is not None]


def read_yaml_file(file_path: Path) -> Any:
    with open(file_path, "r") as f:
        return Yaml().load(f)


def write_yaml_file(contents: Any, file_path: Path) -> None:
    with open(file_path, "w") as f:
        Yaml().dump(contents, f)


def is_command_installed(command: str) -> bool:
    try:
        subprocess.check_output(["which", command])
        return True
    except subprocess.CalledProcessError:
        return False


def format_yaml_file(file_path: Path) -> None:
    format_command = ["prettier", "--write", str(file_path)]
    print(f"Formatting YAML file using command `{' '.join(format_command)}`.")
    subprocess.run(format_command, capture_output=True)
