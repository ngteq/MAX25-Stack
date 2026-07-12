# Merge Report — MainAX25-Stack (MAX25-Stack)

Date: 2026-07-12

**MAX25** = **Main AX.25** — the repo directory remains `MAX25-Stack/`.

## Workspace state before merge

| Path | State |
|------|-------|
| `/home/akb/Code/MAX25-Stack/` | Empty directory (new unified MainAX25 repo) |
| `/home/akb/Code/TNCs-Stack/` | 70 files — TNC2C operator stack |
| `/home/akb/Code/pc-com/` | 173 files — **baycom_pr-Stack** (BayCom PR-Stack) |
| `/home/akb/Code/hyBBX/` | External consumer — not merged |

**Note:** `baycom_pr-Stack` does not exist as a separate directory. It is **`pc-com`** locally and [ngteq/BayCom_PR-Stack](https://github.com/ngteq/BayCom_PR-Stack) upstream.

## Merge operations

### 1. TNCs-Stack → `stacks/tncs/`

```bash
rsync -a --exclude='.git' --exclude='__pycache__' \
  /home/akb/Code/TNCs-Stack/ → MainAX25-Stack/stacks/tncs/
```

**Included:** All tools (`tnc2c-*`), docs, `hybbx-*.ini`, `research/`, images, Makefile.

**Excluded:** `.git`, `__pycache__`

**Size:** ~11 MB, ~70 files

**Key content preserved:**

- TNC2C boot-wait, health, integration test
- PK-TNC2 boot-wait (`pktnc2-*`)
- HyBBX dual INI (`hybbx-dual.ini`)
- Operator docs (`docs/TNC-INVENTORY.md`, `HYBBX-TNC2C.md`, …)

### 2. baycom_pr-Stack (pc-com) → `stacks/baycom-pr/`

```bash
rsync -a --exclude='.git' --exclude='.cursor' --exclude='research' \
  /home/akb/Code/pc-com/ → MainAX25-Stack/stacks/baycom-pr/
```

**Included:** `baycom-pr-ctl`, config templates, tools, docs, scripts, systemd unit.

**Excluded:** `.git`, `.cursor`, `research/` (per baycom AGENTS.md — not for publication)

**Size:** ~728 KB

**Key content preserved:**

- Full `baycom-pr-ctl` lifecycle
- INI examples (CB, HAM, dual, par96)
- `docs/PLUGIN.md` HyBBX contract
- C tools + Python validators

## New structure created (not from either stack)

| Path | Purpose |
|------|---------|
| `plugins/manifest.yaml` | Plugin registry |
| `plugins/betriebsform/{standalone,service,hybbx-edge}/` | Operating mode plugins |
| `plugins/hardware/{tncs,modems}/` | Hardware group plugins |
| `plugins/devices/{tnc2c,pktnc2,baycom-*}/` | Device plugins |
| `scripts/{max25-ctl,discover-plugins,build-all}.sh` | Unified automation |
| `share/hybbx/*.ini.example` | HyBBX Secondary snippets |
| `docs/{ARCHITECTURE,HYBBX,MERGE-REPORT}.md` | Top-level documentation |
| `Makefile`, `README.md`, `AGENTS.md` | Repo entry points |

## Conflicts / decisions

| Item | Decision |
|------|----------|
| Repo name | **MainAX25-Stack (MAX25-Stack)** — Main AX.25 umbrella; source repos unchanged |
| baycom_pr path | Mapped to `stacks/baycom-pr/` (clearer than `pc-com`) |
| HyBBX source | **Not vendored** — referenced as external plugin consumer |
| Git history | **Not merged** — file copy only (per constraint: no commits) |
| `research/` | Kept in tncs; excluded from baycom-pr copy |
| Duplicate tnc2c-old | **Not merged** — superseded by TNCs-Stack |

## Blockers / open items

| Item | Status |
|------|--------|
| PK-TNC2 hardware (Unit B) | Planned — port/baud TBD |
| RF live packet (TNC2C) | Not tested — tools ready |
| `baycom-par96`, `baycom-kiss` device plugins | Scaffold only |
| Auto-generate devices from `modems.ini` | Not implemented — next step |
| Git init in MainAX25-Stack (MAX25-Stack) | Not done — user did not request commit |

## Verification

```bash
cd MainAX25-Stack   # directory: MAX25-Stack/
make all          # builds tncs + baycom-pr C tools
make plugins      # lists plugin.yaml count + discovery table
make test         # baycom-pr offline QA (+ tncs probe if built)
```

## Source repo pointers (unchanged on disk)

| Original | Still at |
|----------|----------|
| TNCs-Stack | `/home/akb/Code/TNCs-Stack/` |
| baycom_pr-Stack | `/home/akb/Code/pc-com/` |
| HyBBX | `/home/akb/Code/hyBBX/` |

MainAX25-Stack (MAX25-Stack) is a **unified working copy**; originals remain for independent development until explicitly deprecated.
