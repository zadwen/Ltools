# LuaTools Linux setup

Portable installer for native Steam on x86_64 Ubuntu, Debian and Zorin OS. It installs Millennium 3.6.1 and an adapter for the archived LuaToolsLinux Python backend.

## Install on another PC

Install native Steam and open it once. Fully exit Steam, then run:

```bash
git clone https://github.com/zadwen/Ltools.git
cd Ltools
./setup.sh
```

Run as your normal desktop user. Enter your password into the terminal when sudo requests it. Flatpak and Snap Steam are unsupported. The installer supports the default Steam folders; set `STEAM_DIR` for another native installation.

Alternatively, copy this repository folder to the other PC and run `./setup.sh` there.

## Included compatibility changes

- Millennium is pinned to 3.6.1 and its archive is verified with SHA-256.
- LuaTools source is pinned to commit `b3fa04a28cef848187f4e816fcd8902be29e936e` of Star123451/LuaToolsLinux.
- A Lua backend launcher starts the Python service in a dedicated virtual environment, since Millennium 3 removed native Python backend support.
- The Store-page script uses `.millennium/Dist/webkit.js`. The previous external browser-script injection is removed.
- Steam's main `steamui/index.html` is never modified by this installer. The unsuccessful main-interface injection from troubleshooting is excluded.
- LuaTools is enabled without replacing your other Millennium settings.
- Existing plugin files, Millennium settings and system Millennium libraries are backed up under `~/.local/share/Ltools/backups/` (or `$XDG_DATA_HOME/Ltools/backups/`).

**Status:** the Store frontend adapter passes JavaScript syntax checks, and Steam and the Python service start on the original PC. Appearance and behavior of the LuaTools button still require confirmation. This is an experimental compatibility adapter, not an upstream-supported release.

## Dependencies

The installer installs `ca-certificates`, `curl`, `jq`, `git`, `tar`, `unzip`, `python3`, `python3-pip`, `python3-venv`, `libssl-dev:i386` and `libstdc++6:i386`, and enables i386 package architecture. Python packages are installed from the pinned upstream `requirements.txt` inside the plugin's `.venv` (including httpx, Beautiful Soup and ruamel.yaml).

Python remains necessary for this adapter; converting all LuaTools functionality to native Lua is not part of this change. The service listens on localhost port 38495, which must be available.

API keys, tokens, cookies, game manifests and personal settings are not copied from the original PC. Configure any required credentials locally after installation. ACCELA, SLSsteam and other external launchers are not installed or configured by this installer. Features requiring them need separate setup; the installer does not unlock or download games.

The old automatic CPU power changes and embedded credential have been removed from the installer. No username, graphics-card model or AC adapter name is hardcoded.

## Validate without installing

```bash
bash -n setup.sh
python3 -m unittest discover -s tests -v
```

Node.js is used by the validation tests when available; it is not needed to run the installed plugin. To troubleshoot an installation, check `/tmp/luatools_bridge.log` and Steam's `logs/cef_log.txt`. Do not share logs without checking for private data.
