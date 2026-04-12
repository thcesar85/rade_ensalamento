"""Funções de banco de dados do projeto Ensalamento RADE."""

import uuid
import logging
from typing import List, Optional

from utils.db_utils import execute_query, execute_update, get_db_connection, get_db_cursor

logger = logging.getLogger(__name__)


def lista_nome_grupo() -> List[str]:
    """Busca os nomes únicos de grupos da tabela auxiliar de agendamento.
    
    Returns:
        Lista com nomes de grupos ou lista vazia em caso de erro
    """
    try:
        query = "SELECT DISTINCT grupo FROM ensalamento.\"aux_agendamento\""
        resultados = execute_query(query)
        return [linha[0] for linha in resultados if linha[0]]
    except Exception as error:
        logger.error(f"Erro ao buscar nomes de grupos: {error}")
        return []


def lista_codigo_grupo() -> List[str]:
    """Busca os códigos únicos de grupos da tabela auxiliar de agendamento.
    
    Returns:
        Lista com códigos de grupos ou lista vazia em caso de erro
    """
    try:
        query = "SELECT DISTINCT codigo_grupo FROM ensalamento.\"aux_agendamento\""
        resultados = execute_query(query)
        return [str(linha[0]) for linha in resultados if linha[0]]
    except Exception as error:
        logger.error(f"Erro ao buscar códigos de grupos: {error}")
        return []


def truncar_tabelas_auxiliares() -> bool:
    """Executa a procedure que trunca as tabelas auxiliares.
    
    Returns:
        True se executado com sucesso, False caso contrário
    """
    try:
        with get_db_connection() as conn:
            with get_db_cursor(conn) as cursor:
                cursor.execute("CALL ensalamento.truncate_aux_tables();")
                conn.commit()
        logger.info("Tabelas auxiliares truncadas com sucesso.")
        return True
    except Exception as error:
        logger.error(f"Erro ao truncar tabelas auxiliares: {error}", exc_info=True)
        return False


def processar_integracao_estagio() -> Optional[str]:
    """Gera um execution_id, chama a procedure de integração e retorna o ID.
    
    Returns:
        execution_id (UUID string) se bem-sucedido, None caso contrário
    """
    execution_id = str(uuid.uuid4())

    try:
        with get_db_connection() as conn:
            with get_db_cursor(conn) as cursor:
                logger.info(f"Iniciando processamento com execution_id: {execution_id}")
                cursor.execute(
                    "CALL ensalamento.processar_integracao_estagio(%s);",
                    (execution_id,)
                )
                conn.commit()
        
        logger.info("Processamento de integração concluído com sucesso.")
        return execution_id

    except Exception as error:
        logger.error(f"Erro ao processar integração: {error}", exc_info=True)
        return None