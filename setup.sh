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
  install         Install prerequisites and open the upstream installer menu
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
        (($# == 0)) || { usage; exit 2; }
        [[ -t 0 && -t 1 ]] || { echo 'Install requires an interactive terminal.' >&2; exit 1; }
        command -v apt-get >/dev/null || { echo 'Automatic installation supports Zorin/Ubuntu/Debian only. Use doctor or repair on other distributions.' >&2; exit 1; }
        echo 'Close Steam before continuing. The upstream menu controls which components are installed.'
        echo 'Option 3 installs only ACCELA/SLSsteam; it does not install the LuaTools plugin.'
        read -r -p 'Install dependencies and launch the third-party installer? [y/N] ' answer
        [[ "$answer" =~ ^[Yy]$ ]] || exit 0
        sudo apt-get update
        sudo apt-get install -y curl ca-certificates git jq unzip python3-venv python3-pip
        tmp=$(mktemp -d)
        trap 'rm -rf -- "$tmp"' EXIT
        # Pin this entry script. Its own downstream downloads are managed by upstream.
        revision=b3fa04a28cef848187f4e816fcd8902be29e936e
        curl --fail --location --show-error --silent --retry 3 --connect-timeout 15 --max-time 180 \
            "https://raw.githubusercontent.com/Star123451/LuaToolsLinux/$revision/install.sh" -o "$tmp/install.sh"
        printf '%s  %s\n' '25ac4c760d10bcd597e848fc075bcb5fd8ce26dd9758f63837327f05d4a1d551' "$tmp/install.sh" | sha256sum --check --status
        bash -n "$tmp/install.sh"
        bash "$tmp/install.sh"
        echo 'Upstream installer exited. Checking the actual installed components...'
        python3 "$ROOT/ltools.py" doctor
        echo 'To repair the detected launcher mapping, run: ./setup.sh repair'
        ;;
    power-enable|power-disable)
        (($# == 0)) || { usage; exit 2; }
        exec bash "$ROOT/scripts/power-install.sh" "$ACTION"
        ;;
    *) usage >&2; exit 2 ;;
esac
