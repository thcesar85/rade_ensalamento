import psycopg2
from config import DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, DB_PORT

def conectar():
    """Estabelece a conexão com o banco de dados PostgreSQL."""
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
        print(f"Erro ao conectar ao banco: {e}")
        return None

def testar_conexao():
    """Função para testar a conexão com o banco."""
    conn = conectar()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT 1;')  # Executando um comando simples para testar a conexão
            print("Teste de conexão bem-sucedido!")
        except Exception as e:
            print(f"Erro no teste de conexão: {e}")
        finally:
            cursor.close()
            conn.close()  # Fechando a conexão após o teste
    else:
        print("Não foi possível conectar ao banco de dados.")
