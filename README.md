# Ltools 2 — Linux gaming setup & repair

**by zadwen** • Zorin OS / Ubuntu / Debian • Bash + Python 3.9+

Ltools helps diagnose and repair the connection between an existing LuaTools
plugin and its installed launcher. It also offers an interactive upstream
installer and optional AC/battery power profiles. Run it as your regular desktop
user, **not with `sudo`**. Individual system changes request sudo themselves.

## Start here: fix an existing installation

Close Steam, then run:

```bash
git clone https://github.com/zadwen/Ltools.git
cd Ltools
./setup.sh doctor
./setup.sh repair --dry-run
./setup.sh repair
```

Restart Steam afterward. `doctor` is read-only and returns exit code 1 if checks
need attention; this is a diagnostic result, not a crash. No arguments runs doctor.
It never prints settings values or API keys.

If more than one launcher or plugin installation exists, select the intended one:

```bash
./setup.sh repair \
  --plugin-dir "$HOME/.local/share/millennium/plugins/luatools" \
  --launcher "$HOME/.local/share/ACCELA/ACCELA.AppImage"
```

Use the actual executable path on your PC. Bifrost and ACCELA's `run.sh` are also
detected. A valid saved custom launcher is preserved. Missing executables and
unknown plugin schemas produce an actionable error instead of a bogus mapping.

## What was fixed

- Removed hardcoded `/home/anas` paths and recursive ownership changes.
- Replaced the unused `Steam/config/luatools_config.json` mapping with the current
  plugin's `backend/data/launcher_path.txt`, after checking the installed schema.
- Removed the embedded API credential. **Revoke/regenerate the previously
  published Hubcap key. Removing it here does not remove it from Git history.**
- Stopped overwriting ACCELA settings, credentials and post-processing preferences.
- Added private timestamped backups and atomic replacement of launcher mappings.
- Replaced unconditional success messages with failure propagation and diagnostics.
- Download the upstream entry script to a file, verify its pinned SHA-256, then run
  it with terminal input available. No `curl | bash` in the Ltools wrapper.
- Removed the instruction to blindly choose option 3: upstream option 3 installs
  ACCELA/SLSsteam only, not the LuaTools plugin.
- Replaced direct CPU governor writes and the hardcoded `AC0` assumption with
  optional supported power-profiles-daemon profiles.

## LuaTools does not appear in Steam

A working external launcher does not mean Steam has loaded LuaTools. Run doctor
first: it recognizes legacy `LuaToolsLinux` folders, custom names identified by
`plugin.json`, Steam-relative plugin locations and `XDG_DATA_HOME`. It reports
partial installations, missing frontend/backend files, and Millennium loader
installation evidence separately. It cannot confirm plugin activation from disk.

1. In Steam, check **Steam > Millennium > Plugins** for LuaTools and enable it
   if present. If Millennium itself is missing, fix the loader first.
2. The old setup's instruction to choose **option 3** installs ACCELA/SLSsteam
   only. It skips the LuaTools plugin. Run `./setup.sh install` and choose the
   upstream **Install/Reinstall LuaTools plugin** option (currently 2); this
   upstream flow also checks Millennium. Review its prompts before continuing.
3. Fully exit Steam, including the tray icon, and restart it. If the plugin still
   fails, fully close Steam again and launch `steam -dev` from a terminal.
   Inspect the LuaTools/Millennium errors; redact any credentials before sharing.
4. Logs are normally in `~/.local/share/millennium/logs`. Startup errors or
   version incompatibility require those logs; launcher repair alone will not
   fix them. Ltools does not automatically move or delete duplicate plugins.

