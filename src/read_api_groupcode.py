"""Serviço para buscar e salvar dados de grupos na API RADE."""

import os
import json
import logging
from typing import List, Dict, Optional
from datetime import datetime

import requests
from dotenv import load_dotenv

from config.config import API_URL_BASE, API_AUTHORIZATION
from src.api_context import get_selected_ies
from utils.db_utils import get_db_connection, get_db_cursor

logger = logging.getLogger(__name__)

# Carrega variáveis de ambiente
load_dotenv()

API_BASE_URL = API_URL_BASE


def fetch_group_data_by_name(nome_grupo: str) -> List[Dict]:
    """Busca dados de grupo na API RADE por nome.
    
    Args:
        nome_grupo: Nome do grupo a buscar
        
    Returns:
        Lista de dicionários com dados dos grupos encontrados
    """
    entity_code = get_selected_ies()
    if not entity_code:
        logger.warning("Nenhuma IES selecionada.")
        return []

    url = f"{API_BASE_URL}/group?entity={entity_code}&name={nome_grupo}"
    headers = {"Authorization": str(API_AUTHORIZATION)}

    try:
        response = requests.get(url, headers=headers, timeout=(5, 20))
        
        if response.status_code == 404:
            return []
        
        if response.status_code != 200:
            logger.error(f"Erro ao buscar grupo '{nome_grupo}': {response.status_code} - {response.text}")
            return []

        grupos = response.json()
        if not isinstance(grupos, list):
            logger.warning(f"Resposta inesperada da API para '{nome_grupo}': {grupos}")
            return []

        dados_filtrados = []
        for grupo in grupos:
            if isinstance(grupo, dict):
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
                logger.warning(f"Item inesperado na resposta da API para '{nome_grupo}': {grupo}")

        return dados_filtrados

    except Exception as error:
        logger.error(f"Erro ao processar grupo '{nome_grupo}': {error}", exc_info=True)
        return []


def save_group_data(grupo: Dict) -> bool:
    """Salva um grupo no banco de dados na tabela auxiliar.
    
    Args:
        grupo: Dicionário com dados do grupo
        
    Returns:
        True se salvo com sucesso, False caso contrário
    """
    sql = """
        INSERT INTO ensalamento."aux_grupo_estagio" (
            entity_code, entity, course_code, course, group_code, code,
            name, start_date, end_date, workload, daily_limit,
            weekly_limit, active, tasks, places
        ) VALUES (
            %(entityCode)s, %(entity)s, %(courseCode)s, %(course)s,
            %(groupCode)s, %(code)s, %(name)s, %(startDate)s, %(endDate)s,
            %(workload)s, %(dailyLimit)s, %(weeklyLimit)s, %(active)s,
            %(tasks)s, %(places)s
        )
    """

    try:
        grupo["tasks"] = json.dumps(grupo.get("tasks", []))
        grupo["places"] = json.dumps(grupo.get("places", []))

        with get_db_connection() as conn:
            with get_db_cursor(conn) as cursor:
                cursor.execute(sql, grupo)
                conn.commit()
        
        logger.info(f"Grupo {grupo.get('groupCode')} inserido com sucesso.")
        return True

    except Exception as error:
        logger.error(f"Erro ao inserir grupo {grupo.get('groupCode')}: {error}", exc_info=True)
        return False


def refresh_tables() -> bool:
    """Executa a procedure de atualização das tabelas auxiliares.
    
    Returns:
        True se executado com sucesso, False caso contrário
    """
    try:
        with get_db_connection() as conn:
            with get_db_cursor(conn) as cursor:
                cursor.execute("CALL ensalamento.upsert_all()")
                conn.commit()
        logger.info("Tabelas auxiliares atualizadas com sucesso.")
        return True
    except Exception as error:
        logger.error(f"Erro ao atualizar tabelas: {error}", exc_info=True)
        return False

