#!/usr/bin/env bash
set -Eeuo pipefail
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
command -v systemctl >/dev/null || { echo 'systemd is required.' >&2; exit 1; }
case "${1:-}" in
    power-enable)
        command -v powerprofilesctl >/dev/null || { echo 'Install power-profiles-daemon first, then retry.' >&2; exit 1; }
        powerprofilesctl get >/dev/null
        if [[ -e /etc/udev/rules.d/99-power-profile.rules ]]; then
            echo 'Legacy power rule exists. Follow the README migration steps first.' >&2
            exit 1
        fi
        if systemctl is-active --quiet tlp.service || systemctl is-active --quiet auto-cpufreq.service; then
            echo 'Another power manager is active (TLP or auto-cpufreq). Resolve that conflict first.' >&2
            exit 1
        fi
        sudo install -D -m 755 "$ROOT/power-profile.py" /usr/local/libexec/ltools-power-profile
        sudo install -m 644 "$ROOT/ltools-power.service" /etc/systemd/system/ltools-power.service
        sudo install -m 644 "$ROOT/ltools-power.timer" /etc/systemd/system/ltools-power.timer
        sudo systemctl daemon-reload
        sudo systemctl start ltools-power.service
        sudo systemctl enable --now ltools-power.timer
        echo 'Power automation enabled. Checks every 30 seconds; unsupported performance falls back to balanced.'
        ;;
    power-disable)
        sudo systemctl disable --now ltools-power.timer
        sudo systemctl stop ltools-power.service
        sudo rm -f /etc/systemd/system/ltools-power.service /etc/systemd/system/ltools-power.timer /usr/local/libexec/ltools-power-profile
        sudo systemctl daemon-reload
        echo 'Ltools v2 power automation removed. Select your preferred profile in desktop settings.'
        ;;
    *) echo 'Expected power-enable or power-disable.' >&2; exit 2 ;;
esac
