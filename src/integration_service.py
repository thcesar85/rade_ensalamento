import os
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from src.read_excel_agendamento import importar_agendamento_excel
from utils.db_functions import truncar_tabelas_auxiliares, lista_nome_grupo, processar_integracao_estagio
from src.read_api_groupcode import fetch_group_data_by_name, save_group_data, refresh_tables
from utils.validador_integracao import ValidadorIntegracao
from src.gera_relatorio_validacao import gerar_relatorio_validacao
from src.import_data_to_ensalamento import enviar_dados_api_ensalamento
import traceback
from utils.db_functions import lista_codigo_grupo

load_dotenv()

EXCEL_DIR = os.getenv("INPUT_EXCEL_DIR", "dados")
LOG_DIR = os.getenv("LOG_DIR", "dados/logs")
os.makedirs(LOG_DIR, exist_ok=True)

def salvar_log(linhas, sucesso=True):
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    status = "sucesso" if sucesso else "falha"
    nome_arquivo = os.path.join(LOG_DIR, f"integracao_{status}_{now}.log")
    with open(nome_arquivo, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas))

def executar_integracao_terminal(filepath):
    logs = []
    val_erros_log = []  # Para log separado de erros de validação
    houve_erro_critico = False
    erros_nao_criticos = {}

    def registrar(mensagem):
        print(mensagem)
        logs.append(mensagem)

    try:
        registrar("Limpando tabelas auxiliares...")
        truncar_tabelas_auxiliares()

        registrar(f"Importando planilha: {filepath}")
        importar_agendamento_excel(filepath)

        registrar("Buscando nomes de grupos...")
        lista_nomes = lista_nome_grupo()

        for nome in lista_nomes:
            registrar(f"Buscando grupo na API: {nome}")
            try:
                grupos = fetch_group_data_by_name(nome)
                registrar(f"API retornou {len(grupos)} grupo(s) para '{nome}'")

                if not grupos:
                    registrar(f"Nenhum grupo encontrado para '{nome}'")

                for grupo in grupos:
                    nome_grupo = grupo.get('name', 'sem nome')
                    registrar(f"Tentando salvar grupo '{nome_grupo}'...")

                    try:
                        save_group_data(grupo)
                        registrar(f"Grupo '{nome_grupo}' salvo com sucesso.")
                    except Exception as e:
                        registrar(f"Erro ao salvar grupo '{nome_grupo}': {e}")
                        registrar(traceback.format_exc())
            except Exception as e:
                registrar(f"Erro ao buscar grupo '{nome}': {e}")
                registrar(traceback.format_exc())

        refresh_tables()

        registrar("Iniciando validações...")
        validador = ValidadorIntegracao()
        df_escola = validador.validar_escola()
        df_grupo = validador.validar_grupo()
        df_tarefa = validador.validar_tarefa()
        df_place = validador.validar_place()
        validador.fechar_conexao()

        gerar_relatorio_validacao(df_escola, df_grupo, df_tarefa, df_place)

        # Organização das validações
        validacoes = {
            "escola": {"df": df_escola, "critico": False},
            "grupo":  {"df": df_grupo,  "critico": False},
            "tarefa": {"df": df_tarefa, "critico": False},
            "local":  {"df": df_place,  "critico": False}
        }

        for nome, dados in validacoes.items():
            df = dados["df"]
            if not df.empty:
                msg_erro = f"Erros de {nome} detectados:"
                registrar(msg_erro)
                registrar(df.to_string(index=False))
                val_erros_log.append(msg_erro)
                val_erros_log.append(df.to_string(index=False))
                if dados["critico"]:
                    houve_erro_critico = True
                else:
                    erros_nao_criticos[nome] = df

        # Salvar TXT com erros de validação (se houver)
        if val_erros_log:
            nome_txt = os.path.join(
                LOG_DIR,
                f"validacao_erros_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            )
            with open(nome_txt, "w", encoding="utf-8") as f:
                f.write("\n".join(val_erros_log))

        if houve_erro_critico:
            registrar("Validações críticas falharam. Integração interrompida.")
            salvar_log(logs, sucesso=False)
            return False, "Erro de validação. Clique no botão 'Abrir Último TXT de Erros de Validação' para detalhes."

        registrar("Validações concluídas. Gerando execução...")
        execution_id = processar_integracao_estagio()

        if execution_id:
            registrar(f"Execução gerada com ID: {execution_id}")
            grupos = lista_codigo_grupo()              # fallback

            if not grupos:
                registrar("Nenhum groupcode encontrado para esta execução (nada para enviar).")
                salvar_log(logs, sucesso=True)
                return True, "Integração finalizada (sem grupos pendentes)."

            registrar(f"Groupcodes encontrados: {grupos}")

            houve_falha = False
            for grupo in grupos:
                registrar(f"Enviando dados para groupcode={grupo}...")
                sucesso = enviar_dados_api_ensalamento(execution_id, group_code=grupo)
                if not sucesso:
                    houve_falha = True
                    registrar(f"Falha no envio do groupcode={grupo}. Verifique o resumo no diretório de logs.")
                else:
                    registrar(f"Envio concluído para groupcode={grupo}.")

            if not houve_falha:
                registrar("Dados enviados para a API com sucesso.")
                salvar_log(logs, sucesso=True)
                return True, "Integração finalizada com sucesso."
            else:
                registrar("Dados enviados com falhas. Verifique o resumo no diretório de logs.")
                salvar_log(logs, sucesso=False)
                return False, "Integração finalizada com falhas. Verifique o log."

        else:
            registrar("Falha ao gerar execução.")
            salvar_log(logs, sucesso=False)
            return False, "Erro ao gerar execução."

    except Exception as e:
        registrar(f"Erro inesperado: {e}")
        registrar(traceback.format_exc())
        salvar_log(logs, sucesso=False)
        return False, f"Erro inesperado: {e}"
