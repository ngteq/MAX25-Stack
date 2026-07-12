"""MAX25 layout detection — dev checkout vs cmake install prefix."""
from __future__ import annotations

import configparser
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
    env_root = os.environ.get("MAX25_ROOT", "").strip()
    if env_root:
        paths.append(Path(env_root) / "local" / f"{device_id}-serial.env")
        paths.append(Path(env_root) / _STACKS / "tncs" / f"{device_id}-serial.env")
    cwd = os.environ.get("PWD", "").strip()
    if cwd:
        paths.append(Path(cwd) / "local" / f"{device_id}-serial.env")
    if prefix is not None:
        paths.append(prefix / _SHARE_MAX25 / "serial" / f"{device_id}-serial.env")
        paths.append(prefix / _SHARE_MAX25 / _STACKS / "tncs" / f"{device_id}-serial.env")
    paths.append(tree / "local" / f"{device_id}-serial.env")
    paths.append(tree / _STACKS / "tncs" / f"{device_id}-serial.env")
    return paths


def baycom_share_dir(tree: Path, prefix: Path | None) -> Path:
    if prefix is not None:
        installed = prefix / _SHARE_MAX25 / "baycom"
        if installed.is_dir():
            return installed
    return tree / "share" / "baycom"


_SITE_BAYCOM_INI = Path("/etc/baycom/baycom-pr.ini")
_SINGLE_SER12_EXAMPLE = "baycom-pr.pccom-ttyS0-only.ini.example"


def is_dual_baycom_ini(path: Path) -> bool:
    """True when profile lists more than one modem or name is 'dual'."""
    if not path.is_file():
        return False
    cp = configparser.ConfigParser()
    try:
        cp.read(path, encoding="utf-8")
    except OSError:
        return False
    if "profile" not in cp:
        return False
    prof = cp["profile"]
    name = prof.get("name", "").strip().lower()
    modem_ids = [x.strip() for x in prof.get("modems", "").split(",") if x.strip()]
    if len(modem_ids) > 1:
        return True
    return name == "dual"


def canonical_dual_baycom_example(
    device_id: str, tree: Path, prefix: Path | None
) -> Path | None:
    """Shipped dual-modem template for kernel-ser12 service mode."""
    if device_id not in ("baycom-ser12", "baycom-par96"):
        return None
    for candidate in (
        tree / _STACKS / "baycom-pr" / "config" / "examples" / "baycom-pr.dual.ini",
        stacks_dir(tree, prefix) / "baycom-pr" / "config" / "examples" / "baycom-pr.dual.ini",
    ):
        if candidate.is_file():
            return candidate
    site = _SITE_BAYCOM_INI
    if site.is_file() and is_dual_baycom_ini(site):
        return site
    return None


def canonical_single_baycom_example(
    device_id: str, tree: Path, prefix: Path | None
) -> Path | None:
    """Shipped single-modem template for kernel BayCom devices."""
    share = baycom_share_dir(tree, prefix)
    if device_id == "baycom-par96":
        for candidate in (
            share / "baycom-pr.par96-single.ini.example",
            tree / _STACKS / "baycom-pr" / "config" / "examples" / "baycom-pr.par96.ini",
            stacks_dir(tree, prefix) / "baycom-pr" / "config" / "examples" / "baycom-pr.par96.ini",
        ):
            if candidate.is_file():
                return candidate
        return None
    ser12 = share / _SINGLE_SER12_EXAMPLE
    if ser12.is_file():
        return ser12
    return None


def baycom_ini_candidates(device_id: str, tree: Path, prefix: Path | None) -> list[Path]:
    """Search order for baycom-pr.ini (local → site single → shipped example)."""
    paths: list[Path] = []
    env_ini = os.environ.get("BAYCOM_INI", "").strip()
    if env_ini:
        paths.append(Path(env_ini))
    env_root = os.environ.get("MAX25_ROOT", "").strip()
    if env_root:
        paths.append(Path(env_root) / "local" / "baycom-pr.ini")
    cwd = os.environ.get("PWD", "").strip()
    if cwd:
        paths.append(Path(cwd) / "local" / "baycom-pr.ini")
    paths.append(tree / "local" / "baycom-pr.ini")

    # Site INI before shipped example so operator edits in /etc win when single-modem.
    paths.append(_SITE_BAYCOM_INI)
    paths.append(Path("/etc/baycom/baycom-pr-single.ini"))

    canonical = canonical_single_baycom_example(device_id, tree, prefix)
    if canonical is not None:
        paths.append(canonical)

    if prefix is not None:
        paths.append(prefix / _SHARE_MAX25 / "baycom" / _SINGLE_SER12_EXAMPLE)
        paths.append(prefix / "etc" / "baycom" / "baycom-pr.ini.example")

    paths.append(tree / _STACKS / "baycom-pr" / "config" / "baycom-pr.ini")
    return paths


def resolve_baycom_profile(
    profile: str,
    device_id: str,
    tree: Path,
    prefix: Path | None,
) -> Path | None:
    """Resolve named profile: single (default) or dual (service mode)."""
    name = profile.strip().lower()
    if name == "dual":
        return canonical_dual_baycom_example(device_id, tree, prefix)
    if name in ("single", "default", ""):
        return resolve_baycom_ini(device_id, tree, prefix)
    return None


def resolve_baycom_ini(
    device_id: str,
    tree: Path,
    prefix: Path | None,
    explicit: str = "",
) -> Path | None:
    """Return first existing baycom-pr.ini path, or None.

    Skips dual-modem /etc/baycom/baycom-pr.ini unless explicit (or env BAYCOM_INI).
    """
    if explicit:
        path = Path(explicit)
        return path if path.is_file() else None
    for candidate in baycom_ini_candidates(device_id, tree, prefix):
        if not candidate.is_file():
            continue
        if candidate == _SITE_BAYCOM_INI and is_dual_baycom_ini(candidate):
            continue
        return candidate
    return None
