# CRDOP license and usage rights

**CRDOP** (MAX25-SoftModem) is **free software** under the **GNU General Public License version 3** (GPL-3.0-or-later).

License files:

| File | Scope |
|------|-------|
| [stacks/crdop/LICENSE](../LICENSE) | CRDOP subproject |
| [LICENSE](../../../LICENSE) | MainAX25-Stack repository root |

---

## Summary (not legal advice)

GPLv3 grants everyone — **private individuals and commercial entities** — the right to:

| Right | Meaning |
|-------|---------|
| **Use** | Run CRDOP for any purpose (personal, club, business, government) |
| **Study** | Read and learn from source code |
| **Modify** | Change code to suit your needs |
| **Distribute** | Share originals or modified versions |
| **Commercial use** | Sell services, products, or support built on CRDOP |

**Copyleft obligation:** When you **distribute** CRDOP (or a combined work based on it), you must:

1. Provide **corresponding source** (or a written offer valid ≥ 3 years).
2. License derivatives under **GPLv3** (or later, per "or later" clause).
3. Preserve copyright notices and license text.
4. Document changes if you modify files.
5. Pass through patent retaliation and anti-tivoization terms as GPLv3 requires.

**No warranty:** Software is provided **AS IS** — no implied fitness for a particular purpose.

---

## Private use

| Scenario | Obligation |
|----------|------------|
| Run CRDOP on your own computer | None beyond GPLv3 acceptance |
| Modify for personal use only | No distribution → no source-offer obligation |
| Internal company use (no binary redistribution) | Same as private — no copyleft trigger until you distribute |

---

## Commercial use

| Scenario | Obligation |
|----------|------------|
| Sell pre-built PCs with CRDOP installed | Provide source (or written offer) to recipients |
| Ship hardware interface **with** CRDOP binaries | GPL applies to distributed software; hardware schematics you create separately may use another license if they are not a derivative of the GPL code |
| SaaS / hosted service (no binary to users) | AGPL would impose network copyleft — **CRDOP is GPL, not AGPL**; consult counsel for your deployment model |
| OEM integration in a product | Ensure GPL compliance for all distributed GPL components; document how users obtain source |

**Practical path:** Include `LICENSE`, offer source at your support URL or ship `stacks/crdop/` tree, and state "based on CRDOP (GPLv3)".

---

## Combined works (MAX25-Stack)

MAX25-Stack bundles CRDOP with daemon, terminal, and plugins. Distribution of the **combined stack** triggers GPLv3 obligations for the GPL-licensed portions. Other components may carry their own licenses — check root `LICENSE` and per-directory notices.

| Component | Typical license |
|-----------|-----------------|
| `stacks/crdop/` | GPL-3.0-or-later |
| MAX25 daemon / terminal | GPL-3.0-or-later (repository default) |

---

## What you may not do

| Restriction | Reason |
|-------------|--------|
| Relicense CRDOP under proprietary terms | GPLv3 copyleft |
| Remove copyright / license notices | GPLv3 §4 |
| Imply warranty or liability from authors | GPLv3 §15–16 |
| Distribute without source (when distributing binaries) | GPLv3 §6 |

Patent suits against GPL users can terminate your license (GPLv3 §8).

---

## ARDOP-plugin (separate)

**ARDOP-plugin** is an optional MAX25-Stack registry entry — **not** part of the CRDOP GPLv3 tree.

| Item | Policy |
|------|--------|
| CRDOP coupling | **None** — third-party ARDOP host software |
| Registry | [plugins/external/ardop/README.md](../../../plugins/external/ardop/README.md) |

CRDOP GPLv3 obligations apply to **CRDOP code**, not to operator ARDOP host software.

---

## Contributor grants

By contributing to `stacks/crdop/`, you agree that contributions are licensed under **GPL-3.0-or-later**, consistent with the repository [CONTRIBUTING.md](../../../CONTRIBUTING.md).

---

## Full license text

- Online: <https://www.gnu.org/licenses/gpl-3.0.html>
- In tree: [stacks/crdop/LICENSE](../LICENSE) · [LICENSE](../../../LICENSE)

---

## Related

| Doc | Topic |
|-----|--------|
| [docs/CRDOP.md](../../../docs/CRDOP.md) | Project rule §5 License |
| [INDEX.md](INDEX.md) | Documentation index |
