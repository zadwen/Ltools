#!/usr/bin/env python3
"""Ltools diagnostics and conservative launcher repair. Standard library only."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone


def plugin_dirs(home):
    data = Path(os.environ.get('XDG_DATA_HOME') or home / '.local/share')
    bases = [data / 'millennium/plugins', home / '.local/share/millennium/plugins',
             home / '.millennium/plugins']
    for steam in (home / '.steam/steam', home / '.steam/root', home / '.local/share/Steam'):
        bases.extend([steam / 'millennium/plugins', steam / 'steamui/millennium/plugins',
                      steam / 'plugins'])
    found = []
    for base in bases:
        if not base.is_dir():
            continue
        for candidate in base.iterdir():
            if not candidate.is_dir():
                continue
            manifest = candidate / 'plugin.json'
            named = candidate.name.lower() in {'luatools', 'luatoolslinux', 'luatoolslinux-main'}
            identified = False
            if manifest.is_file():
                try:
                    metadata = json.loads(manifest.read_text())
                    identified = isinstance(metadata, dict) and metadata.get('name', '').lower() == 'luatools'
                except (ValueError, OSError, AttributeError):
                    pass
            if (named or identified) and candidate.resolve() not in found:
                found.append(candidate.resolve())
    return found


def plugin_health(plugin):
    issues = []
    try:
        manifest = json.loads((plugin / 'plugin.json').read_text())
        if not isinstance(manifest, dict) or manifest.get('name') != 'luatools':
            issues.append('plugin.json does not identify the luatools plugin')
    except (ValueError, OSError):
        issues.append('plugin.json is missing, unreadable or invalid')
    if not (plugin / 'backend/main.py').is_file():
        issues.append('Python backend/main.py is missing (incomplete or nested installation)')
    if not (plugin / 'public/luatools.js').is_file():
        issues.append('public/luatools.js is missing (incomplete LuaTools frontend)')
    return issues


def launcher_candidates(home):
    candidates = [home / '.local/share/Bifrost/bin/Bifrost',
                  home / '.local/share/ACCELA/ACCELA.AppImage',
                  home / '.local/share/ACCELA/run.sh']
    return [p for p in candidates if p.is_file() and os.access(p, os.X_OK)]


def mapping_path(plugin):
    # Require evidence of this schema in the installed plugin, not just its folder name.
    backend = plugin / 'backend'
    for name in ('downloads.py', 'downloadsbroke.py'):
        source = backend / name
        if source.is_file() and 'launcher_path.txt' in source.read_text(errors='replace'):
            return backend / 'data/launcher_path.txt'
    raise ValueError('Unrecognized launcher configuration schema. Set the launcher through the LuaTools UI; no files were changed.')


def atomic_write(path, content):
    """Private backup and atomic replacement. Never silently replace a symlink."""
    if path.is_symlink():
        raise ValueError(f'Refusing to replace a symlink: {path}')
    if path.exists() and path.read_text() == content:
        return None
    path.parent.mkdir(parents=True, exist_ok=True)
    backup = None
    if path.exists():
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        backup = path.with_name(path.name + '.bak-' + stamp)
        # Create privately from the outset; backups can include credentials.
        with os.fdopen(os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'w') as stream:
            stream.write(path.read_text())
    fd, name = tempfile.mkstemp(prefix='.ltools-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)
    return backup


def repair(home, plugin=None, launcher=None, dry_run=False):
    plugins = [plugin.resolve()] if plugin else plugin_dirs(home)
    if len(plugins) != 1:
        raise ValueError('Expected one LuaTools installation. Use --plugin-dir PATH to select it, or install the plugin first.')
    target = mapping_path(plugins[0])
    if launcher:
        selected = launcher.expanduser().resolve()
    else:
        saved = target.read_text().strip() if target.exists() else ''
        # Preserve a valid user-selected launcher, including one outside the usual paths.
        if saved and Path(saved).is_absolute() and Path(saved).is_file() and os.access(saved, os.X_OK):
            selected = Path(saved)
        else:
            candidates = launcher_candidates(home)
            if len(candidates) != 1:
                raise ValueError('No unique executable launcher found. Use --launcher PATH to select your installed launcher.')
            selected = candidates[0].resolve()
    if not selected.is_file() or not os.access(selected, os.X_OK):
        raise ValueError(f'Launcher is missing or not executable: {selected}')
    if '\n' in str(selected) or '\r' in str(selected):
        raise ValueError('Launcher path must not contain newlines.')
    print(f'Launcher: {selected}\nMapping:  {target}')
    if dry_run:
        print('Dry run: no files changed.')
        return
    backup = atomic_write(target, str(selected) + '\n')
    if backup:
        print(f'Backup:   {backup}')
    print('Launcher mapping verified. Restart Steam to reload it.')


def doctor(home):
    problems = 0
    def report(ok, message):
        nonlocal problems
        print(f"[{'OK' if ok else 'CHECK'}] {message}")
        problems += not ok
    print('Ltools 2 • by zadwen — read-only diagnostics')
    print(f'User home: {home}')
    for cmd in ('curl', 'git', 'jq', 'unzip'):
        report(bool(shutil.which(cmd)), f'{cmd} available')
    native = any((home / p).exists() for p in ('.local/share/Steam/steamapps', '.steam/steam/steamapps'))
    report(native, 'Native Steam installation detected')
    for directory, label in (('.var/app/com.valvesoftware.Steam', 'Flatpak'), ('snap/steam', 'Snap')):
        if (home / directory).exists():
            print(f'[INFO] {label} Steam data found. Upstream integration targets native Steam; no sandbox changes are made.')
    plugins = plugin_dirs(home)
    report(len(plugins) == 1, f'{len(plugins)} LuaTools installation(s) detected')
    loader = Path('/usr/lib/millennium').is_dir() or bool(shutil.which('millennium'))
    report(loader, 'Millennium installation evidence found' if loader else
           'Millennium loader not found in the usual location; installing ACCELA alone does not install it')
    print('[INFO] File detection does not prove Steam loaded the plugin.')
    print('[NEXT] In Steam, open Steam > Millennium > Plugins and check whether LuaTools is listed and enabled.')
    print('[NEXT] If Millennium itself is absent from Steam, troubleshoot the loader before the launcher.')
    print('[NEXT] For startup errors: fully exit Steam, run steam -dev, and inspect the LuaTools/Millennium errors locally.')
    data = Path(os.environ.get('XDG_DATA_HOME') or home / '.local/share')
    print(f'[INFO] Millennium log directory: {data / "millennium/logs"} (contents not printed)')
    for plugin in plugins:
        print(f'  {plugin}')
        for issue in plugin_health(plugin):
            report(False, issue)
        try:
            path = mapping_path(plugin)
            saved = path.read_text().strip() if path.exists() else ''
            valid = bool(saved) and Path(saved).is_absolute() and Path(saved).is_file() and os.access(saved, os.X_OK)
            report(valid, 'Saved launcher is executable' if valid else 'Launcher mapping missing or invalid; run ./setup.sh repair')
            report(os.access(path if path.exists() else plugin / 'backend', os.W_OK), 'Plugin configuration writable by this user')
        except (OSError, ValueError) as exc:
            report(False, str(exc))
    candidates = launcher_candidates(home)
    for candidate in candidates:
        print(f'[INFO] Launcher found: {candidate}')
    settings = home / '.local/share/ACCELA/settings.json'
    if settings.exists():
        try:
            data = json.loads(settings.read_text())
            report(isinstance(data, dict), 'ACCELA settings JSON is an object (values are never printed)')
        except (OSError, ValueError):
            report(False, 'ACCELA settings unreadable or invalid JSON; preserve a backup before editing')
    legacy = Path('/etc/udev/rules.d/99-power-profile.rules')
    if legacy.exists():
        report(False, 'Legacy power rule found. See README migration instructions before enabling v2 power management.')
    if shutil.which('powerprofilesctl'):
        result = subprocess.run(['powerprofilesctl', 'get'], capture_output=True, text=True, timeout=10)
        report(result.returncode == 0, 'Power profile daemon reachable')
        if result.returncode == 0:
            print('  Active profile: ' + result.stdout.strip())
    else:
        print('[INFO] powerprofilesctl absent; optional power automation is unavailable.')
    print(f'Checks needing attention: {problems}')
    return 1 if problems else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('doctor', 'repair'))
    parser.add_argument('--plugin-dir', type=Path)
    parser.add_argument('--launcher', type=Path)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    if os.geteuid() == 0:
        parser.error('Run as your normal desktop user, without sudo.')
    try:
        if args.action == 'doctor':
            if args.plugin_dir or args.launcher or args.dry_run:
                parser.error('These options are only supported with repair.')
            return doctor(Path.home())
        repair(Path.home(), args.plugin_dir, args.launcher, args.dry_run)
        return 0
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        print(f'[ERROR] {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