References: [Millennium file locations](https://docs.steambrew.app/users/getting-started/structure),
[plugin settings](https://docs.steambrew.app/users/guides/installing-addons),
[startup troubleshooting](https://docs.steambrew.app/users/getting-started/troubleshooting).

## New installation / upstream repair menu

```bash
./setup.sh install
```

This installs prerequisites using apt and opens the upstream menu. Review the
component names and select what you need. Upstream may ask for additional sudo
operations. Ltools does not automatically choose, remove Steam, or change sandbox
permissions. Native Steam is the integration target; Flatpak and Snap installations
are reported by diagnostics and need separate upstream compatibility review.

The entry script is pinned to LuaToolsLinux commit
`b3fa04a28cef848187f4e816fcd8902be29e936e` with SHA-256
`25ac4c760d10bcd597e848fc075bcb5fd8ce26dd9758f63837327f05d4a1d551`.
**This only pins the entry script**: upstream still downloads dependencies and
release assets independently. It is third-party software, and upstream failures
or Steam/plugin compatibility changes may still require upstream fixes. Ltools
checks the resulting installation and does not claim an upstream exit code proves
that every component works.

## Optional power automation

Install `power-profiles-daemon` if it is absent and ensure it works in your desktop
settings first. Do not combine this feature with TLP or auto-cpufreq.

```bash
./setup.sh power-enable
```

A systemd timer checks approximately every 30 seconds:

| Power state | Requested profile |
| --- | --- |
| Recognized power adapter online | Performance, falling back to balanced if unsupported |
| Recognized adapter offline and battery present | Power saver, falling back to balanced |
| Desktop without battery / unknown adapter state | Balanced |

This optional mode takes control of profile selection while enabled, so manual
profile changes may be replaced at the next check. It never writes CPU governors
or energy preferences directly. The timer persists across reboots.

```bash
systemctl status ltools-power.timer
journalctl -u ltools-power.service -n 30 --no-pager
./setup.sh power-disable
```

After disabling, select your preferred profile in desktop settings.

### Migrate from the original power rule

If doctor reports `/etc/udev/rules.d/99-power-profile.rules`, inspect it first:

```bash
cat /etc/udev/rules.d/99-power-profile.rules
```

**Only if it is the original Ltools rule calling
`/usr/local/bin/switch_power_profile.sh`**, move it aside and reload the rules:

```bash
sudo mv -i /etc/udev/rules.d/99-power-profile.rules /etc/udev/rules.d/99-power-profile.rules.disabled
sudo udevadm control --reload-rules
```

Reboot to clear the old script's direct CPU settings before enabling v2 automation.
The old helper file becomes inactive once the rule is disabled; v2 does not reuse it.

## Backups & permissions

Repair creates `launcher_path.txt.bak-<UTC timestamp>` beside a changed mapping.
Restore a chosen backup with `cp` while Steam is closed, then restart Steam.
An unchanged mapping creates no additional backup. Dry runs write nothing.

If older sudo runs left root-owned files, doctor flags configuration write access.
Inspect the **specific reported directory** with `ls -ld` and correct ownership
only for that application directory. Ltools intentionally does not recursively
change ownership of your Steam library or home folder.

Existing ACCELA settings and locally stored keys remain untouched; rotate exposed
keys through the provider and update them through the application's settings UI.

## Tests and limits

```bash
python3 -m unittest discover -s tests -v
bash -n setup.sh scripts/power-install.sh
```

Tests cover path repair, backup privacy, idempotence, ambiguous launchers, unknown
schemas, symlink handling, and supported power profile selection. The test suite
uses temporary files and mocked profile commands; it does not install software or
change system settings. Real Steam UI integration, GPU behavior, downloads and
hardware power transitions still require testing on the destination PC. No FPS
improvement is promised.

## Upstream references

- [LuaToolsLinux installer, pinned source](https://github.com/Star123451/LuaToolsLinux/blob/b3fa04a28cef848187f4e816fcd8902be29e936e/install.sh)
- [LuaTools launcher path reader/writer, pinned source](https://github.com/Star123451/LuaToolsLinux/blob/b3fa04a28cef848187f4e816fcd8902be29e936e/backend/downloads.py)
