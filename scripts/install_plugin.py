#!/usr/bin/env python3
"""Install LuaTools source with the experimental Millennium 3 frontend adapter."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess


def install(source, steam, backup, install_dependencies=True):
    repo = Path(__file__).resolve().parents[1]
    data = Path(os.environ.get('XDG_DATA_HOME', str(Path.home() / '.local/share')))
    config = Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home() / '.config')))
    target = data / 'millennium/plugins/luatools'
    backup.mkdir(parents=True, exist_ok=True)
    if target.exists():
        shutil.copytree(target, backup / 'luatools', symlinks=True)
    target.mkdir(parents=True, exist_ok=True)
    for name in ('backend', 'public'):
        shutil.copytree(source / name, target / name, dirs_exist_ok=True)
    for name in ('plugin.json', 'requirements.txt'):
        shutil.copy2(source / name, target / name)
    for name in ('main.lua', 'web_bridge_server.py'):
        shutil.copy2(repo / 'compat' / name, target / 'backend' / name)
    (target / 'backend/install_paths.json').write_text(json.dumps({'steam_path': str(steam.resolve())}) + '\n')
    metadata = json.loads((target / 'plugin.json').read_text())
    metadata['backendType'] = 'lua'
    (target / 'plugin.json').write_text(json.dumps(metadata, indent=2) + '\n')
    bridge = '''(function(){
window.Millennium=window.Millennium||{};
window.Millennium.callServerMethod=function(plugin,method,args){
return fetch('http://127.0.0.1:38495/rpc',{
method:'POST',headers:{'Content-Type':'application/json'},
body:JSON.stringify({method:String(method||''),args:args||{}})
}).then(function(r){if(!r.ok)throw new Error('LuaTools bridge unavailable');return r.json();})
.then(function(b){if(b.success!==true)throw new Error(b.error||'RPC failed');return b.result;});
};
})();\n'''
    dist = target / '.millennium/Dist'
    dist.mkdir(parents=True, exist_ok=True)
    shutil.copy2(repo / 'compat/index.js', dist / 'index.js')
    frontend = (repo / 'compat/webkit-loader.js').read_text()
    frontend += '\n;(function(){function startLuaTools(){\n' + bridge
    frontend += (target / 'public/luatools.js').read_text()
    frontend += '\n}\nif(document.body){startLuaTools();}else{document.addEventListener("DOMContentLoaded",startLuaTools,{once:true});}\n})();\n'
    (dist / 'webkit.js').write_text(frontend)
    # Preserve themes and all unrelated Millennium preferences.
    settings = config / 'millennium/config.json'
    settings.parent.mkdir(parents=True, exist_ok=True)
    if settings.exists():
        shutil.copy2(settings, backup / 'millennium-config.json')
        cfg = json.loads(settings.read_text())
    else:
        cfg = {}
    enabled = cfg.setdefault('plugins', {}).setdefault('enabledPlugins', [])
    if 'luatools' not in enabled:
        enabled.append('luatools')
    settings.write_text(json.dumps(cfg, indent=2) + '\n')
    if install_dependencies:
        subprocess.run(['python3', '-m', 'venv', str(target / '.venv')], check=True)
        subprocess.run([str(target / '.venv/bin/python3'), '-m', 'pip', 'install', '-r', str(target / 'requirements.txt')], check=True)
    print('LuaTools installed:', target)
    print('Steam:', steam)
    return target


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('source', 'steam', 'backup'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    install(args.source, args.steam, args.backup)
