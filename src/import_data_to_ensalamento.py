import psycopg2
import pandas as pd
import json
import requests
from config.conn import conectar 
from config.config import API_URL_BASE, API_AUTHORIZATION

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

        grouped = df.groupby([
            "entitycode", "id_place", "coursecode", "groupcode",
            "taskcode", "data", "start_time", "end_time"
        ])

        payloads = []

        for (entitycode, id_place, coursecode, groupcode, taskcode, data_, start, end), group_df in grouped:
            students = group_df["cpf_estudante"].astype(str).str.replace(r'\\D', '', regex=True).tolist()


            payload = {
                "entityCode": str(entitycode),
                "courseCode": str(coursecode),
                "groupCode": str(groupcode),
                "place": str(id_place),
                "taskCode": str(taskcode),
                "date": str(data_),
                "startTime": start,
                "endTime": end,
                "students": students
            }

            payloads.append(payload)

        # Salvar payload e comando curl para debug
        with open("payload.json", "w", encoding="utf-8") as f:
            json.dump(payloads, f, indent=4, ensure_ascii=False)

        # Enviar para a API
        response = requests.post(url, headers=HEADERS, json={"data": payloads})

        print(f"Status Code: {response.status_code}")
        print(f"Resposta: {response.text}")

        mensagem = None
        retorno_data = None
        retorno_erros = None

        try:
            resp_json = response.json()
            mensagem = resp_json.get("message")
            retorno_data = resp_json.get("data", [])
            retorno_erros = resp_json.get("errors", [])
        except Exception as json_err:
            print(f"Erro ao interpretar JSON da resposta: {json_err}")

        with conn.cursor() as cursor:
            # Atualizar status da execução
            if response.status_code == 200:
                cursor.execute("""
                    UPDATE ensalamento."tblobbyensalamento"
                    SET integrated = TRUE
                    WHERE execution_id = %s
                """, (execution_id,))

                cursor.execute("""
                    UPDATE ensalamento."tbexecucaointegracao"
                    SET status = 'CONCLUIDA'
                    WHERE execution_id = %s
                """, (execution_id,))
            else:
                cursor.execute("""
                    UPDATE ensalamento."tbexecucaointegracao"
                    SET status = 'ERRO'
                    WHERE execution_id = %s
                """, (execution_id,))

            # Registrar log da integração
            cursor.execute("""
                INSERT INTO ensalamento."tblogintegracao" (
                    execution_id, lobby_id, response, status_code,
                    mensagem, retorno_data, retorno_erros
                ) VALUES (%s, NULL, %s, %s, %s, %s, %s)
            """, (
                execution_id,
                response.text,
                response.status_code,
                mensagem,
                json.dumps(retorno_data),
                json.dumps(retorno_erros)
            ))

            conn.commit()

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
