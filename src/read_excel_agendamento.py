import pandas as pd
import psycopg2
import json
from datetime import datetime, time
from config.conn import conectar 

def importar_agendamento_excel(caminho_arquivo):
    print("Iniciando importação do agendamento...")

    # Lê a planilha Excel
    df = pd.read_excel(caminho_arquivo)

    # Renomeia as colunas da planilha para os nomes usados no banco
    df.columns = [
        "escola", "grupo", "codigo_grupo", "estudante", "cpf_estudante",
        "atividade", "campo_estagio", "tarefa", "codigo_tarefa",
        "preceptor", "data", "dia_semana", "hora_inicio", "hora_final"
    ]

    conn = conectar()
    if conn is None:
        print("Erro na conexão com o banco de dados.")
        return

    try:
        cursor = conn.cursor()

        for _, row in df.iterrows():
            sql = """
                INSERT INTO ensalamento."aux_agendamento" (
                    escola, grupo, codigo_grupo, estudante, cpf_estudante,
                    atividade, campo_estagio, tarefa, codigo_tarefa,
                    preceptor, data, dia_semana, hora_inicio, hora_final
                ) VALUES (
                    %(escola)s, %(grupo)s, %(codigo_grupo)s, %(estudante)s, %(cpf_estudante)s,
                    %(atividade)s, %(campo_estagio)s, %(tarefa)s, %(codigo_tarefa)s,
                    %(preceptor)s, %(data)s, %(dia_semana)s, %(hora_inicio)s, %(hora_final)s
                )
            """

            dados = {
                "escola": row["escola"],
                "grupo": row["grupo"],
                "codigo_grupo": row["codigo_grupo"],
                "estudante": row["estudante"],
                "cpf_estudante": row["cpf_estudante"],
                "atividade": row["atividade"],
                "campo_estagio": row["campo_estagio"],
                "tarefa": row["tarefa"],
                "codigo_tarefa": row["codigo_tarefa"],
                "preceptor": row["preceptor"],
                "data": pd.to_datetime(row["data"]).date() if not pd.isna(row["data"]) else None,
                "dia_semana": row["dia_semana"],
                "hora_inicio": row["hora_inicio"],
                "hora_final": row["hora_final"]
            }

            cursor.execute(sql, dados)

        conn.commit()
        print("Importação concluída com sucesso.")

    except Exception as e:
        print(f"Erro durante a importação: {e}")
    finally:
        cursor.close()
        conn.close()