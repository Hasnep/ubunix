import subprocess
from pathlib import Path
from textwrap import dedent
from typing import List

from ubunix.parser import PackageSpec
from ubunix.utils import flatten, is_command_installed


def get_nix_manifest(package_specs_to_install: List[PackageSpec]) -> str:
    package_names_to_install = flatten(
        [package_spec.packages for package_spec in package_specs_to_install]
    )
    packages_joined = " ".join(
        [f"pkgs.{package_name}" for package_name in sorted(package_names_to_install)]
    )
    return dedent(
        f"""
        {{ config, pkgs, ... }}: {{
            home.username = "hannes";
            home.homeDirectory = "{Path().home()}";
            home.stateVersion = "22.11";
            home.packages = [
                {packages_joined}
            ];
            programs.home-manager.enable = true; # Let Home Manager install and manage itself.
        }}
        """
    )


def format_nix_manifest(manifest_file_path: Path) -> None:
    format_command = (
        ["alejandra"]
        if is_command_installed("alejandra")
        else ["nix", "run", "nixpkgs#alejandra", "--"]
    ) + [str(manifest_file_path)]
    print(f"Formatting manifest file using command `{' '.join(format_command)}`.")
    subprocess.run(format_command, capture_output=True)


def get_nix_install_command() -> str:
    return " ".join(["nix", "run", "home-manager/master", "--", "switch"])


NIX_FLAKE_CONTENTS = dedent(
    r"""
    {
        description = "Home Manager configuration generated by Ubunix";
        inputs = {
            nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
            home-manager = {
            url = "github:nix-community/home-manager";
            inputs.nixpkgs.follows = "nixpkgs";
            };
        };
        outputs = { nixpkgs, home-manager, ... }:
            let
            system = "x86_64-linux";
            pkgs = nixpkgs.legacyPackages.${system};
            in {
            homeConfigurations.hannes = home-manager.lib.homeManagerConfiguration {
                inherit pkgs;
                modules = [ ./home.nix ];
            };
        };
    }
    """
)