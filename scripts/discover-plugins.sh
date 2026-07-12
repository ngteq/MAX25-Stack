#!/usr/bin/env bash
# MainAX25-Stack (MAX25-Stack) — list registered plugins from manifest.yaml + on-disk plugin.yaml files.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MANIFEST="${ROOT}/plugins/manifest.yaml"
JSON=0

usage() {
  cat <<'EOF'
Usage: discover-plugins.sh [--json] [--type TYPE] [--id ID]

  --json       Machine-readable output (one JSON object per line)
  --type TYPE  Filter: hardware | device
  --id ID      Show single plugin by id
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --json) JSON=1; shift ;;
    --type) TYPE_FILTER="${2:-}"; shift 2 ;;
    --id) ID_FILTER="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 1 ;;
  esac
done

if [[ ! -f "$MANIFEST" ]]; then
  echo "manifest not found: $MANIFEST" >&2
  exit 1
fi

emit_plugin() {
  local type="$1" id="$2" path="$3" extra="${4:-}"
  local full="${ROOT}/plugins/${path}"
  local yaml="${full}/plugin.yaml"
  local label="" status="" hybbx=""

  if [[ -f "$yaml" ]]; then
    label=$(grep -E '^label:' "$yaml" 2>/dev/null | head -1 | sed 's/^label:[[:space:]]*//' || true)
    status=$(grep -E '^status:' "$yaml" 2>/dev/null | head -1 | sed 's/^status:[[:space:]]*//' || true)
    hybbx=$(grep -E '^(hybbx_plugin|plugin):' "$yaml" 2>/dev/null | head -1 | sed 's/^[^:]*:[[:space:]]*//' || true)
  fi

  if [[ -n "${TYPE_FILTER:-}" && "$type" != "$TYPE_FILTER" ]]; then return; fi
  if [[ -n "${ID_FILTER:-}" && "$id" != "$ID_FILTER" ]]; then return; fi

  if [[ "$JSON" -eq 1 ]]; then
    printf '{"type":"%s","id":"%s","path":"plugins/%s","label":"%s","status":"%s","hybbx":"%s"%s}\n' \
      "$type" "$id" "$path" "$label" "$status" "$hybbx" "$extra"
  else
    printf '%-14s %-18s %-30s %s\n' "$type" "$id" "plugins/$path" "${label:-—}"
  fi
}

if [[ "$JSON" -eq 0 && -z "${ID_FILTER:-}" ]]; then
  printf '%-14s %-18s %-30s %s\n' "TYPE" "ID" "PATH" "LABEL"
  printf '%s\n' "--------------------------------------------------------------------------------"
fi

# Parse manifest sections (simple line-based — no PyYAML dependency)
section=""
while IFS= read -r line || [[ -n "$line" ]]; do
  line="${line%%#*}"
  line="${line%"${line##*[![:space:]]}"}"
  [[ -z "$line" ]] && continue

  case "$line" in
    betriebsform:) section=""; continue ;;
    hardware:) section=hardware; continue ;;
    devices:) section=device; continue ;;
    schema_version:*|stack:*|description:*) continue ;;
  esac

  [[ -z "$section" ]] && continue

  if [[ "$line" =~ ^[[:space:]]*-[[:space:]]+id:[[:space:]]*(.+)$ ]]; then
    cur_id="${BASH_REMATCH[1]}"
    cur_path=""
    continue
  fi
  if [[ -n "${cur_id:-}" && "$line" =~ ^[[:space:]]+path:[[:space:]]*(.+)$ ]]; then
    cur_path="${BASH_REMATCH[1]}"
    emit_plugin "$section" "$cur_id" "$cur_path"
    cur_id=""
  fi
done < "$MANIFEST"

# Also scan for plugin.yaml not in manifest (future auto-gen)
while IFS= read -r yaml; do
  dir="$(dirname "$yaml")"
  rel="${dir#${ROOT}/plugins/}"
  id="$(grep -E '^id:' "$yaml" | head -1 | sed 's/^id:[[:space:]]*//' || basename "$dir")"
  type="$(grep -E '^type:' "$yaml" | head -1 | sed 's/^type:[[:space:]]*//' || echo unknown)"
  # Skip if already emitted via manifest for same id+type would duplicate — acceptable for scaffold
done < <(find "${ROOT}/plugins" -name plugin.yaml -not -path '*/betriebsform/*' 2>/dev/null | sort)
