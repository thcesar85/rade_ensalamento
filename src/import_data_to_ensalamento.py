import psycopg2
import pandas as pd
import json
import requests
import os
from datetime import datetime
from dotenv import load_dotenv
from config.conn import conectar 
from config.config import API_URL_BASE, API_AUTHORIZATION

# Carrega variáveis do .env
load_dotenv()
LOG_DIR = os.getenv("LOG_DIR", "C:/rade/dados/logs")

API_BASE_URL = API_URL_BASE
API_TOKEN = API_AUTHORIZATION
url = f"{API_BASE_URL}/activity"

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": API_TOKEN
}

def enviar_dados_api_ensalamento(execution_id):
    conn = conectar()
    if conn is None:
        print("Erro ao conectar ao banco.")
        return

    try:
        query = """
            SELECT 
                id, execution_id, entitycode, coursecode, groupcode, taskcode,
                id_place, place, data, start_time, end_time, cpf_estudante
            FROM ensalamento."tblobbyensalamento"
            WHERE execution_id = %s AND integrated = FALSE
        """

        df = pd.read_sql(query, conn, params=(execution_id,))

        if df.empty:
            print("Nenhum dado encontrado para enviar.")
            return

        os.makedirs(LOG_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        resumo_csv_path = os.path.join(LOG_DIR, f"resumo_envio_{execution_id}_{timestamp}.csv")

        cursor = conn.cursor()
        houve_falha = False
        linhas_resumo = []

        # ENVIO LINHA A LINHA (sem groupby)
        for _, row in df.iterrows():
            entitycode = row["entitycode"]
            id_place = row["id_place"]
            coursecode = row["coursecode"]
            groupcode = row["groupcode"]
            taskcode = row["taskcode"]
            data_ = row["data"]
            start = row["start_time"]
            end = row["end_time"]
            cpf = str(row["cpf_estudante"]).strip()

            payload = {
                "entityCode": str(entitycode),
                "courseCode": str(coursecode),
                "groupCode": str(groupcode),
                "place": str(id_place),
                "taskCode": str(taskcode),
                "date": str(data_),
                "startTime": start,
                "endTime": end,
                "students": [cpf]
            }

            response = requests.post(url, headers=HEADERS, json={"data": [payload]})

            status_code = response.status_code
            response_text = response.text
            mensagem = None
            retorno_data = None
            retorno_erros = None

            try:
                resp_json = response.json()
                mensagem = resp_json.get("message")
                retorno_data = resp_json.get("data", [])
                retorno_erros = resp_json.get("errors", [])
            except Exception as json_err:
                mensagem = f"Erro ao interpretar JSON: {json_err}"

            if status_code == 200:
                cursor.execute("""
                    UPDATE ensalamento."tblobbyensalamento"
                    SET integrated = TRUE
                    WHERE id = %s
                """, (row["id"],))
            else:
                houve_falha = True

            # Registrar log da resposta
            cursor.execute("""
                INSERT INTO ensalamento."tblogintegracao" (
                    execution_id, lobby_id, response, status_code,
                    mensagem, retorno_data, retorno_erros
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                execution_id,
                row["id"],
                response_text,
                status_code,
                mensagem,
                json.dumps(retorno_data, ensure_ascii=False),
                json.dumps(retorno_erros, ensure_ascii=False)
            ))

            # Adicionar linha para CSV
            linhas_resumo.append({
                "entitycode": entitycode,
                "course": coursecode,
                "grupo": groupcode,
                "cpf": cpf,
                "data": str(data_),
                "hora": f"{start}-{end}",
                "status": "sucesso" if status_code == 200 else "erro",
                "http": status_code,
                "mensagem": mensagem or "sem mensagem"
            })

        # Salvar CSV de resumo
        df_resumo = pd.DataFrame(linhas_resumo)
        df_resumo.to_csv(resumo_csv_path, index=False, encoding="utf-8")
        print(f"Resumo salvo em: {resumo_csv_path}")

        # Atualizar status da execução
        status_final = 'ERRO' if houve_falha else 'CONCLUIDA'
        cursor.execute("""
            UPDATE ensalamento."tbexecucaointegracao"
            SET status = %s
            WHERE execution_id = %s
        """, (status_final, execution_id))

        conn.commit()
        cursor.close()

    except Exception as e:
        print(f"Erro ao processar envio: {e}")
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE ensalamento."tbexecucaointegracao"
                SET status = 'ERRO', erro = %s
                WHERE execution_id = %s
            """, (str(e), execution_id))
            conn.commit()
    finally:
        conn.close()
