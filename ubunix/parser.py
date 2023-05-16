from typing import Any, Dict, List, NamedTuple, NotRequired, Optional, Tuple, TypedDict

from ubunix.constants import PACKAGE_MANAGER_NAMES, PackageManagerName
from ubunix.utils import flatten, skip_nones


class PackageSpec(NamedTuple):
    package_manager_name: PackageManagerName
    ignore: bool
    force: bool
    comment: Optional[str]
    packages: List[str]

    def serialise(
        self,
    ) -> Tuple[str, Any]:
        packages_serialised = (
            self.packages[0] if len(self.packages) == 1 else sorted(self.packages)
        )
        if not self.ignore and self.comment is None and not self.force:
            return self.package_manager_name, packages_serialised
        else:
            return self.package_manager_name, dict(
                skip_nones(
                    [
                        (
                            ("comment", self.comment)
                            if self.comment is not None
                            else None
                        ),
                        (("ignore", self.ignore) if self.ignore else None),
                        (("force", self.force) if self.force else None),
                        ("packages", packages_serialised),
                    ]
                )
            )


class MetaPackage(NamedTuple):
    name: str
    category: str
    ignore: bool
    comment: Optional[str]
    package_specs: Dict[PackageManagerName, PackageSpec]

    def serialise(self) -> Tuple[str, Any]:
        package_specs = list(self.package_specs.items())
        package_specs_sorted = sorted(
            package_specs, key=lambda x: PACKAGE_MANAGER_NAMES.index(x[0])
        )
        package_specs_serialised = [ps.serialise() for (_, ps) in package_specs_sorted]
        if not self.ignore and self.comment is None:
            return self.name, dict(package_specs_serialised)
        else:
            return self.name, dict(
                skip_nones(
                    [
                        (("comment", self.comment) if self.comment else None),
                        (("ignore", self.ignore) if self.ignore else None),
                        *package_specs_serialised,
                    ]
                )
            )


Config = List[MetaPackage]


PackageSpecDictRaw = TypedDict(
    "PackageManagerConfigDict",
    {
        "packages": str | List[str],
        "force": NotRequired[bool],
        "ignore": NotRequired[bool],
        "comment": NotRequired[str],
    },
)
PackageSpecRaw = str | List[str] | PackageSpecDictRaw
PackageSpecDict = TypedDict(
    "PackageManagerConfigDict",
    {
        "packages": List[str],
        "force": bool,
        "ignore": bool,
        "comment": str,
    },
)
MetaPackageDict = TypedDict(
    "MetaPackageDict",
    {
        "ignore": NotRequired[bool],
        "comment": NotRequired[str],
        "guix": NotRequired[PackageSpecRaw],
        "apt": NotRequired[PackageSpecRaw],
        "nix": NotRequired[PackageSpecRaw],
        "flatpak": NotRequired[PackageSpecRaw],
    },
)
ConfigDict = Dict[str, Dict[str, MetaPackageDict]]


def parse_config(config_dict: ConfigDict) -> List[MetaPackage]:
    def parse_package_spec(
        package_spec_raw: PackageSpecRaw, package_manager_name: PackageManagerName
    ) -> PackageSpec:
        match package_spec_raw:
            case str() as package:
                packages = [package]
                ignore = False
                force = False
                comment = None
            case list() as packages:
                packages = packages
                ignore = False
                force = False
                comment = None
            case _ as package_manager_package_raw_dict:
                package_manager_package_raw_dict: PackageSpecDictRaw
                packages_raw = package_manager_package_raw_dict["packages"]
                packages = (
                    packages_raw if isinstance(packages_raw, list) else [packages_raw]
                )
                ignore = package_manager_package_raw_dict.get("ignore", False)
                force = package_manager_package_raw_dict.get("force", False)
                comment = package_manager_package_raw_dict.get("comment")
        if force and ignore:
            raise Exception(
                f"Both `force` and `ignore` were both set for packages `{', '.join(packages)}` from `{package_manager_name}`."
            )
        return PackageSpec(
            package_manager_name=package_manager_name,
            ignore=ignore,
            force=force,
            comment=comment,
            packages=packages,
        )

    def parse_meta_package(
        meta_package_name: str, category_name: str, meta_package_dict: MetaPackageDict
    ) -> MetaPackage:
        package_specs_raw: Dict[PackageManagerName, PackageSpec] = {
            package_manager_name: parse_package_spec(
                meta_package_dict.get(package_manager_name, ""), package_manager_name
            )
            for package_manager_name in PACKAGE_MANAGER_NAMES
            if package_manager_name in meta_package_dict.keys()
        }
        return MetaPackage(
            name=meta_package_name,
            category=category_name,
            comment=meta_package_dict.get("comment"),
            ignore=meta_package_dict.get("ignore", False),
            package_specs=package_specs_raw,
        )

    def parse_category(
        category_name: str, category_packages: Dict[str, MetaPackageDict]
    ) -> List[MetaPackage]:
        return [
            parse_meta_package(package_name, category_name, package_dict)
            for package_name, package_dict in category_packages.items()
        ]

    return flatten(
        [
            parse_category(category_name, category_packages)
            for category_name, category_packages in config_dict.items()
        ]
    )
