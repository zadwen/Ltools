import contextlib
import importlib.util
import io
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import Mock

import ltools

spec = importlib.util.spec_from_file_location('power', Path(__file__).parents[1] / 'scripts/power-profile.py')
power = importlib.util.module_from_spec(spec)
spec.loader.exec_module(power)


class RepairTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.plugin = self.home / '.local/share/millennium/plugins/luatools'
        (self.plugin / 'backend').mkdir(parents=True)
        (self.plugin / 'backend/downloads.py').write_text("path = 'launcher_path.txt'")
        self.launcher = self.home / '.local/share/ACCELA/ACCELA.AppImage'
        self.launcher.parent.mkdir(parents=True)
        self.launcher.write_text('#!/bin/sh\nexit 0\n')
        self.launcher.chmod(0o700)
        self.target = self.plugin / 'backend/data/launcher_path.txt'

    def repair(self, **kwargs):
        with contextlib.redirect_stdout(io.StringIO()):
            ltools.repair(self.home, **kwargs)

    def test_legacy_folder_name_detected(self):
        renamed = self.plugin.with_name('LuaToolsLinux')
        self.plugin.rename(renamed)
        self.assertEqual(ltools.plugin_dirs(self.home), [renamed])

    def test_manifest_detects_renamed_folder(self):
        renamed = self.plugin.with_name('custom-folder')
        self.plugin.rename(renamed)
        (renamed / 'plugin.json').write_text('{"name": "luatools"}')
        self.assertEqual(ltools.plugin_dirs(self.home), [renamed])

    def test_partial_plugin_detected_and_reported(self):
        (self.plugin / 'backend/downloads.py').unlink()
        (self.plugin / 'backend').rmdir()
        self.assertEqual(ltools.plugin_dirs(self.home), [self.plugin])
        self.assertEqual(len(ltools.plugin_health(self.plugin)), 3)

    def test_complete_plugin_health(self):
        (self.plugin / 'plugin.json').write_text('{"name": "luatools"}')
        (self.plugin / 'backend/main.py').write_text('# backend')
        (self.plugin / 'public').mkdir()
        (self.plugin / 'public/luatools.js').write_text('// frontend')
        self.assertEqual(ltools.plugin_health(self.plugin), [])

    def test_correct_schema_and_idempotence(self):
        self.repair()
        self.assertEqual(self.target.read_text().strip(), str(self.launcher))
        self.repair()
        self.assertEqual(list(self.target.parent.glob('*.bak-*')), [])

    def test_backup_and_settings_preserved(self):
        self.target.parent.mkdir()
        self.target.write_text('/old/missing\n')
        settings = self.launcher.parent / 'settings.json'
        settings.write_text('{"custom": true}')
        self.repair()
        backup, = self.target.parent.glob('*.bak-*')
        self.assertEqual(backup.read_text(), '/old/missing\n')
        self.assertEqual(backup.stat().st_mode & 0o777, 0o600)
        self.assertEqual(settings.read_text(), '{"custom": true}')

    def test_dry_run_does_not_create_data(self):
        self.repair(dry_run=True)
        self.assertFalse(self.target.parent.exists())

    def test_ambiguous_launchers_require_selection(self):
        other = self.home / '.local/share/Bifrost/bin/Bifrost'
        other.parent.mkdir(parents=True)
        other.write_text('test')
        other.chmod(0o700)
        with self.assertRaisesRegex(ValueError, 'unique'):
            self.repair()
        self.repair(launcher=other)
        self.assertEqual(self.target.read_text().strip(), str(other))

    def test_valid_custom_launcher_preserved(self):
        self.target.parent.mkdir()
        self.target.write_text(str(self.launcher) + '\n')
        self.repair()
        self.assertEqual(self.target.read_text().strip(), str(self.launcher))

    def test_unknown_schema_leaves_files_untouched(self):
        (self.plugin / 'backend/downloads.py').write_text('new schema')
        with self.assertRaisesRegex(ValueError, 'Unrecognized'):
            self.repair()
        self.assertFalse(self.target.exists())

    def test_missing_launcher_does_not_write(self):
        self.launcher.unlink()
        with self.assertRaises(ValueError):
            self.repair()
        self.assertFalse(self.target.exists())

    def test_symlink_not_overwritten(self):
        self.target.parent.mkdir()
        other = self.home / 'unrelated'
        other.write_text('preserve')
        self.target.symlink_to(other)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            self.repair(launcher=self.launcher)
        self.assertEqual(other.read_text(), 'preserve')

    def test_duplicate_steam_symlink_deduplicated(self):
        alternate = self.home / '.millennium'
        alternate.symlink_to(self.home / '.local/share/millennium')
        self.assertEqual(len(ltools.plugin_dirs(self.home)), 1)


class PowerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def supply(self, name, kind, online=None):
        folder = self.root / name
        folder.mkdir()
        (folder / 'type').write_text(kind)
        if online is not None:
            (folder / 'online').write_text(str(online))

    def test_desktop_without_battery_is_balanced(self):
        self.assertEqual(power.desired_profile(self.root), 'balanced')

    def test_non_ac0_adapter(self):
        self.supply('ADP1', 'Mains', 1)
        self.assertEqual(power.desired_profile(self.root), 'performance')

    def test_battery(self):
        self.supply('ADP1', 'Mains', 0)
        self.supply('BAT0', 'Battery')
        self.assertEqual(power.desired_profile(self.root), 'power-saver')

    def test_usb_c_online_wins(self):
        self.supply('AC', 'Mains', 0)
        self.supply('ucsi', 'USB_C', 1)
        self.supply('BAT0', 'Battery')
        self.assertEqual(power.desired_profile(self.root), 'performance')

    def test_unsupported_performance_fallback(self):
        self.supply('AC', 'Mains', 1)
        run = Mock(side_effect=[subprocess.CompletedProcess([], 0, '* balanced:\n power-saver:\n'),
                                subprocess.CompletedProcess([], 0, 'power-saver\n'),
                                subprocess.CompletedProcess([], 0)])
        power.apply(self.root, run)
        self.assertEqual(run.call_args.args[0], ['powerprofilesctl', 'set', 'balanced'])

    def test_no_repeated_profile_writes(self):
        run = Mock(side_effect=[subprocess.CompletedProcess([], 0, '* balanced:\n'),
                                subprocess.CompletedProcess([], 0, 'balanced\n')])
        power.apply(self.root, run)
        self.assertEqual(run.call_count, 2)


if __name__ == '__main__':
    unittest.main()
