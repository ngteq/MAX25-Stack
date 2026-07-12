# shellcheck shell=bash
# Load station serial env for TNC boot-wait (tnc2c | pktnc2).
# Sourced by tnc2c-boot-wait.sh / pktnc2-boot-wait.sh — do not execute directly.
#
# Search order (first match wins):
#   /etc/max25/<id>-serial.env
#   $MAX25_ROOT/local/<id>-serial.env
#   $PWD/local/<id>-serial.env          (cwd when start script runs)
#   <checkout>/local/<id>-serial.env    (walk up from script dir)
#   $PREFIX/share/max25/stacks/tncs/<id>-serial.env

load_serial_env() {
  local device_id="${1:?device_id required}"
  local script_dir="${2:?script_dir required}"
  local env_name="${device_id}-serial.env"
  local candidates=()
  local p dir

  candidates+=("/etc/max25/${env_name}")

  if [[ -n "${MAX25_ROOT:-}" ]]; then
    candidates+=("${MAX25_ROOT}/local/${env_name}")
    candidates+=("${MAX25_ROOT}/stacks/tncs/${env_name}")
  fi

  if [[ -n "${PWD:-}" ]]; then
    candidates+=("${PWD}/local/${env_name}")
    candidates+=("${PWD}/stacks/tncs/${env_name}")
  fi

  dir="${script_dir}"
  while [[ "${dir}" != "/" ]]; do
    candidates+=("${dir}/local/${env_name}")
    candidates+=("${dir}/stacks/tncs/${env_name}")
    local parent
    parent="$(dirname "${dir}")"
    [[ "${parent}" == "${dir}" ]] && break
    dir="${parent}"
  done

  candidates+=("${script_dir}/${env_name}")

  local prefix="${script_dir}"
  for _ in 1 2 3 4; do
    prefix="$(dirname "${prefix}")"
    candidates+=("${prefix}/share/max25/stacks/tncs/${env_name}")
  done

  for p in "${candidates[@]}"; do
    if [[ -f "${p}" ]]; then
      # shellcheck source=/dev/null
      source "${p}"
      SERIAL_ENV_FILE="${p}"
      return 0
    fi
  done
  SERIAL_ENV_FILE=""
  return 1
}

apply_tnc2c_env() {
  export TNC_DEV="${TNC2C_DEV:-${TNC_DEV:-/dev/ttyS4}}"
  export TNC_BAUD="${TNC2C_BAUD:-${TNC_BAUD:-19200}}"
  export TNC_LINE="${TNC2C_LINE:-${TNC_LINE:-8n1}}"
}

apply_pktnc2_env() {
  export TNC_DEV="${PKTNC2_DEV:-${TNC_DEV:-/dev/ttyS5}}"
  export TNC_BAUD="${PKTNC2_BAUD:-${TNC_BAUD:-9600}}"
  export TNC_LINE="${PKTNC2_LINE:-${TNC_LINE:-8n1}}"
}
