"""Repository para operações de banco de dados relacionadas à integração."""

import json
import logging
from typing import Dict, List, Optional, Tuple

import pandas as pd

from utils.db_utils import get_db_connection, get_db_cursor

logger = logging.getLogger(__name__)


class IntegracaoRepository:
    """Repository para operações de banco de dados relacionadas à integração."""

    SCHEMA = "ensalamento"
    TABLE_LOBBY = f'"{SCHEMA}"."tblobbyensalamento"'
    TABLE_LOG = f'"{SCHEMA}"."tblogintegracao"'
    TABLE_EXECUCAO = f'"{SCHEMA}"."tbexecucaointegracao"'

    @staticmethod
    def fetch_not_integrated_rows(conn, execution_id: str, group_code: Optional[str] = None) -> pd.DataFrame:
        """Busca registros não integrados do lobby de ensalamento."""
        query = f"""
            SELECT
                id, execution_id, entitycode, coursecode, groupcode, taskcode,
                id_place, place, data, start_time, end_time, cpf_estudante
            FROM {IntegracaoRepository.TABLE_LOBBY}
            WHERE execution_id = %s AND integrated = FALSE
        """
        params = [execution_id]

        if group_code is not None:
            query += " AND groupcode = %s"
            params.append(group_code)

        return pd.read_sql(query, conn, params=tuple(params))

    @staticmethod
    def mark_record_integrated(cursor, lobby_id: int) -> None:
        """Marca um registro do lobby como integrado."""
        cursor.execute(f"""
            UPDATE {IntegracaoRepository.TABLE_LOBBY}
            SET integrated = TRUE
            WHERE id = %s
        """, (lobby_id,))

    @staticmethod
    def insert_log_entry(
        cursor,
        execution_id: str,
        lobby_id: int,
        response: str,
        status_code: int,
        mensagem: Optional[str],
        retorno_data: Optional[List[Dict]] = None,
        retorno_erros: Optional[List[Dict]] = None,
    ) -> None:
        """Registra um log de tentativa de integração."""
        cursor.execute(f"""
            INSERT INTO {IntegracaoRepository.TABLE_LOG} (
                execution_id, lobby_id, response, status_code, mensagem, retorno_data, retorno_erros
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            execution_id,
            lobby_id,
            response,
            status_code,
            mensagem,
            json.dumps(retorno_data or [], ensure_ascii=False),
            json.dumps(retorno_erros or [], ensure_ascii=False),
        ))

    @staticmethod
    def update_execution_status(cursor, execution_id: str, status: str) -> None:
        """Atualiza o status de uma execução de integração."""
        cursor.execute(f"""
            UPDATE {IntegracaoRepository.TABLE_EXECUCAO}
            SET status = %s
            WHERE execution_id = %s
        """, (status, execution_id))

    @staticmethod
    def record_execution_error(cursor, execution_id: str, error_message: str) -> None:
        """Registra erro em uma execução de integração."""
        cursor.execute(f"""
            UPDATE {IntegracaoRepository.TABLE_EXECUCAO}
            SET status = 'ERRO', erro = %s
            WHERE execution_id = %s
        """, (error_message, execution_id))

