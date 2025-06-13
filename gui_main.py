import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from utils.db_config import get_db_config, save_db_config
from src.read_excel_agendamento import importar_agendamento_excel
from utils.db_functions import (
    truncar_tabelas_auxiliares,
    lista_nome_grupo,
    processar_integracao_estagio
)
from src.read_api_groupcode import (
    fetch_group_data_by_name,
    save_group_data,
    refresh_tables
)
from src.import_data_to_ensalamento import enviar_dados_api_ensalamento
from src.relatorio_execucao import gerar_relatorio_por_data
from utils.validador_integracao import ValidadorIntegracao
from src.gera_relatorio_validacao import gerar_relatorio_validacao

def abrir_janela_status():
    status_window = tk.Toplevel(app)
    status_window.title("Processando Integração...")
    status_window.geometry("500x400")

    log = scrolledtext.ScrolledText(status_window, width=60, height=20, state='disabled')
    log.pack(padx=10, pady=10)

    def atualizar_log(mensagem):
        log.config(state='normal')
        log.insert(tk.END, f"{mensagem}\n")
        log.see(tk.END)
        log.update()
        log.config(state='disabled')

    return atualizar_log, status_window

def iniciar_integracao(filepath):
    log, janela = abrir_janela_status()
    try:
        log("Limpando tabelas auxiliares...")
        truncar_tabelas_auxiliares()

        log("Importando planilha...")
        importar_agendamento_excel(filepath)

        lista_nomes = lista_nome_grupo()
        for nome in lista_nomes:
            grupos = fetch_group_data_by_name(nome)
            if not grupos:
                log(f"Nenhum grupo encontrado para: {nome}")
                continue
            for grupo in grupos:
                save_group_data(grupo)

        refresh_tables()

        log("Validando dados antes da integração...")
        validador = ValidadorIntegracao()

        df_escola = validador.validar_escola()
        df_grupo = validador.validar_grupo()
        df_tarefa = validador.validar_tarefa()
        df_place = validador.validar_place()
        validador.fechar_conexao()

        gerar_relatorio_validacao(df_escola, df_grupo, df_tarefa, df_place)

        houve_erro = False
        mensagem_erro = ""

        if not df_escola.empty:
            mensagem_erro += "Erros de escola detectados.\n"
            log("Erros de escola detectados.")
            log(df_escola.to_string(index=False))
            houve_erro = True

        if not df_grupo.empty:
            mensagem_erro += "Erros de grupo detectados.\n"
            log("Erros de grupo detectados.")
            log(df_grupo.to_string(index=False))
            houve_erro = True

        if not df_tarefa.empty:
            mensagem_erro += "Erros de tarefa detectados.\n"
            log("Erros de tarefa detectados.")
            log(df_tarefa.to_string(index=False))
            houve_erro = True

        if not df_place.empty:
            mensagem_erro += "Erros de local (place) detectados.\n"
            log("Erros de local (place) detectados.")
            log(df_place.to_string(index=False))
            houve_erro = True

        if houve_erro:
            messagebox.showerror("Erro de Validação", f"Inconsistências foram encontradas nos dados:\n\n{mensagem_erro}\nVerifique o relatório gerado.")
            log("Validação falhou. Integração encerrada.")
            return

        execution_id = processar_integracao_estagio()
        if execution_id:
            log(f"Execução gerada: {execution_id}")
            log("Enviando dados para a API...")
            enviar_dados_api_ensalamento(execution_id)
            log("Integração concluída.")
            messagebox.showinfo("Concluído", "Integração concluída com sucesso.")
        else:
            log("Falha ao gerar execução.")
            messagebox.showerror("Erro", "Falha ao gerar execução.")

    except Exception as e:
        log(f"Erro durante o processamento:\n{e}")
        messagebox.showerror("Erro", str(e))
    finally:
        janela.destroy()

def selecionar_arquivo():
    filepath = filedialog.askopenfilename(
        filetypes=[("Excel files", "*.xlsx")],
        title="Selecione a planilha de agendamento"
    )
    if filepath:
        iniciar_integracao(filepath)

def abrir_gui():
    global app
    app = tk.Tk()
    app.title("Integração de Ensalamento - RADE")
    app.geometry("500x350")
    app.resizable(False, False)

    tk.Label(
        app,
        text="Integração com Sistema de Ensalamento RADE",
        font=("Arial", 14, "bold")
    ).pack(pady=15)

    frame = tk.Frame(app)
    frame.pack(pady=5)

    tk.Button(
        frame, text="Selecionar Planilha e Iniciar Integração",
        command=selecionar_arquivo,
        width=45
    ).pack(pady=5)

    tk.Button(
        frame, text="Gerar Relatório por Data",
        command=gerar_relatorio_por_data,
        width=45
    ).pack(pady=5)

    tk.Button(
        frame, text="Sair",
        command=app.destroy,
        width=45,
        fg="red"
    ).pack(pady=15)

    tk.Label(app, text="Desenvolvido por thcesar85 - v1.0", font=("Arial", 8)).pack(side="bottom", pady=5)

    app.mainloop()

if __name__ == "__main__":
    abrir_gui()
