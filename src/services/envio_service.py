import os
import json
import logging
import time
from typing import List, Optional, Tuple

import pandas as pd
import requests

from config.config import API_AUTHORIZATION, API_URL_BASE, API_TIMEOUT_CONNECT, API_TIMEOUT_READ, API_MAX_RETRIES, API_RETRY_BACKOFF_FACTOR
from src.repositories.integracao_repository import IntegracaoRepository
from src.models.integracao_models import ActivityPayload, SummaryRow
from utils.db_utils import get_db_connection
from utils.db_functions import get_group_active_status, GroupCacheManager

logger = logging.getLogger(__name__)

API_BASE_URL = API_URL_BASE.rstrip("/")
DEFAULT_TIMEOUT = (API_TIMEOUT_CONNECT, API_TIMEOUT_READ)
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
        logger.info(f"[{execution_id}] Iniciando envio de dados (group_code={group_code or 'todos'})")
        cache_manager = GroupCacheManager()
        
        try:
            with get_db_connection() as conn:
                if not resumo_csv_path:
                    resumo_csv_path = os.path.join(LOG_DIR, f"resumo_envio_{execution_id}.csv")
                os.makedirs(LOG_DIR, exist_ok=True)
                csv_ja_existe = os.path.exists(resumo_csv_path)

                df = self.repository.fetch_not_integrated_rows(conn, execution_id, group_code)
                if df.empty:
                    logger.info(f"[{execution_id}] Nenhum dado encontrado para enviar.")
                    return True
                
                logger.info(f"[{execution_id}] Total de {len(df)} registros para processar")

                df = _normalize_dataframe(df)
                houve_falha = False
                linhas_resumo: List[SummaryRow] = []
                url = f"{API_BASE_URL}/activity"
                headers = _auth_headers()
                if not headers.get("Authorization"):
                    raise RuntimeError("API_AUTHORIZATION vazio/não configurado.")

                session = requests.Session()
                with conn.cursor() as cursor:
                    logger.info(f"[{execution_id}] Iniciando processamento de {len(df)} linhas")
                    for idx, (_, row) in enumerate(df.iterrows(), 1):
                        logger.debug(f"[{execution_id}] Processando linha {idx}/{len(df)}")
                        houve_falha = self._process_row(
                            session, url, headers, cursor, execution_id, row, 
                            houve_falha, linhas_resumo, cache_manager=cache_manager
                        )

                    self._write_summary_csv(resumo_csv_path, linhas_resumo, csv_ja_existe)
                    status = "ERRO" if houve_falha else "CONCLUIDA"
                    self.repository.update_execution_status(cursor, execution_id, status)
                    conn.commit()

                # Log estatísticas do cache
                hits, misses, hit_rate, size = cache_manager.stats()
                logger.info(f"[{execution_id}] Cache Stats - Hits: {hits}, Misses: {misses}, Hit Rate: {hit_rate:.1f}%, Size: {size}")

                return not houve_falha

        except ValueError as ve:
            logger.error(f"[{execution_id}] Erro de validação de dados: {ve}", exc_info=True)
            try:
                with get_db_connection() as conn:
                    with conn.cursor() as cursor:
                        self.repository.record_execution_error(cursor, execution_id, f"Erro de validação: {str(ve)}")
                        conn.commit()
            except Exception as db_error:
                logger.error(f"[{execution_id}] Erro ao registrar falha: {db_error}")
            return False
            
        except RuntimeError as re:
            logger.error(f"[{execution_id}] Erro de configuração: {re}", exc_info=True)
            try:
                with get_db_connection() as conn:
                    with conn.cursor() as cursor:
                        self.repository.record_execution_error(cursor, execution_id, f"Erro de configuração: {str(re)}")
                        conn.commit()
            except Exception as db_error:
                logger.error(f"[{execution_id}] Erro ao registrar falha: {db_error}")
            return False
            
        except Exception as error:
            logger.error(f"[{execution_id}] Erro ao processar envio: {error}", exc_info=True)
            try:
                with get_db_connection() as conn:
                    with conn.cursor() as cursor:
                        self.repository.record_execution_error(cursor, execution_id, str(error))
                        conn.commit()
            except Exception as db_error:
                logger.error(f"[{execution_id}] Erro ao registrar falha: {db_error}")
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
        cache_manager: Optional[GroupCacheManager] = None,
    ) -> bool:
        """Processa uma linha de dados com validações robustas.
        
        Args:
            session: Sessão requests.
            url: URL da API.
            headers: Headers HTTP.
            cursor: Cursor de banco de dados.
            execution_id: ID da execução.
            row: Linha de dados.
            houve_falha: Indicador se houve falha anterior.
            linhas_resumo: Lista de linhas de resumo.
            cache_manager: Gerenciador de cache de grupos.
            
        Returns:
            bool: True se houve falha, False caso contrário.
        """
        cpf = row["cpf_estudante"]
        start = row["start_time"]
        end = row["end_time"]
        group_code = row["groupcode"]

        try:
            # VALIDAÇÃO 1: Verifica CPF
            if not cpf or str(cpf).strip() == "":
                mensagem = "CPF ausente/nulo - registro ignorado"
                logger.warning(f"[{execution_id}] {mensagem} (grupo={group_code})")
                self.repository.insert_log_entry(
                    cursor, execution_id, row["id"], mensagem, 400, mensagem, [], [{"cpf": "missing"}]
                )
                linhas_resumo.append(
                    _create_summary_row(row, "", start, end, False, 400, mensagem)
                )
                return houve_falha

            # VALIDAÇÃO 2: Verifica se grupo está ativo
            is_active = get_group_active_status(group_code, cache_manager=cache_manager)
            if is_active is False:
                mensagem = "Grupo inativo - envio cancelado"
                logger.info(f"[{execution_id}] Grupo {group_code} inativo. Pulando envio para CPF {cpf}")
                self.repository.insert_log_entry(
                    cursor, execution_id, row["id"], mensagem, 200, mensagem, [], []
                )
                linhas_resumo.append(
                    _create_summary_row(row, cpf, start, end, False, 200, mensagem)
                )
                return houve_falha
            
            if is_active is None:
                mensagem = "Grupo não encontrado no banco - envio cancel​ado"
                logger.warning(f"[{execution_id}] {mensagem} (grupo={group_code})")
                self.repository.insert_log_entry(
                    cursor, execution_id, row["id"], mensagem, 404, mensagem, [], [{"group": "not_found"}]
                )
                linhas_resumo.append(
                    _create_summary_row(row, cpf, start, end, False, 404, mensagem)
                )
                return True  # Conta como falha

            # VALIDAÇÃO 3: Constrói e valida payload
            try:
                payload = _build_payload(row)
            except (KeyError, ValueError, TypeError) as payload_error:
                mensagem = f"Erro ao construir payload: {str(payload_error)}"
                logger.error(f"[{execution_id}] {mensagem}")
                self.repository.insert_log_entry(
                    cursor, execution_id, row["id"], mensagem, 400, mensagem, [], [{"error": str(payload_error)}]
                )
                linhas_resumo.append(
                    _create_summary_row(row, cpf, start, end, False, 400, "Erro de dados")
                )
                return True
            
            # ENVIO: Tenta com retries
            status_code, response_text, response = self._send_request(
                session, url, headers, payload, execution_id=execution_id
            )
            mensagem, retorno_data, retorno_erros = _parse_response(response)

            success = bool(response and response.ok)
            if success:
                logger.debug(f"[{execution_id}] Envio bem-sucedido para CPF {cpf}")
                self.repository.mark_record_integrated(cursor, row["id"])
            else:
                logger.warning(f"[{execution_id}] Falha no envio para CPF {cpf}: HTTP {status_code}")
                houve_falha = True

            self.repository.insert_log_entry(
                cursor,
                execution_id,
                row["id"],
                response_text or "sem resposta",
                status_code,
                mensagem or "sem mensagem",
                retorno_data or [],
                retorno_erros or [],
            )
            linhas_resumo.append(
                _create_summary_row(row, cpf, start, end, success, status_code, mensagem)
            )
            return houve_falha

        except Exception as row_error:
            mensagem = f"Erro inesperado ao processar linha: {str(row_error)}"
            logger.error(f"[{execution_id}] {mensagem}", exc_info=True)
            self.repository.insert_log_entry(
                cursor, execution_id, row["id"], mensagem, 500, mensagem, [], [{"error": str(row_error)}]
            )
            linhas_resumo.append(
                _create_summary_row(row, cpf, start, end, False, 500, "Erro interno")
            )
            return True

    @staticmethod
    def _send_request(session: requests.Session, url: str, headers: dict, payload: ActivityPayload, execution_id: str = ""):
        """Envia requisição HTTP POST com retries exponenciais e tratamento robusto de erros.
        
        Args:
            session: Sessão requests.
            url: URL destino.
            headers: Headers HTTP.
            payload: Payload da requisição.
            execution_id: ID da execução para logging.
            
        Returns:
            Tuple[int, str, Optional[requests.Response]]: Status code, response text, response object.
        """
        max_attempts = API_MAX_RETRIES
        backoff_factor = API_RETRY_BACKOFF_FACTOR
        last_error = None
        
        # Validação de entrada
        if not url or not isinstance(url, str):
            logger.error(f"[{execution_id}] URL inválida: {url}")
            return 400, "URL inválida", None
        
        if not headers or not isinstance(headers, dict):
            logger.error(f"[{execution_id}] Headers inválidos")
            return 400, "Headers inválidos", None
        
        if payload is None:
            logger.error(f"[{execution_id}] Payload nulo")
            return 400, "Payload nulo", None
        
        for attempt in range(1, max_attempts + 1):
            try:
                logger.debug(f"[{execution_id}] Tentativa {attempt}/{max_attempts} de envio para {url}")
                
                # Timeout: conecta em 5s, lê em 20s
                response = session.post(
                    url, 
                    headers=headers, 
                    json={"data": [payload.to_dict()]}, 
                    timeout=DEFAULT_TIMEOUT,
                    verify=True  # Valida certificado SSL
                )
                
                logger.debug(f"[{execution_id}] Status {response.status_code} recebido")
                
                # Valida resposta
                if response.status_code >= 500:
                    # Erro no servidor - tenta retry
                    if attempt < max_attempts:
                        logger.warning(f"[{execution_id}] Erro no servidor ({response.status_code}) - tentará novamente")
                        delay = (2 ** (attempt - 1)) * backoff_factor
                        time.sleep(delay)
                        continue
                    else:
                        logger.error(f"[{execution_id}] Erro no servidor após {max_attempts} tentativas")
                        return response.status_code, response.text or "Erro no servidor", response
                
                return response.status_code, response.text, response
                
            except requests.exceptions.Timeout as exc:
                last_error = exc
                logger.warning(f"[{execution_id}] Timeout na tentativa {attempt}/{max_attempts}: {exc}")
                if attempt < max_attempts:
                    delay = (2 ** (attempt - 1)) * backoff_factor
                    logger.info(f"[{execution_id}] Aguardando {delay:.1f}s antes de retry (timeout)...")
                    time.sleep(delay)
                else:
                    logger.error(f"[{execution_id}] Timeout após {max_attempts} tentativas")
                    return 408, f"Timeout após {max_attempts} tentativas: {str(exc)}", None
                    
            except requests.exceptions.ConnectionError as exc:
                last_error = exc
                logger.warning(f"[{execution_id}] Erro de conexão na tentativa {attempt}/{max_attempts}: {exc}")
                if attempt < max_attempts:
                    delay = (2 ** (attempt - 1)) * backoff_factor
                    logger.info(f"[{execution_id}] Aguardando {delay:.1f}s antes de retry (conexão)...")
                    time.sleep(delay)
                else:
                    logger.error(f"[{execution_id}] Erro de conexão após {max_attempts} tentativas")
                    return 503, f"Erro de conexão após {max_attempts} tentativas: {str(exc)}", None
                    
            except requests.exceptions.HTTPError as exc:
                last_error = exc
                logger.error(f"[{execution_id}] Erro HTTP na tentativa {attempt}/{max_attempts}: {exc}")
                if attempt < max_attempts and exc.response.status_code >= 500:
                    delay = (2 ** (attempt - 1)) * backoff_factor
                    logger.info(f"[{execution_id}] Aguardando {delay:.1f}s antes de retry (HTTP {exc.response.status_code})...")
                    time.sleep(delay)
                else:
                    return exc.response.status_code if exc.response else 500, str(exc), exc.response
                    
            except requests.exceptions.RequestException as exc:
                last_error = exc
                logger.error(f"[{execution_id}] Erro de requisição na tentativa {attempt}/{max_attempts}: {exc}")
                if attempt < max_attempts:
                    delay = (2 ** (attempt - 1)) * backoff_factor
                    logger.info(f"[{execution_id}] Aguardando {delay:.1f}s antes de retry (requisição)...")
                    time.sleep(delay)
                else:
                    logger.error(f"[{execution_id}] Erro de requisição após {max_attempts} tentativas")
                    return 599, f"Erro de requisição: {str(exc)}", None
            
            except ValueError as exc:
                logger.error(f"[{execution_id}] Erro de validação no payload na tentativa {attempt}: {exc}")
                return 400, f"Erro de validação: {str(exc)}", None
                
            except Exception as exc:
                logger.error(f"[{execution_id}] Erro inesperado na tentativa {attempt}/{max_attempts}: {exc}", exc_info=True)
                if attempt < max_attempts:
                    delay = (2 ** (attempt - 1)) * backoff_factor
                    logger.info(f"[{execution_id}] Aguardando {delay:.1f}s antes de retry (erro inesperado)...")
                    time.sleep(delay)
                else:
                    return 500, f"Erro inesperado: {str(exc)}", None
        
        # Fallback se sair do loop
        error_msg = f"Max retries exceeded: {str(last_error) if last_error else 'unknown'}"
        logger.error(f"[{execution_id}] {error_msg}")
        return 599, error_msg, None

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
