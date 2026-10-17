import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('installer', REPO / 'scripts/install_plugin.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class InstallTest(unittest.TestCase):
    def test_clean_install_and_reinstall_preserve_preferences(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'source'
            (source / 'backend').mkdir(parents=True)
            (source / 'public').mkdir()
            (source / 'public/luatools.js').write_text('window.testLuaTools=true;')
            (source / 'plugin.json').write_text('{"name":"luatools"}')
            (source / 'requirements.txt').write_text('httpx==0.27.2\n')
            config = root / 'config/millennium/config.json'
            config.parent.mkdir(parents=True)
            original = {'themes': {'activeTheme': 'custom'}, 'plugins': {'enabledPlugins': ['other']}}
            config.write_text(json.dumps(original))
            with patch.dict(os.environ, {'XDG_DATA_HOME': str(root / 'data'), 'XDG_CONFIG_HOME': str(root / 'config')}):
                target = installer.install(source, root / 'Steam', root / 'backup1', False)
                settings = json.loads(config.read_text())
                self.assertEqual(settings['themes'], original['themes'])
                self.assertEqual(settings['plugins']['enabledPlugins'], ['other', 'luatools'])
                self.assertEqual(json.loads((target / 'plugin.json').read_text())['backendType'], 'lua')
                self.assertEqual(json.loads((target / 'backend/install_paths.json').read_text())['steam_path'], str(root / 'Steam'))
                self.assertNotIn('millennium.add_browser_js(', (target / 'backend/main.lua').read_text())
                (target / 'backend/personal-state.json').write_text('{"preserve":true}')
                installer.install(source, root / 'Steam', root / 'backup2', False)
                self.assertTrue((root / 'backup2/luatools/backend/personal-state.json').exists())
                self.assertTrue((target / 'backend/personal-state.json').exists())
                self.assertEqual(json.loads(config.read_text())['plugins']['enabledPlugins'].count('luatools'), 1)
                if shutil.which('node'):
                    for name in ('index.js', 'webkit.js'):
                        subprocess.run(['node', '--check', str(target / '.millennium/Dist' / name)], check=True)


if __name__ == '__main__':
    unittest.main()
