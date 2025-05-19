import os
import requests
from datetime import datetime
from dotenv import load_dotenv
import json
from config.conn import conectar 
from config.config import API_URL_BASE, API_AUTHORIZATION

API_BASE_URL = API_URL_BASE  #os.getenv("API_BASE_URL")
API_TOKEN = API_AUTHORIZATION  #"Bearer 5Xf4IYXlV1TTpAUsJL10y3BTEMlqGT6p" #os.getenv("API_TOKEN")


def fetch_group_data_by_code(codigo_grupo):
    """Faz a requisição GET na API e retorna os dados filtrados de um grupo específico."""
    url = f"{API_BASE_URL}/group/{codigo_grupo}"
    headers = {
        "Authorization": API_TOKEN
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Erro ao buscar grupo: {response.status_code} - {response.text}")

    try:
        grupo = response.json()
    except Exception as e:
        raise ValueError(f"Erro ao decodificar JSON: {e} - Conteúdo: {response.text}")

    if not isinstance(grupo, dict):
        raise ValueError(f"Resposta inesperada da API para o grupo {codigo_grupo}: {grupo}")

    dados_filtrados = {
        "entityCode": grupo.get("entityCode"),
        "entity": grupo.get("entity"),
        "courseCode": grupo.get("courseCode"),
        "course": grupo.get("course"),
        "groupCode": grupo.get("groupCode"),
        "code": grupo.get("code"),
        "name": grupo.get("name"),
        "startDate": grupo.get("startDate"),
        "endDate": grupo.get("endDate"),
        "workload": grupo.get("workload"),
        "dailyLimit": grupo.get("dailyLimit"),
        "weeklyLimit": grupo.get("weeklyLimit"),
        "active": grupo.get("active"),
        "tasks": grupo.get("tasks", []),
        "places": grupo.get("places", [])
    }

    return [dados_filtrados]

def fetch_group_data():
    """
    Faz a requisição na API para o grupo especificado e retorna um dict com só os campos desejados.
    """
    url = f"{API_BASE_URL}/group"
    headers = {
        "Authorization": API_TOKEN
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        grupos = response.json()  # <- isso deve ser uma lista de dicionários

        dados_filtrados = []
        for grupo in grupos:
            if isinstance(grupo, dict):  # adiciona esta verificação
                dados_filtrados.append({
                    "entityCode": grupo.get("entityCode"),
                    "entity": grupo.get("entity"),
                    "courseCode": grupo.get("courseCode"),
                    "course": grupo.get("course"),
                    "groupCode": grupo.get("groupCode"),
                    "code": grupo.get("code"),
                    "name": grupo.get("name"),
                    "startDate": grupo.get("startDate"),
                    "endDate": grupo.get("endDate"),
                    "workload": grupo.get("workload"),
                    "dailyLimit": grupo.get("dailyLimit"),
                    "weeklyLimit": grupo.get("weeklyLimit"),
                    "active": grupo.get("active"),
                    "tasks": grupo.get("tasks", []),
                    "places": grupo.get("places", [])
                })
            else:
                print(f"Aviso: grupo inesperado (não é um dicionário): {grupo}")

        return dados_filtrados

    except Exception as e:
        print(f"Erro ao buscar grupos: {e}")
        return []


def save_group_data(grupo):
    """Insere os dados de um grupo no banco de dados."""
    conn = conectar()
    if conn is None:
        print("Conexão com o banco falhou.")
        return

    try:
        cursor = conn.cursor()

        sql = """
            INSERT INTO aux_grupo_estagio (
                entity_code,
                entity,
                course_code,
                course,
                group_code,
                code,
                name,
                start_date,
                end_date,
                workload,
                daily_limit,
                weekly_limit,
                active,
                tasks,
                places
            ) VALUES (
                %(entityCode)s,
                %(entity)s,
                %(courseCode)s,
                %(course)s,
                %(groupCode)s,
                %(code)s,
                %(name)s,
                %(startDate)s,
                %(endDate)s,
                %(workload)s,
                %(dailyLimit)s,
                %(weeklyLimit)s,
                %(active)s,
                %(tasks)s,
                %(places)s
            )
        """

        # Convertendo arrays para JSON se necessário
        grupo["tasks"] = json.dumps(grupo.get("tasks", []))
        grupo["places"] = json.dumps(grupo.get("places", []))

        cursor.execute(sql, grupo)
        conn.commit()
        print(f"Grupo {grupo['groupCode']} inserido com sucesso.")

    except Exception as e:
        print(f"Erro ao inserir grupo {grupo.get('groupCode')}: {e}")
    finally:
        cursor.close()
        conn.close()

def refresh_tables():
    
    """Insere os dados de um grupo no banco de dados."""
    conn = conectar()
    if conn is None:
        print("Conexão com o banco falhou.")
        return

    try:
        cursor = conn.cursor()

        sql = """
            call public.upsert_all()
        """

        cursor.execute(sql)
        conn.commit()
        print(f"Tabelas atualizadas com sucesso.")


    except Exception as e:
        print(f"Erro ao inserir procedure de atualização das tabelas: {e}")
    finally:
        cursor.close()
        conn.close()