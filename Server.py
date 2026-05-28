import os
import sys
import RapidHost

# ── Configuração ──────────────────────────────────────────────────────────────

def get_resource_path(relative_path):
    """Resolves absolute path to resource, supporting both dev and PyInstaller packaging."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)

STATIC_DIR  = get_resource_path("Static")
TEMPLATE_DIR = get_resource_path("Template")

HOST = os.environ.get("APP_HOST", "0.0.0.0")
PORT = int(os.environ.get("APP_PORT", 5000))
DEBUG = os.environ.get("APP_DEBUG", "false").lower() == "true"

# ── Validação dos diretórios ──────────────────────────────────────────────────

for label, path in [("Static", STATIC_DIR), ("Template", TEMPLATE_DIR)]:
    if not os.path.isdir(path):
        raise FileNotFoundError(f"Diretório '{label}' não encontrado: {path}")

# ── Servidor ──────────────────────────────────────────────────────────────────

RapidHost.hostIP(HOST)
RapidHost.hostPort(PORT)
RapidHost.setStaticPath(STATIC_DIR)
RapidHost.setTemplatePath(TEMPLATE_DIR)

if DEBUG:
    print(f"[DEBUG] Iniciando servidor em http://{HOST}:{PORT}")
    print(f"[DEBUG] Static:   {STATIC_DIR}")
    print(f"[DEBUG] Template: {TEMPLATE_DIR}")

RapidHost.hostSite("index.html")