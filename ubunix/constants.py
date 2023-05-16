import os
from pathlib import Path
from typing import List, Literal

XDG_CONFIG_HOME = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config"))
XDG_DATA_HOME = Path(os.getenv("XDG_DATA_HOME", Path.home() / ".local" / "share"))


PackageManagerName = Literal["flatpak", "guix", "apt", "nix"]
PACKAGE_MANAGER_NAMES: List[PackageManagerName] = ["flatpak", "guix", "apt", "nix"]
