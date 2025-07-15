import psycopg2
from config.config import DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, DB_PORT

def conectar():
    """Estabelece a conexão com o banco de dados PostgreSQL."""
    campos = {
        "DB_HOST": DB_HOST,
        "DB_NAME": DB_NAME,
        "DB_USER": DB_USER,
        "DB_PASSWORD": DB_PASSWORD,
        "DB_PORT": DB_PORT,
    }

    # Verifica se há variáveis ausentes (None ou string vazia)
    ausentes = [k for k, v in campos.items() if not v]
    if ausentes:
        print(f"[ERRO] Variáveis de ambiente ausentes: {', '.join(ausentes)}")
        return None

    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT
        )
        print("Conexão com o banco estabelecida com sucesso!")
        return conn
    except Exception as e:
        print(f"[ERRO] Falha ao conectar no banco: {e}")
        return None

def testar_conexao():
    """Função para testar a conexão com o banco."""
    conn = conectar()
    if not conn:
        print("[ERRO] Não foi possível conectar ao banco de dados.")
        return

    try:
        cursor = conn.cursor()
        cursor.execute('SELECT 1;')
        print("Teste de conexão bem-sucedido!")
    except Exception as e:
        print(f"[ERRO] Falha ao executar consulta de teste: {e}")
    finally:
        try:
            cursor.close()
        except:
            pass
        conn.close()
