"""Módulo de conexão com o banco de dados PostgreSQL."""

import logging
from typing import Optional

import psycopg2
from psycopg2 import OperationalError

from config.config import DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, DB_PORT

logger = logging.getLogger(__name__)


def conectar() -> Optional[psycopg2.extensions.connection]:
    """Estabelece conexão com o banco de dados PostgreSQL.
    
    Returns:
        Optional[psycopg2.extensions.connection]: Conexão com o banco ou None em caso de erro.
    """
    campos = {
        "DB_HOST": DB_HOST,
        "DB_NAME": DB_NAME,
        "DB_USER": DB_USER,
        "DB_PASSWORD": DB_PASSWORD,
        "DB_PORT": DB_PORT,
    }

    # Verifica se há variáveis ausentes (None ou string vazia)
    ausentes = [k for k, v in campos.items() if not v]
    if ausentes:
        logger.error(f"Variáveis de ambiente ausentes: {', '.join(ausentes)}")
        return None

    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT
        )
        logger.info("Conexão com o banco estabelecida com sucesso.")
        return conn
    except OperationalError as e:
        logger.error(f"Falha ao conectar no banco: {e}")
        return None


def testar_conexao() -> None:
    """Testa a conexão com o banco de dados."""
    conn = conectar()
    if not conn:
        logger.error("Não foi possível conectar ao banco de dados.")
        return

    try:
        cursor = conn.cursor()
        cursor.execute('SELECT 1;')
        logger.info("Teste de conexão bem-sucedido!")
    except Exception as e:
        logger.error(f"Falha ao executar consulta de teste: {e}")
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        conn.close()
