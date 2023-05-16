import subprocess
from pathlib import Path
from typing import List

from ubunix.parser import PackageSpec
from ubunix.utils import enquote, flatten


def get_guix_manifest(package_specs_to_install: List[PackageSpec]) -> str:
    # Flatten list of package names
    packages_to_install = flatten(
        [package_spec.packages for package_spec in package_specs_to_install]
    )
    package_names_joined = "\n".join(
        [enquote(package_name) for package_name in sorted(packages_to_install)]
    )
    return f"(specifications->manifest '({package_names_joined}))"


def format_guix_manifest(manifest_file_path: Path) -> None:
    format_command = ["guix", "style", "--whole-file", str(manifest_file_path)]
    print(f"Formatting manifest file using command `{' '.join(format_command)}`.")
    subprocess.run(format_command, capture_output=True)


def get_guix_install_command(
    guix_manifest_file_path: Path, guix_profile_path: Path
) -> str:
    return " ".join(
        [
            "guix",
            "package",
            f"--manifest={guix_manifest_file_path}",
            f"--profile={guix_profile_path}",
        ]
    )
