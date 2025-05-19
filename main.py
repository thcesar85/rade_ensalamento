from src.read_api_groupcode import save_group_data, refresh_tables, fetch_group_data_by_code
from src.read_excel_agendamento import importar_agendamento_excel
from utils.db_functions import (
    lista_codigo_grupo,
    truncar_tabelas_auxiliares,
    processar_integracao_estagio
)
from src.import_data_to_ensalamento import enviar_dados_api_ensalamento
from config.config import EXCEL_DIR
import warnings
warnings.filterwarnings("ignore", message="pandas only supports SQLAlchemy")

def main():
    excel_file = f"{EXCEL_DIR}/agendamento.xlsx"

    try:
        print("Limpando tabelas auxiliares...")
        truncar_tabelas_auxiliares()

        print("Iniciando a importação da planilha de agendamento...")
        importar_agendamento_excel(excel_file)

        print("Obtendo lista de grupos...")
        lista_grupos = lista_codigo_grupo()

        print("Iniciando extração dos grupos...")
        for codigo in lista_grupos:
            grupos = fetch_group_data_by_code(codigo)
            for grupo in grupos:
                save_group_data(grupo)

        refresh_tables()

        print("Processando integração...")
        execution_id = processar_integracao_estagio()

        if execution_id:
            print(f"Execução registrada: {execution_id}")
            print("Enviando dados para a API...")
            enviar_dados_api_ensalamento(execution_id)
        else:
            print("Falha ao gerar execução.")

    except Exception as e:
        print(f"Erro durante o processamento: {e}")

if __name__ == "__main__":
    main()
