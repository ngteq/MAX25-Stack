# AGENT-INDEX — Operations manual (MAX25-Stack)

**Repository:** MainAX25-Stack (MAX25-Stack)  
**Updated:** 2026-07-13  
**Purpose:** **Code + publication** in this repo. **All documentation work** — owner only in the **0-RESEARCH project** (`/home/akb/Code/0-RESEARCHES/`), never by agents here.

**Read order:** `AGENT-INDEX.md` (this file) → `AGENTS.md` → `docs/DEVELOPMENT.md` → `docs/README.md` (read-only reference)

**0-RESEARCH project:** `/home/akb/Code/0-RESEARCHES/` — **100 % of documentation** ([vault AGENT-INDEX](../0-RESEARCHES/AGENT-INDEX.md)). Background research jobs: vault §0.3 — operator approval required.

**Sibling:** [HyBBX AGENT-INDEX](../hyBBX/AGENT-INDEX.md)

---

## 0.0 SLAVE repository (this repo)

| Item | Value |
|------|--------|
| **Role** | **SLAVE** — job/work repository |
| **MASTER** | `/home/akb/Code/0-RESEARCHES/` — [vault AGENT-INDEX §0.6](../0-RESEARCHES/AGENT-INDEX.md#06-master-repository-static-rule) |
| **Publication** | Product code may ship; **documentation** only in MASTER (`projects/max25-stack/`) |
| **Cross-repo** | Must not influence HyBBX or other slaves; specs live in MASTER |
| **Agent delete repo** | **Forbidden** — operator only |

Agents: **code** in this repo when requested; **no** documentation here (§0.1 below + vault §0.5).

---

| In MAX25-Stack (agents) | **Not** in MAX25-Stack (agents) |
|-------------------------|----------------------------------|
| **Code** — stacks, daemon, plugins, scripts, tests, build | **Documentation work** — planning, roadmaps, architecture, scope, design write-ups |
| **Publication** — VERSION, release-check, example INI when **code** requires it | Proactive edits to `docs/` or stack `docs/` |
| Code comments; README only when user asks for a release note | Substituting `docs/` for the 0-RESEARCH project |

**Owner rule:** 100 % of documentation is written and maintained in **0-RESEARCH** (`0-RESEARCHES/`), **never** in MAX25-Stack by agents.

Existing `docs/` here are **frozen reference** unless the user explicitly requests a doc change tied to shipping code.

---

## 0. Publication standard (all projects)

Every persistent document — research notes, shipped repo docs, examples, agent guides — must be:

| Principle | Requirement |
|-----------|-------------|
| **Complete** | A reader can act without unstated context; link to SSoT for depth |
| **Compact** | No padding, duplicate essays, or version-history bloat in technical docs |
| **AI- and human-readable** | Clear headings, tables, lists; one topic per section; stable terminology |
| **Generic** | No personal names, handles, or site-private labels unless technically required |
| **Technical** | Facts, procedures, contracts — not meta about how documentation is produced |
| **Neutral wording** | State requirements in plain prose; do not cite undocumented internal policy names |

| Avoid | Use instead |
|-------|-------------|
| Personal or site-specific paths in examples | `$SRC`, `$PREFIX`, [docs/PATHS.md](docs/PATHS.md), `/dev/ttyS0`, `main.example.com` |
| Private nicknames in text | Operator, RF host, site config, reference device |
| “Rule X says…” without a shipped doc | Direct requirement in the same paragraph |
| Long investigations in `docs/` | Research vault `0-RESEARCHES/projects/max25-stack/` (§0.5) |

**Allowed exception:** A literal path, hostname, or git identity is permitted only when technically required (PATHS.md, CONTRIBUTING, protocol samples).

**Static development rule:** See `docs/DEVELOPMENT.md` § Publication standard.

---

## 0.2 Research vault governance (agents — read-only here)

| Topic | Spec |
|-------|------|
| **Inbound only / no deletion** | [0-RESEARCHES AGENT-INDEX §0.1](../0-RESEARCHES/AGENT-INDEX.md#01-vault-retention-research-vault-only) |
| **Automation (dedup, REGISTER)** | [§0.2](../0-RESEARCHES/AGENT-INDEX.md#02-automation--algorithmization) · `tools/vault-duplicate-check.sh` · `tools/vault-register-check.sh` |
| **Sole doc workspace** | [§0.5](../0-RESEARCHES/AGENT-INDEX.md#05-documentation-sole-workspace-static-rule) — all MAX25 documentation in `projects/max25-stack/` |

---

## 1. What belongs in this repo

| In MAX25-Stack (agents: code + publication) | Not in MAX25-Stack (agents) |
|---------------------------------------------|-----------------------------|
| Stacks, daemon, plugins, scripts, tests, CMake | **All documentation work** → owner in `0-RESEARCHES/` only |
| Shipped `docs/` — **read-only reference** unless user requests a release-tied edit | Research, roadmaps, scope drafts, architecture planning in `docs/` |
| Examples: `share/max25/`, `share/baycom/`, `share/hybbx/` when code needs them | Personal `local/` paths in committed examples |
| VERSION / release-check when publishing | Extending `docs/MERGE-REPORT.md` (archive only) |

**HyBBX:** external consumer — attach contract in `docs/HYBBX.md` + `share/hybbx/*.ini.example` only.

---

## 2. Mandatory workflow (code tasks)

```
1. SEARCH   — Existing code, plugin, or stack README? (§3)
2. CLASSIFY — Operator | architecture | plugin | protocol | stack (§4)
3. CODE     — Minimal diff; match conventions
4. VERIFY   — tests, release-check when publishing
```

**Rules:** Minimal diffs. Link `stacks/*/` READMEs — do not duplicate. **No documentation edits** unless user explicitly asks (release-tied). No commit/push unless the user asks.

---

## 3. SEARCH — Before writing

### 3.1 Quick routing

| Question | Read first |
|----------|------------|
| Agent rules | [AGENTS.md](../AGENTS.md) |
| Doc index | [docs/README.md](docs/README.md) |
| Path variables | [docs/PATHS.md](docs/PATHS.md) |
| Architecture / one-RF policy | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| **DEV-Levels roadmap (1–4)** | [docs/V2.0.0-SCOPE.md](docs/V2.0.0-SCOPE.md#dev-levels-roadmap-stack-wide) |
| Modular TCP/IP service | [docs/MODULAR-TCPIP-SERVER.md](docs/MODULAR-TCPIP-SERVER.md) |
| Device workflow | [docs/PLUGINS-DEVICE-MODEL.md](docs/PLUGINS-DEVICE-MODEL.md) |
| Full device list | [docs/DEVICES-LIST-FULL.md](docs/DEVICES-LIST-FULL.md) |
| Operator runbook | [docs/MAX25-OPERATOR-RUNBOOK.md](docs/MAX25-OPERATOR-RUNBOOK.md) |
| BayCom | [docs/BAYCOM.md](docs/BAYCOM.md) |
| CRDOP | [docs/CRDOP.md](docs/CRDOP.md), [stacks/crdop/docs/INDEX.md](stacks/crdop/docs/INDEX.md) |
| M25/1 protocol | [include/max25/protocol.md](include/max25/protocol.md) |
| Plugin registry | [plugins/manifest.yaml](plugins/manifest.yaml) |
| Stack implementation | `stacks/<name>/README.md` |
| Deep research | `0-RESEARCHES/projects/max25-stack/` |

### 3.2 Code / config search

```bash
rg -i "keyword" /home/akb/Code/MAX25-Stack --glob '*.{md,py,sh,yaml,ini.example}'
./scripts/discover-plugins.sh --json | rg -i "keyword"
```

---

## 4. CLASSIFY — Content type

| Type | Target | Also update |
|------|--------|-------------|
| New / changed device plugin | `plugins/devices/<id>/plugin.yaml`, `plugins/manifest.yaml` | `docs/DEVICES-LIST-FULL.md`, `share/clients/` if profile |
| M25/1 protocol change | `include/max25/protocol.md` | `docs/MAX25-CLIENT.md`, daemon tests |
| Operator procedure | Matching `docs/*.md` + `share/max25/*.example` | [docs/MAX25-OPERATOR-RUNBOOK.md](docs/MAX25-OPERATOR-RUNBOOK.md) if end-to-end |
| HyBBX attach | [docs/HYBBX.md](docs/HYBBX.md) | `share/hybbx/*.ini.example` |
| BayCom kernel path | [docs/BAYCOM.md](docs/BAYCOM.md) | `stacks/baycom-pr/docs/` for driver depth |
| TNC recovery | `stacks/tncs/docs/TNC-RECOVERY.md` | link from `docs/PACKET-RADIO.md` |
| CRDOP DSP / host spec | `stacks/crdop/docs/` | [docs/CRDOP.md](docs/CRDOP.md) summary only |
| Platform limits | [docs/PLATFORMS.md](docs/PLATFORMS.md) | [docs/FREEBSD-AX25.md](docs/FREEBSD-AX25.md) if *BSD |
| v1 / v2 scope | `docs/V1.0.0-SCOPE.md`, `docs/V2.0.0-SCOPE.md` (DEV-Level 1–4 roadmap) | `VERSION`, `release-check.sh` if release |
| Modular TCP/IP + platforms | [docs/MODULAR-TCPIP-SERVER.md](docs/MODULAR-TCPIP-SERVER.md), [docs/PLATFORMS.md](docs/PLATFORMS.md) | [docs/V2.0.0-SCOPE.md](docs/V2.0.0-SCOPE.md) |
| Investigation | `0-RESEARCHES/projects/max25-stack/` | vault INDEX |

---

## 5. WRITE — Shipped doc rules

### 5.1 Language

- **English only** in shipped docs, UI strings, examples, script output ([`.cursor/rules/english-only-project.mdc`](.cursor/rules/english-only-project.mdc))
- New source comments: English

### 5.2 Paths and examples

- Use [docs/PATHS.md](docs/PATHS.md): `$SRC`, `$PREFIX`, `$BUILD`
- Serial: `/dev/ttyS0`, `/dev/ttyUSB0` — not home directories
- Hostnames: `main.example.com`

### 5.3 Architecture constraints (when documenting behavior)

- **Linux daemon:** `max25d` + BayCom kernel + full RF lifecycle on Linux
- **One RF device per host** — see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **Standalone-first** — HyBBX attaches after prep
- **Official client:** `max25-terminal` only in core; third-party GUI via M25/1 welcome

### 5.4 Stack README rule

Detail lives in `stacks/<name>/README.md` — `docs/` links, does not copy.

---

## 6. REGISTER — After changes

| Change | Update |
|--------|--------|
| Plugin / device | `plugins/manifest.yaml`, `plugin.yaml`, `discover-plugins.sh` output |
| New doc file | [docs/README.md](docs/README.md), `scripts/release-check.sh` required list |
| M25/1 | `include/max25/protocol.md`, [docs/MAX25-CLIENT.md](docs/MAX25-CLIENT.md) |
| HyBBX contract | [docs/HYBBX.md](docs/HYBBX.md), `share/hybbx/` |
| v1 scope / devices | [docs/V1.0.0-SCOPE.md](docs/V1.0.0-SCOPE.md), [docs/DEVICES-LIST-FULL.md](docs/DEVICES-LIST-FULL.md) |
| Virtual netdev | [docs/NETDEV.md](docs/NETDEV.md) |
| Research finding | `0-RESEARCHES/projects/max25-stack/` + vault `INDEX.md` |

---

## 7. Task → action

| Task | Read | Write | Register |
|------|------|-------|----------|
| New device id | manifest, PLUGINS-DEVICE-MODEL | plugin.yaml + backend | manifest, DEVICES-LIST-FULL |
| TNC recovery change | TNC-RECOVERY.md, kiss_bridge | stacks/tncs + doc | vault note if investigation |
| BayCom operator step | BAYCOM.md, baycom-pr README | docs/BAYCOM.md | share/baycom example |
| Protocol field | protocol.md | protocol + MAX25-CLIENT | test_proto.py |
| FreeBSD port research | PLATFORMS, FREEBSD-AX25 | vault `projects/max25-stack/` | vault INDEX + `vault-register-check.sh` |

**Research vault tools** (when writing outside this repo): `0-RESEARCHES/tools/vault-duplicate-check.sh` before WRITE; `vault-register-check.sh` after.

---

## 8. Anti-patterns

| Do not | Do instead |
|--------|------------|
| Session logic in MAX25 | HyBBX |
| Open `/dev/tty*` from third-party client | M25/1 to `max25d` |
| Userspace serial + kernel BayCom on same UART | One owner — [docs/PACKET-RADIO.md](docs/PACKET-RADIO.md) |
| Research dumps in `docs/` | Research vault |
| Extend MERGE-REPORT.md | Current docs only |
| German in shipped user-facing text | English |

---

## 9. Meta files

| File | Role |
|------|------|
| **AGENT-INDEX.md** | This manual |
| **AGENTS.md** | Agent map + rules |
| **docs/DEVELOPMENT.md** | Toolchain, testing, doc duty |
| **docs/README.md** | Shipped doc index |
| **plugins/manifest.yaml** | Device registry |
| **CONTRIBUTING.md** | Human contributors |

---

## 10. Change log

| Date | Change |
|------|--------|
| 2026-07-13 | First version — aligned with research vault AGENT-INDEX |
| 2026-07-13 | §0.2 vault governance; code-first workflow; vault tools cross-link |
