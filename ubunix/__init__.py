from pathlib import Path
from typing import Annotated, List, Optional, Set

import typer

from ubunix.apt import get_apt_manifest
from ubunix.constants import PACKAGE_MANAGER_NAMES, XDG_DATA_HOME, PackageManagerName
from ubunix.flatpak import get_flatpak_manifest
from ubunix.guix import format_guix_manifest, get_guix_manifest
from ubunix.nix import NIX_FLAKE_CONTENTS, format_nix_manifest, get_nix_manifest
from ubunix.parser import ConfigDict, MetaPackage, parse_config
from ubunix.utils import (
    format_yaml_file,
    is_command_installed,
    read_yaml_file,
    skip_nones,
    write_yaml_file,
)


def read_packages_file(packages_file_path: Path) -> List[MetaPackage]:
    try:
        packages: ConfigDict = read_yaml_file(packages_file_path)
    except FileNotFoundError:
        raise Exception(f"Packages file not found: `{packages_file_path}`.")
    else:
        return parse_config(packages)


def get_installed_package_managers() -> List[PackageManagerName]:
    return [
        package_manager_name
        for package_manager_name in PACKAGE_MANAGER_NAMES
        if is_command_installed(package_manager_name)
    ]


def get_install_with(
    meta_package: MetaPackage, installed_package_managers: List[PackageManagerName]
) -> Set[PackageManagerName]:
    if meta_package.ignore:
        return set()
    else:
        package_specs = skip_nones(
            [
                meta_package.package_specs.get(package_manager_name)
                for package_manager_name in installed_package_managers
            ]
        )
        forced_package_managers: List[PackageManagerName] = [
            package_spec.package_manager_name
            for package_spec in package_specs
            if package_spec.force
        ]
        highest_priority_package_manager: Optional[PackageManagerName] = next(
            (
                package_spec.package_manager_name
                for package_spec in package_specs
                if not package_spec.ignore
            ),
            None,
        )
        return set(
            forced_package_managers
            + (
                []
                if highest_priority_package_manager is None
                else [highest_priority_package_manager]
            )
        )  # type: ignore


app = typer.Typer()


@app.command()
def generate(
    packages_file_path: Annotated[Path, typer.Option("--packages")],
    flatpak_manifest_file_path: Annotated[Path, typer.Option("--flatpak-manifest")],
    guix_manifest_file_path: Annotated[Path, typer.Option("--guix-manifest")],
    apt_manifest_file_path: Annotated[Path, typer.Option("--apt-manifest")],
    nix_manifest_path: Annotated[Path, typer.Option("--nix-manifest")],
    guix_profile_path: Annotated[Path, typer.Option("--guix-profile")] = XDG_DATA_HOME
    / "guix-profiles"
    / "default",
    nix_profile_path: Annotated[Path, typer.Option("--nix-profile")] = XDG_DATA_HOME
    / "nix-profile",
) -> None:
    installed_package_managers = get_installed_package_managers()
    packages = [
        (p, get_install_with(p, installed_package_managers))
        for p in read_packages_file(packages_file_path)
    ]
    if "flatpak" in installed_package_managers:
        package_specs_to_install = skip_nones(
            [
                p.package_specs.get("flatpak")
                for (p, install_with) in packages
                if "flatpak" in install_with
            ]
        )
        package_specs_to_remove = skip_nones(
            [
                p.package_specs.get("flatpak")
                for (p, install_with) in packages
                if "flatpak" not in install_with
            ]
        )
        flatpak_manifest = get_flatpak_manifest(
            package_specs_to_install, package_specs_to_remove
        )
        with open(flatpak_manifest_file_path, "w") as f:
            f.write(flatpak_manifest)

    if "guix" in installed_package_managers:
        package_specs_to_install = skip_nones(
            [
                p.package_specs.get("guix")
                for (p, install_with) in packages
                if "guix" in install_with
            ]
        )
        guix_manifest = get_guix_manifest(package_specs_to_install)
        with open(guix_manifest_file_path, "w") as f:
            f.write(guix_manifest)
        format_guix_manifest(guix_manifest_file_path)

    if "apt" in installed_package_managers:
        package_specs_to_install = skip_nones(
            [
                p.package_specs.get("apt")
                for (p, install_with) in packages
                if "apt" in install_with
            ]
        )
        package_specs_to_remove = skip_nones(
            [
                p.package_specs.get("apt")
                for (p, install_with) in packages
                if "apt" not in install_with
            ]
        )
        apt_manifest = get_apt_manifest(
            package_specs_to_install, package_specs_to_remove
        )
        with open(apt_manifest_file_path, "w") as f:
            f.write(apt_manifest)

    if "nix" in installed_package_managers:
        package_specs_to_install = skip_nones(
            [
                p.package_specs.get("nix")
                for (p, install_with) in packages
                if "nix" in install_with
            ]
        )
        nix_manifest = get_nix_manifest(package_specs_to_install)

        # Create folder
        nix_manifest_path.mkdir(parents=True, exist_ok=True)

        nix_flake_file_path = nix_manifest_path / "flake.nix"
        home_manager_manifest_path = nix_manifest_path / "home.nix"

        with open(nix_flake_file_path, "w") as f:
            f.write(NIX_FLAKE_CONTENTS)
        with open(home_manager_manifest_path, "w") as f:
            f.write(nix_manifest)

        format_nix_manifest(nix_manifest_path / "flake.nix")
        format_nix_manifest(nix_manifest_path / "home.nix")

    for p, install_with in packages:
        if len(install_with) == 0:
            print(f"Package `{p.name}` was not installed.")


@app.command()
def format(packages_file_path: Annotated[Path, typer.Option("--packages")]) -> None:
    meta_packages = read_packages_file(packages_file_path)
    categories = sorted(list({p.category for p in meta_packages}))
    meta_packages_by_category = dict(
        [
            (
                category,
                dict(
                    sorted(
                        [
                            meta_package.serialise()
                            for meta_package in meta_packages
                            if meta_package.category == category
                        ],
                        key=lambda x: x[0],
                    )
                ),
            )
            for category in categories
        ]
    )
    write_yaml_file(meta_packages_by_category, packages_file_path)
    format_yaml_file(packages_file_path)


def main() -> None:
    app()
