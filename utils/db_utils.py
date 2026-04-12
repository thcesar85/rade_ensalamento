"""Utilities para gerenciamento de banco de dados e reutilização de código."""

from contextlib import contextmanager
from typing import Generator, Optional, Any, Callable, List, Dict, Tuple
import logging

from config.conn import conectar

logger = logging.getLogger(__name__)


@contextmanager
def get_db_connection() -> Generator:
    """Context manager para gerenciamento seguro de conexão BD.
    
    Garante que a conexão seja fechada mesmo com exceções.
    
    Yields:
        Conexão com banco de dados
        
    Raises:
        ConnectionError: Se não conseguir conectar ao banco
    """
    conn = conectar()
    if conn is None:
        raise ConnectionError("Falha ao conectar ao banco de dados.")
    
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def get_db_cursor(conn) -> Generator:
    """Context manager para gerenciamento seguro de cursor BD.
    
    Yields:
        Cursor do banco de dados
    """
    cursor = conn.cursor()
    try:
        yield cursor
    finally:
        cursor.close()


def execute_query(
    query: str,
    params: Optional[Tuple] = None,
    fetch_one: bool = False,
) -> Any:
    """Executa uma query SELECT de forma segura com gerenciamento automático.
    
    Args:
        query: Query SQL a executar
        params: Parâmetros SQL em tupla (opcional)
        fetch_one: Se True, retorna um resultado; se False, retorna todos
        
    Returns:
        Resultado da query ou lista de resultados
    """
    with get_db_connection() as conn:
        with get_db_cursor(conn) as cursor:
            cursor.execute(query, params or ())
            return cursor.fetchone() if fetch_one else cursor.fetchall()


def execute_update(
    query: str,
    params: Optional[Tuple] = None,
) -> int:
    """Executa UPDATE/INSERT/DELETE e commita automaticamente.
    
    Args:
        query: Query SQL a executar
        params: Parâmetros SQL em tupla (opcional)
        
    Returns:
        Número de linhas afetadas
    """
    with get_db_connection() as conn:
        with get_db_cursor(conn) as cursor:
            cursor.execute(query, params or ())
            conn.commit()
            return cursor.rowcount


def execute_many(
    query: str,
    data: List[Tuple],
) -> int:
    """Executa uma query múltiplas vezes com múltiplos parâmetros.
    
    Args:
        query: Query SQL a executar
        data: Lista de tuplas com parâmetros
        
    Returns:
        Número de linhas afetadas
    """
    with get_db_connection() as conn:
        with get_db_cursor(conn) as cursor:
            cursor.executemany(query, data)
            conn.commit()
            return cursor.rowcount


def execute_transaction(
    callback: Callable,
    *args,
    **kwargs,
) -> Any:
    """Executa uma função dentro de uma transação com rollback automático.
    
    Args:
        callback: Função a executar (recebe conn como primeiro argumento)
        *args: Argumentos adicionais para a função
        **kwargs: Argumentos nomeados adicionais
        
    Returns:
        Resultado da função
        
    Raises:
        Propaga a exceção se a transação falhar
    """
    with get_db_connection() as conn:
        try:
            result = callback(conn, *args, **kwargs)
            conn.commit()
            return result
        except Exception as error:
            conn.rollback()
            logger.error(f"Transação falhou: {error}", exc_info=True)
            raise


def normalize_string(value: Optional[str]) -> Optional[str]:
    """Normaliza string removendo espaços e lidando com nulos.
    
    Args:
        value: String a normalizar
        
    Returns:
        String normalizada ou None
    """
    if value is None or str(value).lower() == "nan":
        return None
    normalized = str(value).strip()
    return normalized if normalized else None


def normalize_cpf(cpf: Optional[str]) -> Optional[str]:
    """Normaliza CPF removendo caracteres especiais.
    
    Args:
        cpf: CPF a normalizar
        
    Returns:
        CPF normalizado (apenas números) ou None se inválido
    """
    if not cpf:
        return None
    
    cpf_cleaned = "".join(filter(str.isdigit, str(cpf)))
    return cpf_cleaned if len(cpf_cleaned) == 11 else None
