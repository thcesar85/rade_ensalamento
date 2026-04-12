import os
import json
import logging
from typing import List, Optional

import pandas as pd
import requests

from config.config import API_AUTHORIZATION, API_URL_BASE
from src.repositories.integracao_repository import IntegracaoRepository
from src.models.integracao_models import ActivityPayload, SummaryRow
from utils.db_utils import get_db_connection

logger = logging.getLogger(__name__)

API_BASE_URL = API_URL_BASE.rstrip("/")
DEFAULT_TIMEOUT = (5, 20)  # (connect, read)
LOG_DIR = os.getenv("LOG_DIR", "dados/logs")


def _bearer(value: str) -> str:
    token = (value or "").strip()
    if not token:
        return ""
    if not token.lower().startswith("bearer "):
        return f"Bearer {token}"
    return token


def _auth_headers() -> dict:
    return {
        "Content-Type": "application/json",
        "Authorization": _bearer(str(API_AUTHORIZATION)),
    }


def _normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df["cpf_estudante"] = df["cpf_estudante"].apply(lambda value: None if pd.isna(value) else str(value).strip())
    df["data"] = df["data"].astype(str)
    df["start_time"] = df["start_time"].astype(str)
    df["end_time"] = df["end_time"].astype(str)
    return df


def _build_payload(row: pd.Series) -> ActivityPayload:
    return ActivityPayload(
        entityCode=str(row["entitycode"]),
        courseCode=str(row["coursecode"]),
        groupCode=str(row["groupcode"]),
        place=str(row["id_place"]),
        taskCode=str(row["taskcode"]),
        date=row["data"],
        startTime=row["start_time"],
        endTime=row["end_time"],
        students=[row["cpf_estudante"]],
    )


def _parse_response(response: Optional[requests.Response]):
    if not response or not response.headers.get("Content-Type", "").startswith("application/json"):
        return None, [], []
    try:
        payload = response.json()
        return payload.get("message"), payload.get("data", []), payload.get("errors", [])
    except Exception as error:
        return f"Erro ao interpretar JSON: {error}", [], []


def _create_summary_row(row: pd.Series, cpf: str, start: str, end: str, success: bool, http_status: int, mensagem: Optional[str]) -> SummaryRow:
    return SummaryRow(
        lobby_id=row["id"],
        entitycode=row["entitycode"],
        course=row["coursecode"],
        grupo=row["groupcode"],
        cpf=cpf or "",
        data=row["data"],
        hora=f"{start}-{end}",
        status="sucesso" if success else "erro",
        http=http_status,
        mensagem=mensagem or "sem mensagem",
    )


