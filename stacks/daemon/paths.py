"""MAX25 layout detection — dev checkout vs cmake install prefix."""
from __future__ import annotations

import os
from pathlib import Path

_MANIFEST = Path("plugins/manifest.yaml")
_SHARE_MAX25 = Path("share/max25")
_STACKS = Path("stacks")


def _repo_from_daemon_dir(here: Path) -> Path | None:
    if here.name == "daemon" and (here.parent / "tncs").is_dir():
        repo = here.parent.parent
        if (repo / _MANIFEST).is_file():
            return repo
    return None


def _prefix_from_bindir(bindir: Path) -> Path | None:
    prefix = bindir.parent
    if (prefix / _SHARE_MAX25).is_dir() and not (prefix / _MANIFEST).is_file():
        return prefix
    return None


def resolve_layout(exe: Path) -> tuple[Path, Path | None]:
    """Return (tree_root, install_prefix).

    tree_root is the repo root in dev, or MAX25_ROOT / prefix when installed.
    install_prefix is set when exe lives under PREFIX/bin, else None.
    """
    exe = exe.resolve()
    here = exe.parent

    repo = _repo_from_daemon_dir(here)
    if repo is not None:
        return repo, None

    prefix = _prefix_from_bindir(here)
    if prefix is not None:
        tree = Path(os.environ.get("MAX25_ROOT", str(prefix)))
        return tree, prefix

    if (here.parent / _MANIFEST).is_file():
        return here.parent, None

    return exe.parents[2], None


def share_max25_dir(tree: Path, prefix: Path | None) -> Path:
    if prefix is not None:
        share = prefix / _SHARE_MAX25
        if share.is_dir():
            return share
    return tree / _SHARE_MAX25


def stacks_dir(tree: Path, prefix: Path | None) -> Path:
    tree_stacks = tree / _STACKS
    if tree_stacks.is_dir():
        return tree_stacks
    if prefix is not None:
        installed = prefix / _SHARE_MAX25 / _STACKS
        if installed.is_dir():
            return installed
    return tree_stacks


def ctl_path(tree: Path, prefix: Path | None, exe: Path) -> Path:
    if prefix is not None:
        sibling = exe.resolve().parent / "max25-ctl"
        if sibling.is_file():
            return sibling
    script = tree / "scripts" / "max25-ctl"
    if script.is_file():
        return script
    if prefix is not None:
        return prefix / "bin" / "max25-ctl"
    return script


def default_ini_candidates(tree: Path, prefix: Path | None) -> list[Path]:
    candidates: list[Path] = []
    env_ini = os.environ.get("MAX25D_INI", "").strip()
    if env_ini:
        candidates.append(Path(env_ini))
    candidates.append(Path("/etc/max25/max25d.ini"))
    candidates.append(share_max25_dir(tree, prefix) / "max25d.ini.example")
    if prefix is None or tree != prefix:
        candidates.append(tree / _SHARE_MAX25 / "max25d.ini.example")
    return candidates


def serial_env_candidates(device_id: str, tree: Path, prefix: Path | None) -> list[Path]:
    paths: list[Path] = [Path(f"/etc/max25/{device_id}-serial.env")]
    if prefix is not None:
        paths.append(prefix / _SHARE_MAX25 / "serial" / f"{device_id}-serial.env")
        paths.append(prefix / _SHARE_MAX25 / _STACKS / "tncs" / f"{device_id}-serial.env")
    env_root = os.environ.get("MAX25_ROOT", "").strip()
    if env_root:
        paths.append(Path(env_root) / _STACKS / "tncs" / f"{device_id}-serial.env")
    paths.append(tree / _STACKS / "tncs" / f"{device_id}-serial.env")
    return paths
