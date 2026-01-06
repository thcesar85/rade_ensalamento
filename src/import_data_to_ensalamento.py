import os
import json
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from config.conn import conectar 
from config.config import API_URL_BASE, API_AUTHORIZATION

# Carrega .env
load_dotenv()
LOG_DIR = os.getenv("LOG_DIR", "dados/logs")

API_BASE_URL = API_URL_BASE.rstrip("/")
DEFAULT_TIMEOUT = (5, 20)  # (connect, read)

def _bearer(value: str) -> str:
    v = (value or "").strip()
    if not v:
        return ""
    if not v.lower().startswith("bearer "):
        return f"Bearer {v}"
    return v

def _auth_headers():
    return {
        "Content-Type": "application/json",
        "Authorization": _bearer(str(API_AUTHORIZATION))
    }

def _to_str_or_none(x):
    if pd.isna(x):
        return None
    return str(x).strip()

def enviar_dados_api_ensalamento(execution_id, group_code=None, resumo_csv_path=None):
    """
    Envia dados linha-a-linha para a API de ensalamento, opcionalmente filtrando por group_code.
    O CSV de resumo é único por execution_id e é escrito em append a cada chamada.
    """
    conn = conectar()
    if conn is None:
        print("Erro ao conectar ao banco.")
        return

    # Caminho único por execution_id (sem timestamp) — permite múltiplas chamadas
    os.makedirs(LOG_DIR, exist_ok=True)
    if not resumo_csv_path:
        resumo_csv_path = os.path.join(LOG_DIR, f"resumo_envio_{execution_id}.csv")
    csv_ja_existe = os.path.exists(resumo_csv_path)

    try:
        base_query = """
            SELECT 
                id, execution_id, entitycode, coursecode, groupcode, taskcode,
                id_place, place, data, start_time, end_time, cpf_estudante
            FROM ensalamento."tblobbyensalamento"
            WHERE execution_id = %s AND integrated = FALSE
        """
        params = [execution_id]

        if group_code is not None:
            base_query += " AND groupcode = %s"
            params.append(group_code)

        df = pd.read_sql(base_query, conn, params=tuple(params))

        if df.empty:
            print("Nenhum dado encontrado para enviar.")
            return

        # Normalizações básicas
        df["cpf_estudante"] = df["cpf_estudante"].apply(_to_str_or_none)
        df["data"] = df["data"].astype(str)
        df["start_time"] = df["start_time"].astype(str)
        df["end_time"] = df["end_time"].astype(str)

        cursor = conn.cursor()
        houve_falha = False
        linhas_resumo = []

        url = f"{API_BASE_URL}/activity"
        headers = _auth_headers()
        if not headers.get("Authorization"):
            raise RuntimeError("API_AUTHORIZATION vazio/não configurado.")

        session = requests.Session()

        for _, row in df.iterrows():
            entitycode = row["entitycode"]
            id_place = row["id_place"]
            coursecode = row["coursecode"]
            groupcode = row["groupcode"]
            taskcode = row["taskcode"]
            data_ = row["data"]
            start = row["start_time"]
            end = row["end_time"]
            cpf = row["cpf_estudante"]

            if not cpf:
                houve_falha = True
                msg_cpf = "CPF ausente/nulo"
                cursor.execute("""
                    INSERT INTO ensalamento."tblogintegracao" (
                        execution_id, lobby_id, response, status_code, mensagem, retorno_data, retorno_erros
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (execution_id, row["id"], msg_cpf, 400, msg_cpf, "[]", json.dumps([{"cpf":"missing"}], ensure_ascii=False)))
                linhas_resumo.append({
                    "lobby_id": row["id"],
                    "entitycode": entitycode,
                    "course": coursecode,
                    "grupo": groupcode,
                    "cpf": "",
                    "data": data_,
                    "hora": f"{start}-{end}",
                    "status": "erro",
                    "http": 400,
                    "mensagem": msg_cpf
                })
                continue

            payload = {
                "entityCode": str(entitycode),
                "courseCode": str(coursecode),
                "groupCode": str(groupcode),
                "place": str(id_place),
                "taskCode": str(taskcode),
                "date": data_,
                "startTime": start,
                "endTime": end,
                "students": [cpf]
            }

            # POST (com timeout)
            try:
                response = session.post(url, headers=headers, json={"data": [payload]}, timeout=DEFAULT_TIMEOUT)
                status_code = response.status_code
                response_text = response.text
            except requests.RequestException as rexc:
                response = None
                status_code = 599
                response_text = str(rexc)

            mensagem, retorno_data, retorno_erros = None, [], []
            try:
                if response and response.headers.get("Content-Type", "").startswith("application/json"):
                    resp_json = response.json()
                    mensagem = resp_json.get("message")
                    retorno_data = resp_json.get("data", [])
                    retorno_erros = resp_json.get("errors", [])
            except Exception as json_err:
                mensagem = f"Erro ao interpretar JSON: {json_err}"

            # Sucesso = qualquer 2xx
            if response and response.ok:
                cursor.execute("""
                    UPDATE ensalamento."tblobbyensalamento"
                    SET integrated = TRUE
                    WHERE id = %s
                """, (row["id"],))
            else:
                houve_falha = True

            cursor.execute("""
                INSERT INTO ensalamento."tblogintegracao" (
                    execution_id, lobby_id, response, status_code, mensagem, retorno_data, retorno_erros
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

            linhas_resumo.append({
                "lobby_id": row["id"],
                "entitycode": entitycode,
                "course": coursecode,
                "grupo": groupcode,
                "cpf": cpf,
                "data": data_,
                "hora": f"{start}-{end}",
                "status": "sucesso" if response and response.ok else "erro",
                "http": status_code,
                "mensagem": mensagem or "sem mensagem"
            })

        # CSV de resumo — APPEND no mesmo arquivo por execution_id
        df_resumo = pd.DataFrame(linhas_resumo)
        df_resumo.to_csv(
            resumo_csv_path,
            index=False,
            encoding="utf-8",
            mode="a",
            header=not csv_ja_existe  # escreve header só se o arquivo não existia
        )
        print(f"Resumo atualizado: {resumo_csv_path}")

        # Status da execução
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
