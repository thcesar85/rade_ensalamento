import psycopg2
import uuid
from config.conn import conectar  # sua função de conexão

def lista_codigo_grupo():
    conn = conectar()
    if conn is None:
        print("Erro na conexão com o banco.")
        return []

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT codigo_grupo FROM public."aux_agendamento"
        """)
        resultados = cursor.fetchall()
        grupos = [linha[0] for linha in resultados]
        return grupos
    except Exception as e:
        print(f"Erro ao buscar grupos: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def truncar_tabelas_auxiliares():
    """Executa a procedure que trunca as tabelas auxiliares."""
    conn = conectar()
    if conn is None:
        print("Erro ao conectar no banco.")
        return

    try:
        cursor = conn.cursor()
        cursor.execute("CALL truncate_aux_tables();")
        conn.commit()
        print("Tabelas auxiliares truncadas com sucesso.")
    except Exception as e:
        print(f"Erro ao truncar tabelas auxiliares: {e}")
    finally:
        cursor.close()
        conn.close()

def processar_integracao_estagio():
    """Gera um execution_id, chama a procedure e retorna o ID."""
    conn = conectar()
    if conn is None:
        print("Erro ao conectar no banco.")
        return None

    execution_id = str(uuid.uuid4())

    try:
        cursor = conn.cursor()

        print(f"Iniciando processamento com execution_id: {execution_id}")
        cursor.execute("CALL processar_integracao_estagio(%s);", (execution_id,))
        conn.commit()

        print("Processamento concluído com sucesso.")
        return execution_id

    except Exception as e:
        print(f"Erro ao processar integração: {e}")
        conn.rollback()
        return None

    finally:
        cursor.close()
        conn.close()