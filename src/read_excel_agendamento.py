"""Serviço para importar dados de agendamento do arquivo Excel."""

import logging
from typing import Optional

import pandas as pd

from utils.db_utils import get_db_connection, get_db_cursor

logger = logging.getLogger(__name__)


def importar_agendamento_excel(caminho_arquivo: str) -> bool:
    """Importa dados de agendamento de um arquivo Excel para o banco.
    
    Args:
        caminho_arquivo: Caminho para o arquivo Excel
        
    Returns:
        True se importação bem-sucedida, False caso contrário
    """
    logger.info("Iniciando importação do agendamento...")

    try:
        # Lê a planilha Excel
        df = pd.read_excel(caminho_arquivo)

        # Renomeia as colunas da planilha para os nomes usados no banco
        df.columns = [
            "escola", "curso", "grupo", "codigo_grupo", "estudante", "cpf_estudante",
            "atividade", "campo_estagio", "tarefa", "codigo_tarefa",
            "preceptor", "data", "dia_semana", "hora_inicio", "hora_final"
        ]

        sql = """
            INSERT INTO ensalamento."aux_agendamento" (
                escola, curso, grupo, codigo_grupo, estudante, cpf_estudante,
                atividade, campo_estagio, tarefa, codigo_tarefa,
                preceptor, data, dia_semana, hora_inicio, hora_final
            ) VALUES (
                %(escola)s, %(curso)s, %(grupo)s, %(codigo_grupo)s, %(estudante)s, %(cpf_estudante)s,
                %(atividade)s, %(campo_estagio)s, %(tarefa)s, %(codigo_tarefa)s,
                %(preceptor)s, %(data)s, %(dia_semana)s, %(hora_inicio)s, %(hora_final)s
            )
        """

        with get_db_connection() as conn:
            with get_db_cursor(conn) as cursor:
                for _, row in df.iterrows():
                    dados = {
                        "escola": row["escola"],
                        "curso": row["curso"],
                        "grupo": row["grupo"],
                        "codigo_grupo": row["codigo_grupo"],
                        "estudante": row["estudante"],
                        "cpf_estudante": row["cpf_estudante"],
                        "atividade": row["atividade"],
                        "campo_estagio": row["campo_estagio"],
                        "tarefa": row["tarefa"],
                        "codigo_tarefa": row["codigo_tarefa"],
                        "preceptor": row["preceptor"],
                        "data": pd.to_datetime(row["data"]).date() if not pd.isna(row["data"]) else None,
                        "dia_semana": row["dia_semana"],
                        "hora_inicio": row["hora_inicio"],
                        "hora_final": row["hora_final"]
                    }

                    cursor.execute(sql, dados)

                conn.commit()

        logger.info("Importação concluída com sucesso.")
        return True

    except Exception as error:
        logger.error(f"Erro durante a importação: {error}", exc_info=True)
        return False
