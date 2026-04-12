import os
from datetime import datetime
from dotenv import load_dotenv
from src.read_excel_agendamento import importar_agendamento_excel
from utils.db_functions import truncar_tabelas_auxiliares, lista_nome_grupo, processar_integracao_estagio
from src.read_api_groupcode import fetch_group_data_by_name, save_group_data, refresh_tables
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

def limpar_tabelas_auxiliares_step(logs, registrar):
    registrar("Limpando tabelas auxiliares...")
    truncar_tabelas_auxiliares()

def importar_planilha_step(filepath, logs, registrar):
    registrar(f"Importando planilha: {filepath}")
    importar_agendamento_excel(filepath)

def buscar_e_salvar_grupos_step(logs, registrar):
    registrar("Buscando nomes de grupos...")
    lista_nomes = lista_nome_grupo()

    for nome in lista_nomes:
        registrar(f"Buscando grupo na API: {nome}")
        try:
            grupos = fetch_group_data_by_name(nome)
            registrar(f"API retornou {len(grupos)} grupo(s) para '{nome}'")

            if not grupos:
                registrar(f"Nenhum grupo encontrado para '{nome}'")
                continue

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

def processar_execucao_step(logs, registrar):
    refresh_tables()

    registrar("Gerando execução...")
    execution_id = processar_integracao_estagio()

    if not execution_id:
        registrar("Falha ao gerar execução.")
        return False, "Erro ao gerar execução."

    registrar(f"Execução gerada com ID: {execution_id}")
    grupos = lista_codigo_grupo()

    if not grupos:
        registrar("Nenhum groupcode encontrado para esta execução (nada para enviar).")
        return True, "Integração finalizada (sem grupos pendentes)."

    registrar(f"Groupcodes encontrados: {grupos}")

    for grupo in grupos:
        registrar(f"Enviando dados para groupcode={grupo}...")
        sucesso = enviar_dados_api_ensalamento(execution_id, group_code=grupo)
        if not sucesso:
            registrar(f"Falha no envio do groupcode={grupo}. Verifique o resumo no diretório de logs.")
        else:
            registrar(f"Envio concluído para groupcode={grupo}.")

    registrar("Processo de envio concluído.")
    return True, "Integração finalizada com sucesso."

def executar_integracao_terminal(filepath):
    logs = []

    def registrar(mensagem):
        print(mensagem)
        logs.append(mensagem)

    try:
        limpar_tabelas_auxiliares_step(logs, registrar)
        importar_planilha_step(filepath, logs, registrar)
        buscar_e_salvar_grupos_step(logs, registrar)
        sucesso, mensagem = processar_execucao_step(logs, registrar)

        salvar_log(logs, sucesso=sucesso)
        return sucesso, mensagem

    except Exception as e:
        registrar(f"Erro inesperado: {e}")
        registrar(traceback.format_exc())
        salvar_log(logs, sucesso=False)
        return False, f"Erro inesperado: {e}"
