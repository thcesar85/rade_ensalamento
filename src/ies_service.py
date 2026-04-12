"""Serviço para gerenciamento de configurações IES."""

import logging
from dataclasses import dataclass
from typing import List, Optional

from utils.db_utils import execute_query

logger = logging.getLogger(__name__)


@dataclass
class IES:
    """Modelo de dados para Instituição de Ensino Superior."""
    id: int
    entity_name: str
    entity_code: str
    api_key: str


def list_active() -> List[IES]:
    """Busca todas as IES ativas configuradas no banco.
    
    Returns:
        Lista de objetos IES ativos ou lista vazia em caso de erro
    """
    query = """
        SELECT id, entity_name, entity_code, api_key
        FROM ensalamento.tbConfigIes
        WHERE is_active = TRUE
        ORDER BY entity_name
    """
    try:
        rows = execute_query(query)
        return [IES(id=row[0], entity_name=row[1], entity_code=row[2], api_key=row[3]) 
                for row in rows]
    except Exception as error:
        logger.error(f"Erro ao listar IES ativas: {error}", exc_info=True)
        return []


def get_by_id(ies_id: int) -> Optional[IES]:
    """Busca uma IES específica por ID.
    
    Args:
        ies_id: ID da IES a buscar
        
    Returns:
        Objeto IES ou None se não encontrada
    """
    query = """
        SELECT id, entity_name, entity_code, api_key
        FROM ensalamento.tbConfigIes
        WHERE id = %s AND is_active = TRUE
    """
    try:
        row = execute_query(query, params=(ies_id,), fetch_one=True)
        if not row:
            return None
        return IES(id=row[0], entity_name=row[1], entity_code=row[2], api_key=row[3])
    except Exception as error:
        logger.error(f"Erro ao buscar IES id={ies_id}: {error}", exc_info=True)
        return None
