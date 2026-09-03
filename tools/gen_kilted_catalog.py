#!/usr/bin/env python3
"""Generate extensions/commands/ros/data/kilted_variants.json from rosdistro.

Downloads the pinned rosdistro tag (same snapshot as recipes/ros-kilted) and the
kilted distribution cache (package.xml blobs), then expands packages-up-to
ros_core / ros_base / desktop.

Requires PyYAML:  pip install pyyaml
"""

from __future__ import annotations

import argparse
import io
import json
import tarfile
import urllib.request
from pathlib import Path
from xml.etree import ElementTree as ET

try:
    import yaml
except ImportError as exc:
    raise SystemExit("PyYAML is required: pip install pyyaml") from exc

REPO_ROOT = Path(__file__).resolve().parents[1]
ROSDISTRO_TAG = "kilted/2026-06-17"
CONAN_VERSION = "2026.06.17"
ROSDISTRO_URL = (
    f"https://github.com/ros/rosdistro/archive/refs/tags/{ROSDISTRO_TAG}.tar.gz"
)
CACHE_URL = "https://repo.ros2.org/rosdistro_cache/kilted-cache.yaml.gz"
VARIANT_SEEDS = {
    "core": "ros_core",
    "base": "ros_base",
    "desktop": "desktop",
}

DEPEND_TAGS = {
    "depend",
    "build_depend",
    "build_export_depend",
    "exec_depend",
    "buildtool_depend",
    "buildtool_export_depend",
}


def _download(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "ros-conan-catalog/1.0"})
    with urllib.request.urlopen(req) as resp:
        return resp.read()


def _index_and_distro_names(tarball: bytes) -> set[str]:
    """Package names listed in the pinned kilted/distribution.yaml."""
    names: set[str] = set()
    with tarfile.open(fileobj=io.BytesIO(tarball), mode="r:gz") as tar:
        distro_member = None
        for member in tar.getmembers():
            if member.name.endswith("/kilted/distribution.yaml"):
                distro_member = member
                break
        if distro_member is None:
            raise RuntimeError("kilted/distribution.yaml not found in rosdistro tarball")
        data = yaml.safe_load(tar.extractfile(distro_member))
    for repo in (data.get("repositories") or {}).values():
        release = repo.get("release") or {}
        packages = release.get("packages")
        if packages:
            names.update(packages)
        else:
            # Single-package repo: last path component of the release url, or skip.
            url = release.get("url") or ""
            if url:
                repo_name = url.rstrip("/").rsplit("/", 1)[-1]
                if repo_name.endswith(".git"):
                    repo_name = repo_name[:-4]
                if repo_name.endswith("-release"):
                    repo_name = repo_name[: -len("-release")]
                names.add(repo_name)
    return names


def _load_package_xml_map(cache_gz: bytes) -> dict[str, str]:
    import gzip

    cache = yaml.safe_load(gzip.decompress(cache_gz))
    release_package_xmls = cache.get("release_package_xmls") or {}
    if not release_package_xmls:
        raise RuntimeError("rosdistro cache has no release_package_xmls")
    return release_package_xmls


def _local_name(tag: str) -> str:
    return tag.split("}", 1)[-1]


def _direct_depends(package_xml: str) -> set[str]:
    root = ET.fromstring(package_xml)
    deps: set[str] = set()
    for child in list(root):
        if _local_name(child.tag) not in DEPEND_TAGS:
            continue
        name = (child.text or "").strip()
        if name:
            deps.add(name)
    return deps


def _closure(seed: str, xmls: dict[str, str], distro_names: set[str]) -> list[str]:
    seen: set[str] = set()
    stack = [seed]
    while stack:
        pkg = stack.pop()
        if pkg in seen:
            continue
        seen.add(pkg)
        xml = xmls.get(pkg)
        if not xml:
            continue
        for dep in _direct_depends(xml):
            if dep in distro_names or dep in xmls:
                stack.append(dep)
    return sorted(seen)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=REPO_ROOT / "extensions" / "commands" / "ros" / "data" / "kilted_variants.json",
    )
    args = parser.parse_args()

    print(f"Downloading {ROSDISTRO_URL}")
    tarball = _download(ROSDISTRO_URL)
    distro_names = _index_and_distro_names(tarball)
    print(f"Pinned distro lists {len(distro_names)} package names")

    print(f"Downloading {CACHE_URL}")
    xmls = _load_package_xml_map(_download(CACHE_URL))
    print(f"Cache has {len(xmls)} package.xml blobs")

    variants = {}
    for variant, seed in VARIANT_SEEDS.items():
        packages = _closure(seed, xmls, distro_names)
        variants[variant] = packages
        print(f"{variant} ({seed}): {len(packages)} packages")

    doc = {
        "distro": "kilted",
        "rosdistro_tag": ROSDISTRO_TAG,
        "conan_version": CONAN_VERSION,
        "variants": variants,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
