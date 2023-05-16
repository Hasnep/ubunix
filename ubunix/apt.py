from pathlib import Path
from typing import List

from ubunix.parser import PackageSpec
from ubunix.utils import flatten


def get_apt_manifest(
    package_specs_to_install: List[PackageSpec],
    package_specs_to_remove: List[PackageSpec],
) -> str:
    package_names_to_install = flatten(
        [package_spec.packages for package_spec in package_specs_to_install]
    )
    package_names_to_remove = [
        package_name
        for package_name in flatten(
            [package_spec.packages for package_spec in package_specs_to_remove]
        )
        if package_name not in package_names_to_install
    ]
    return "\n".join(
        [
            "sudo nala remove " + " ".join(sorted(package_names_to_remove))
            if len(package_names_to_remove) > 0
            else "",
            "sudo nala install " + " ".join(sorted(package_names_to_install))
            if len(package_names_to_install) > 0
            else "",
        ]
    )


def get_apt_install_command(apt_manifest_file_path: Path) -> str:
    return " ".join(["source", str(apt_manifest_file_path)])
