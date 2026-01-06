import os
import sys
from dotenv import load_dotenv
from src.api_context import get_api_token 

# Detecta se está rodando como .exe (PyInstaller) ou script .py
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Caminho do .env
dotenv_path = os.path.join(BASE_DIR, '.env')
load_dotenv(dotenv_path)

# =========================
# 🔐 CREDENCIAIS (Banco + API)
# =========================

DB_HOST = "142.93.58.98"
DB_PORT = "15432"
DB_NAME = "automacao"
DB_USER = "admin"

DB_PASSWORD = "{9Sc3Q*rbC29"


#API_AUTHORIZATION = f"Bearer {API_BEARER_TOKEN_IDOMED}"
API_URL_BASE = "https://radeestagio.com.br/api/v1"

# =========================
# 📁 Diretórios configuráveis via .env
# =========================

EXCEL_DIR = os.getenv("INPUT_EXCEL_DIR", os.path.join(BASE_DIR, "dados"))
LOG_DIR = "dados/logs"  #os.getenv("LOG_DIR", os.path.join(EXCEL_DIR, "logs"))
EXCEL_OLD_DIR = "dados/old"  #os.getenv("EXCEL_OLD_DIR", os.path.join(EXCEL_DIR, "old"))

# =========================
# 🛠️ Garante que as pastas existam
# =========================

for path in [EXCEL_DIR, LOG_DIR, EXCEL_OLD_DIR]:
    os.makedirs(path, exist_ok=True)


# === AUTH dinâmico: só token vindo do contexto, sem fallback
class _LazyAuth:
    def __str__(self):
        token = get_api_token()
        if not token:
            raise RuntimeError(
                "API token não definido no contexto. Selecione a IES antes de chamar a API."
            )
        return token
    __repr__ = __str__
    def __format__(self, f):  # suporta f-strings
        return format(str(self), f)

API_AUTHORIZATION = _LazyAuth()