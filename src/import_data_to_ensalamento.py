from src.services.envio_service import EnvioService


def enviar_dados_api_ensalamento(execution_id, group_code=None, resumo_csv_path=None):
    """Ponto de entrada para envio de dados à API de ensalamento."""
    service = EnvioService()
    return service.enviar_dados(execution_id=execution_id, group_code=group_code, resumo_csv_path=resumo_csv_path)

