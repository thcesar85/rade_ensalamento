import pandas as pd
from datetime import datetime
from config.config import EXCEL_DIR


def gerar_relatorio_validacao(df_escola, df_grupo, df_tarefa, df_place):
    agora = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    nome_arquivo = f"{EXCEL_DIR}/relatorio_validacao_{agora}.xlsx"

    with pd.ExcelWriter(nome_arquivo, engine='openpyxl') as writer:
        if not df_escola.empty:
            df_escola.to_excel(writer, sheet_name='Erros_Escola', index=False)
        if not df_grupo.empty:
            df_grupo.to_excel(writer, sheet_name='Erros_Grupo', index=False)
        if not df_tarefa.empty:
            df_tarefa.to_excel(writer, sheet_name='Erros_Tarefa', index=False)
        if not df_place.empty:
            df_place.to_excel(writer, sheet_name='Erros_Place', index=False)

        # Se não houver erro, ainda cria uma aba indicando isso
        if df_escola.empty and df_grupo.empty and df_tarefa.empty and df_place.empty:
            pd.DataFrame([['Nenhum erro encontrado.']]).to_excel(
                writer, sheet_name='Sem_Erros', index=False, header=False
            )

    print(f"📄 Relatório de validação salvo em: {nome_arquivo}")
