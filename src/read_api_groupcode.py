import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv
from config.conn import conectar
from config.config import API_URL_BASE, API_AUTHORIZATION

# Carrega variáveis de ambiente
load_dotenv()

API_BASE_URL = API_URL_BASE
API_TOKEN = API_AUTHORIZATION

def fetch_group_data_by_name(nome_grupo):
    """
    Faz a requisição GET na API e retorna os dados filtrados dos grupos com o nome informado.
    Se não encontrar, retorna lista vazia. Nunca lança exceção para grupo não encontrado.
    """
    url = f"{API_BASE_URL}/group?name={nome_grupo}"
    headers = {"Authorization": API_TOKEN}

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 404:
            return []
        if response.status_code != 200:
            print(f"Erro ao buscar grupo '{nome_grupo}': {response.status_code} - {response.text}")
            return []

        grupos = response.json()
        if not isinstance(grupos, list):
            print(f"Resposta inesperada da API para nome '{nome_grupo}': {grupos}")
            return []

        dados_filtrados = []
        for grupo in grupos:
            if isinstance(grupo, dict):
                dados_filtrados.append({
                    "entityCode": grupo.get("entityCode"),
                    "entity": grupo.get("entity"),
                    "courseCode": 1244,
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
                print(f"Aviso: item inesperado na resposta da API para nome '{nome_grupo}': {grupo}")

        return dados_filtrados

    except Exception as e:
        print(f"Erro ao processar grupo '{nome_grupo}': {e}")
        return []

def fetch_group_data_by_code(codigo_grupo):
    """
    Faz a requisição GET para buscar um grupo por código.
    Retorna uma lista com 1 item se encontrado, ou lista vazia.
    """
    url = f"{API_BASE_URL}/group/{codigo_grupo}"
    headers = {"Authorization": API_TOKEN}

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 404:
            return []
        if response.status_code != 200:
            print(f"Erro ao buscar grupo '{codigo_grupo}': {response.status_code} - {response.text}")
            return []

        grupo = response.json()
        if not isinstance(grupo, dict):
            print(f"Resposta inesperada da API para grupo '{codigo_grupo}': {grupo}")
            return []

        return [{
            "entityCode": grupo.get("entityCode"),
            "entity": grupo.get("entity"),
            "courseCode": 1244, #grupo.get("courseCode"),
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
        }]

    except Exception as e:
        print(f"Erro ao processar grupo '{codigo_grupo}': {e}")
        return []

def fetch_group_data():
    """
    Busca todos os grupos disponíveis via API.
    Retorna uma lista com os dados filtrados.
    """
    url = f"{API_BASE_URL}/group"
    headers = {"Authorization": API_TOKEN}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        grupos = response.json()

        dados_filtrados = []
        for grupo in grupos:
            if isinstance(grupo, dict):
                dados_filtrados.append({
                    "entityCode": grupo.get("entityCode"),
                    "entity": grupo.get("entity"),
                    "courseCode": 1244, ##grupo.get("courseCode"),
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
    """
    Salva um grupo no banco de dados na tabela auxiliar.
    """
    conn = conectar()
    if conn is None:
        print("Conexão com o banco falhou.")
        return

    try:
        cursor = conn.cursor()

        sql = """
            INSERT INTO ensalamento."aux_grupo_estagio" (
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
    """
    Executa a procedure de atualização das tabelas auxiliares.
    """
    conn = conectar()
    if conn is None:
        print("Conexão com o banco falhou.")
        return

    try:
        cursor = conn.cursor()
        cursor.execute("CALL ensalamento.upsert_all()")
        conn.commit()
        print("Tabelas auxiliares atualizadas com sucesso.")
    except Exception as e:
        print(f"Erro ao atualizar tabelas: {e}")
    finally:
        cursor.close()
        conn.close()