class EnvioService:
    """Serviço responsável pelo envio de dados à API de ensalamento."""

    def __init__(self, repository: Optional[IntegracaoRepository] = None):
        """Inicializa o serviço.
        
        Args:
            repository: Repository para operações de banco de dados.
        """
        self.repository = repository or IntegracaoRepository()

    def enviar_dados(self, execution_id: str, group_code: Optional[str] = None, resumo_csv_path: Optional[str] = None) -> bool:
        """Envia dados à API de ensalamento.
        
        Args:
            execution_id: ID da execução de integração.
            group_code: Código do grupo (opcional).
            resumo_csv_path: Caminho para salvar resumo em CSV (opcional).
            
        Returns:
            bool: True se sucesso, False caso contrário.
        """
        try:
            with get_db_connection() as conn:
                if not resumo_csv_path:
                    resumo_csv_path = os.path.join(LOG_DIR, f"resumo_envio_{execution_id}.csv")
                os.makedirs(LOG_DIR, exist_ok=True)
                csv_ja_existe = os.path.exists(resumo_csv_path)

                df = self.repository.fetch_not_integrated_rows(conn, execution_id, group_code)
                if df.empty:
                    logger.info("Nenhum dado encontrado para enviar.")
                    return True

                df = _normalize_dataframe(df)
                houve_falha = False
                linhas_resumo: List[SummaryRow] = []
                url = f"{API_BASE_URL}/activity"
                headers = _auth_headers()
                if not headers.get("Authorization"):
                    raise RuntimeError("API_AUTHORIZATION vazio/não configurado.")

                session = requests.Session()
                with conn.cursor() as cursor:
                    for _, row in df.iterrows():
                        houve_falha = self._process_row(session, url, headers, cursor, execution_id, row, houve_falha, linhas_resumo)

                    self._write_summary_csv(resumo_csv_path, linhas_resumo, csv_ja_existe)
                    status = "ERRO" if houve_falha else "CONCLUIDA"
                    self.repository.update_execution_status(cursor, execution_id, status)
                    conn.commit()

                return not houve_falha

        except Exception as error:
            logger.error(f"Erro ao processar envio: {error}")
            try:
                with get_db_connection() as conn:
                    with conn.cursor() as cursor:
                        self.repository.record_execution_error(cursor, execution_id, str(error))
                        conn.commit()
            except Exception as db_error:
                logger.error(f"Erro ao registrar falha: {db_error}")
            return False

    def _process_row(
        self,
        session: requests.Session,
        url: str,
        headers: dict,
        cursor,
        execution_id: str,
        row,
        houve_falha: bool,
        linhas_resumo: List[SummaryRow],
    ) -> bool:
        """Processa uma linha de dados.
        
        Args:
            session: Sessão requests.
            url: URL da API.
            headers: Headers HTTP.
            cursor: Cursor de banco de dados.
            execution_id: ID da execução.
            row: Linha de dados.
            houve_falha: Indicador se houve falha anterior.
            linhas_resumo: Lista de linhas de resumo.
            
        Returns:
            bool: True se houve falha, False caso contrário.
        """
        cpf = row["cpf_estudante"]
        start = row["start_time"]
        end = row["end_time"]

        if not cpf:
            mensagem = "CPF ausente/nulo"
            self.repository.insert_log_entry(cursor, execution_id, row["id"], mensagem, 400, mensagem, [], [{"cpf": "missing"}])
            linhas_resumo.append(_create_summary_row(row, "", start, end, False, 400, mensagem))
            return True

        payload = _build_payload(row)
        status_code, response_text, response = self._send_request(session, url, headers, payload)
        mensagem, retorno_data, retorno_erros = _parse_response(response)

        success = bool(response and response.ok)
        if success:
            self.repository.mark_record_integrated(cursor, row["id"])
        else:
            houve_falha = True

        self.repository.insert_log_entry(
            cursor,
            execution_id,
            row["id"],
            response_text,
            status_code,
            mensagem,
            retorno_data,
            retorno_erros,
        )
        linhas_resumo.append(_create_summary_row(row, cpf, start, end, success, status_code, mensagem))
        return houve_falha

    @staticmethod
    def _send_request(session: requests.Session, url: str, headers: dict, payload: ActivityPayload):
        """Envia requisição HTTP POST.
        
        Args:
            session: Sessão requests.
            url: URL destino.
            headers: Headers HTTP.
            payload: Payload da requisição.
            
        Returns:
            Tuple[int, str, Optional[requests.Response]]: Status code, response text, response object.
        """
        try:
            response = session.post(url, headers=headers, json={"data": [payload.to_dict()]}, timeout=DEFAULT_TIMEOUT)
            return response.status_code, response.text, response
        except requests.RequestException as exc:
            return 599, str(exc), None

    @staticmethod
    def _write_summary_csv(resumo_csv_path: str, linhas_resumo: List[SummaryRow], csv_ja_existe: bool) -> None:
        """Escreve resumo em arquivo CSV.
        
        Args:
            resumo_csv_path: Caminho do arquivo CSV.
            linhas_resumo: Linhas de resumo.
            csv_ja_existe: Indicador se arquivo já existe.
        """
        df_resumo = pd.DataFrame([row.to_dict() for row in linhas_resumo])
        df_resumo.to_csv(
            resumo_csv_path,
            index=False,
            encoding="utf-8",
            mode="a",
            header=not csv_ja_existe,
        )
        logger.info(f"Resumo atualizado: {resumo_csv_path}")
