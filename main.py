from src.read_api_groupcode import save_group_data, refresh_tables, fetch_group_data_by_name
from src.read_excel_agendamento import importar_agendamento_excel
from utils.db_functions import (
    lista_nome_grupo,
    truncar_tabelas_auxiliares,
    processar_integracao_estagio
)
from src.import_data_to_ensalamento import enviar_dados_api_ensalamento
from utils.validador_integracao import ValidadorIntegracao
from src.gera_relatorio_validacao import gerar_relatorio_validacao
from config.config import EXCEL_DIR
import pandas as pd
from datetime import datetime
import warnings
warnings.filterwarnings("ignore", message="pandas only supports SQLAlchemy")

def main():
    excel_file = f"{EXCEL_DIR}/agendamento.xlsx"

    try:
        print("Limpando tabelas auxiliares...")
        truncar_tabelas_auxiliares()

        print("Importando planilha de agendamento...")
        importar_agendamento_excel(excel_file)

        print("Obtendo lista de grupos...")
        lista_nomes = lista_nome_grupo()

        print("Iniciando extração dos grupos na API...")
        for nome in lista_nomes:
            grupos = fetch_group_data_by_name(nome)
            for grupo in grupos:
                save_group_data(grupo)

        refresh_tables()

        print("Iniciando validação dos dados antes da integração...")
        validador = ValidadorIntegracao()

        df_escola = validador.validar_escola()
        df_grupo = validador.validar_grupo()
        df_tarefa = validador.validar_tarefa()
        df_place = validador.validar_place()

        validador.fechar_conexao()

        gerar_relatorio_validacao(df_escola, df_grupo, df_tarefa, df_place)

        houve_erro = False

        if not df_escola.empty:
            print("Erros de escola:")
            print(df_escola)
            houve_erro = True

        if not df_grupo.empty:
            print("Erros de grupo:")
            print(df_grupo)
            houve_erro = True

        if not df_tarefa.empty:
            print("Erros de tarefa vinculada ao grupo:")
            print(df_tarefa)
            houve_erro = True

        if not df_place.empty:
            print("Erros de place:")
            print(df_place)
            houve_erro = True

        if houve_erro:
            print("Validação encontrou inconsistências. Processo encerrado sem enviar para a API.")
            return

        print("Validação concluída sem erros. Seguindo para geração da execução e envio...")

        execution_id = processar_integracao_estagio()

        if execution_id:
            print(f"Execução registrada: {execution_id}")
            print("Enviando dados para a API...")
            enviar_dados_api_ensalamento(execution_id)
            print("Integração e envio concluídos com sucesso!")
        else:
            print("Falha ao gerar execução.")

    except Exception as e:
        print(f"Erro durante o processamento: {e}")

if __name__ == "__main__":
    main()
