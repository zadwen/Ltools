#!/usr/bin/env bash
set -Eeuo pipefail
trap 'printf "[ERROR] Setup stopped at line %s. Fix the error above before retrying.\n" "$LINENO" >&2' ERR
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
usage() {
    cat <<'HELP'
Ltools 2 • by zadwen
Usage: ./setup.sh [doctor|repair|install|power-enable|power-disable] [options]
  doctor          Read-only diagnostics (default)
  repair          Repair existing launcher mapping; back up changed files
                  Options: --launcher PATH --plugin-dir PATH --dry-run
  install         Explain the upstream compatibility blocker
  power-enable    Enable supported power profiles on AC/battery (optional)
  power-disable   Remove Ltools v2 power automation
Run as your normal desktop user, without sudo. Privileged steps request sudo.
HELP
}
case "${1:-doctor}" in -h|--help|help) usage; exit 0;; esac
if (( EUID == 0 )); then
    echo 'Run this script as your normal desktop user, without sudo.' >&2
    exit 1
fi
command -v python3 >/dev/null || { echo 'Install Python 3 first: sudo apt install python3' >&2; exit 1; }
ACTION=${1:-doctor}
if (($#)); then shift; fi
case "$ACTION" in
    doctor|repair) exec python3 "$ROOT/ltools.py" "$ACTION" "$@" ;;
    install)
        cat >&2 <<'NOTICE'
Installation paused: this repository's LuaToolsLinux upstream uses a Python backend.
Millennium 3.0 removed Python plugin support. Installing current Millennium with
this old plugin does not produce a compatible setup.
Run ./setup.sh doctor for local file checks. Confirm your Millennium version
in its settings before selecting a compatible plugin/runtime combination.
Ltools does not automatically downgrade Millennium or claim to port this plugin.
See README: Millennium 3 compatibility.
NOTICE
        exit 1
        ;;
    power-enable|power-disable)
        (($# == 0)) || { usage; exit 2; }
        exec bash "$ROOT/scripts/power-install.sh" "$ACTION"
        ;;
    *) usage >&2; exit 2 ;;
esac
