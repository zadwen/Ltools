import json
import traceback
import sys
import types
import os
import mimetypes
import importlib.util
from http.server import BaseHTTPRequestHandler, HTTPServer

HOST = '127.0.0.1'
PORT = 38495

# =========================================================
# EMULADOR DO MILLENNIUM v2 (Mocks de Sistema)
# =========================================================
class MockLogger:
    def __init__(self, *args, **kwargs): pass
    def log(self, msg): print(f"[Log] {msg}")
    def info(self, msg): print(f"[Info] {msg}")
    def warn(self, msg): print(f"[Aviso] {msg}")
    def error(self, msg): print(f"[Erro] {msg}")

# Mockar o PluginUtils antes de carregar o main
plugin_utils_mock = types.ModuleType("PluginUtils")
plugin_utils_mock.Logger = MockLogger
sys.modules["PluginUtils"] = plugin_utils_mock

# Mockar o Millennium (Necessário para o main.py carregar)
millennium_mock = types.ModuleType("Millennium")
millennium_mock.version = lambda: "2.0.0-emulator"
def configured_steam_path():
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "install_paths.json")
    if os.path.isfile(config_path):
        with open(config_path, encoding="utf-8") as handle:
            return json.load(handle)["steam_path"]
    return os.path.expanduser("~/.steam/steam")

millennium_mock.steam_path = configured_steam_path
millennium_mock.callServerMethod = lambda *args, **kwargs: None
millennium_mock.add_browser_js = lambda *args, **kwargs: None
millennium_mock.ready = lambda *args, **kwargs: None
sys.modules["Millennium"] = millennium_mock

# Mockar o platform_bridge que o seu main.py tenta importar
platform_bridge_mock = types.ModuleType("platform_bridge")
platform_bridge_mock.Millennium = millennium_mock
sys.modules["platform_bridge"] = platform_bridge_mock

# =========================================================
# DETECÇÃO DE CAMINHOS
# =========================================================
backend_dir = os.path.dirname(os.path.abspath(__file__))
plugin_root = os.path.dirname(backend_dir)
public_dir = os.path.join(plugin_root, "public")

# Adiciona as pastas ao PATH para evitar erros de import
for p in [backend_dir, plugin_root]:
    if p not in sys.path:
        sys.path.insert(0, p)

os.chdir(backend_dir)

# =========================================================
# CARREGAMENTO E INICIALIZAÇÃO DO PLUGIN
# =========================================================
path_to_main = os.path.join(backend_dir, "main.py")
old_main = None

if os.path.exists(path_to_main):
    try:
        spec = importlib.util.spec_from_file_location("main", path_to_main)
        old_main = importlib.util.module_from_spec(spec)
        sys.modules["main"] = old_main
        spec.loader.exec_module(old_main)
        
        # INICIALIZAÇÃO CRÍTICA: Chama o _load() do seu main.py
        if hasattr(old_main, 'plugin'):
            print("[Emulador] Inicializando lógica do plugin (_load)...")
            old_main.plugin._load()
            
        print("[Emulador] main.py carregado e inicializado com sucesso!")
    except Exception as e:
        print(f"[Emulador Erro] Falha crítica no main.py:\n{traceback.format_exc()}")

# =========================================================
# SERVIDOR WEB (RPC + ARQUIVOS)
# =========================================================
class RPCBridgeHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args): pass

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        """Entrega arquivos da pasta public (Temas, JS, Imagens)"""
        clean_path = self.path.split('?')[0].lstrip('/')
        file_path = os.path.abspath(os.path.join(public_dir, clean_path))

        if os.path.exists(file_path) and os.path.isfile(file_path):
            self.send_response(200)
            mime_type, _ = mimetypes.guess_type(file_path)
            self.send_header('Content-Type', mime_type or 'application/octet-stream')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            with open(file_path, 'rb') as f:
                self.wfile.write(f.read())
        else:
            self.send_error(404)

    def do_POST(self):
        """Processa comandos RPC (Funções do Python)"""
        if self.path == '/rpc':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            try:
                payload = json.loads(post_data.decode('utf-8'))
                method = payload.get('method', '')
                args = payload.get('args', {})
                
                result = self.handle_method(method, args)
                response = {"success": True, "result": result}
            except Exception as e:
                print(f"[ERRO RPC] Método {method}: {str(e)}")
                response = {"success": False, "error": str(e)}
                
            self.wfile.write(json.dumps(response).encode('utf-8'))

    def handle_method(self, method, args):
        if method == "Logger.log":
            print(f"[JS LOG] {args.get('message', '')}")
            return "Logged"

        # Procura a função no seu main.py
        if old_main and hasattr(old_main, method):
            func = getattr(old_main, method)
            try:
                # Tenta passar argumentos, se der erro de tipo, tenta sem nada
                try: return func(**args)
                except TypeError: return func()
            except Exception as e:
                print(f"[ERRO na funcao {method}]:\n{traceback.format_exc()}")
                return None
        
        print(f"[Aviso] Funcao '{method}' nao encontrada.")
        return None

def run():
    print(f"--- Emulador LuaTools Ativo na porta {PORT} ---")
    server_address = (HOST, PORT)
    httpd = HTTPServer(server_address, RPCBridgeHandler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()

if __name__ == '__main__':
    run()
