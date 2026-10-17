#!/usr/bin/env bash
set -euo pipefail
repo_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
if [[ ${EUID} -eq 0 ]]; then echo 'Run as your desktop user; sudo is requested only for system packages.' >&2; exit 1; fi
if [[ $(uname -m) != x86_64 ]]; then echo 'Only x86_64 Linux is supported.' >&2; exit 1; fi
command -v apt-get >/dev/null || { echo 'This installer supports Ubuntu, Debian and Zorin OS.' >&2; exit 1; }
if pgrep -f '^.*/ubuntu12_32/steam( |$)' >/dev/null; then echo 'Fully exit Steam before installing.' >&2; exit 1; fi
sudo dpkg --add-architecture i386
sudo apt-get update
sudo apt-get install -y ca-certificates curl jq git tar unzip python3 python3-pip python3-venv libssl-dev:i386 libstdc++6:i386
steam_dir=${STEAM_DIR:-}
if [[ -z $steam_dir ]]; then
 for candidate in "$HOME/.local/share/Steam" "$HOME/.steam/steam"; do
  if [[ -f $candidate/steam.sh ]]; then steam_dir=$(realpath "$candidate"); break; fi
 done
fi
[[ -n $steam_dir && -f $steam_dir/steam.sh ]] || { echo 'Install native Steam and launch it once first. Flatpak/Snap Steam is unsupported.' >&2; exit 1; }
work_dir=$(mktemp -d)
trap 'rm -rf -- "$work_dir"' EXIT
# Pin the inspected Millennium release and verify its archive before installing.
version=3.6.1
curl -fL --retry 3 "https://github.com/SteamClientHomebrew/Millennium/releases/download/v${version}/millennium-v${version}-linux-x86_64.tar.gz" -o "$work_dir/millennium.tar.gz"
printf '%s  %s\n' 0215a19779ad928a53c5e947773063692ad40ab5a179ba119686de5150fbb763 "$work_dir/millennium.tar.gz" | sha256sum -c -
backup_dir="${XDG_DATA_HOME:-$HOME/.local/share}/Ltools/backups/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$backup_dir"
if [[ -d /usr/lib/millennium ]]; then sudo cp -a /usr/lib/millennium "$backup_dir/system-millennium"; fi
sudo tar -xzf "$work_dir/millennium.tar.gz" -C / ./usr/lib/millennium/
mkdir -p "$steam_dir/ubuntu12_32" "$steam_dir/ubuntu12_64"
sudo chmod +x /usr/lib/millennium/libmillennium_pvs64 /usr/lib/millennium/libmillennium_luavm_x86
ln -sfn /usr/lib/millennium/libmillennium_bootstrap_x86.so "$steam_dir/ubuntu12_32/libXtst.so.6"
ln -sfn /usr/lib/millennium/libmillennium_bootstrap_hhx64.so "$steam_dir/ubuntu12_64/libXtst.so.6"
ln -sfn /usr/lib/millennium/libmillennium_hhx64.so "$steam_dir/ubuntu12_64/libmillennium_hhx64.so"
# Fetch source, never this PC's keys, tokens, cached manifests or settings.
commit=b3fa04a28cef848187f4e816fcd8902be29e936e
curl -fL --retry 3 "https://github.com/Star123451/LuaToolsLinux/archive/${commit}.tar.gz" -o "$work_dir/luatools.tar.gz"
mkdir "$work_dir/source"
tar -xzf "$work_dir/luatools.tar.gz" -C "$work_dir/source" --strip-components=1
python3 "$repo_dir/scripts/install_plugin.py" --source "$work_dir/source" --steam "$steam_dir" --backup "$backup_dir"
printf '\nInstalled. Start Steam and test LuaTools on a game Store page.\nBackup: %s\n' "$backup_dir"
