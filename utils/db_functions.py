"""Funções de banco de dados do projeto Ensalamento RADE."""

import uuid
import logging
from typing import List, Optional, Dict

from utils.db_utils import execute_query, execute_update, get_db_connection, get_db_cursor

logger = logging.getLogger(__name__)


# ============================================================================
# ITEM 3: Cache Manager - Sistema de cache em memória para grupos e status
# ============================================================================

class GroupCacheManager:
    """Gerenciador de cache em memória para dados de grupos."""
    
    def __init__(self):
        """Inicializa o cache."""
        self._cache: Dict[str, Optional[bool]] = {}
        self._hits = 0
        self._misses = 0
    
    def get(self, key: str) -> Optional[bool]:
        """Obtém valor do cache."""
        if key in self._cache:
            self._hits += 1
            logger.debug(f"[CACHE] HIT: {key} (hits={self._hits}, misses={self._misses})")
            return self._cache[key]
        self._misses += 1
        logger.debug(f"[CACHE] MISS: {key} (hits={self._hits}, misses={self._misses})")
        return None
    
    def set(self, key: str, value: Optional[bool]) -> None:
        """Armazena valor no cache."""
        self._cache[key] = value
        logger.debug(f"[CACHE] SET: {key} = {value}")
    
    def stats(self) -> tuple:
        """Retorna estatísticas do cache."""
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0
        return self._hits, self._misses, hit_rate, len(self._cache)
    
    def clear(self) -> None:
        """Limpa o cache."""
        self._cache.clear()
        logger.debug(f"[CACHE] Cache limpo")


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


def get_group_active_status(group_code: str, cache_manager: Optional['GroupCacheManager'] = None) -> Optional[bool]:
    """Busca o status ativo de um grupo pelo code com cache.
    
    Args:
        group_code: Código do grupo a verificar
        cache_manager: Gerenciador de cache (opcional)
        
    Returns:
        True se grupo está ativo, False se inativo, None se não encontrado
    """
    try:
        # Verifica cache primeiro
        if cache_manager is not None:
            cached_value = cache_manager.get(group_code)
            if cached_value is not None:
                return cached_value
        
        # Query no banco
        query = """
            SELECT active FROM ensalamento."tbGroup" 
            WHERE code = %s 
            LIMIT 1
        """
        results = execute_query(query, (group_code,))
        
        if results and len(results) > 0:
            active_status = results[0][0]
            # Armazena no cache manager
            if cache_manager is not None:
                cache_manager.set(group_code, active_status)
            logger.debug(f"Buscado do BD: {group_code} = {active_status}")
            return active_status
        
        logger.warning(f"Grupo {group_code} não encontrado na tbGroup")
        return None
        
    except Exception as error:
        logger.error(f"Erro ao buscar status ativo do grupo {group_code}: {error}")
        return None