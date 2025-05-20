import tkinter as tk
from tkinter import filedialog, messagebox
from utils.db_config import get_db_config, save_db_config
from src.read_excel_agendamento import importar_agendamento_excel
from utils.db_functions import (
    truncar_tabelas_auxiliares,
    lista_codigo_grupo,
    processar_integracao_estagio
)
from src.read_api_groupcode import (
    fetch_group_data_by_code,
    save_group_data,
    refresh_tables
)
from src.import_data_to_ensalamento import enviar_dados_api_ensalamento
from src.relatorio_execucao import gerar_relatorio_por_data

def abrir_config_banco():
    conf = get_db_config()

    config_window = tk.Toplevel(app)
    config_window.title("Configurar Banco de Dados")
    config_window.geometry("350x300")

    tk.Label(config_window, text="Host:").pack()
    host_entry = tk.Entry(config_window)
    host_entry.insert(0, conf["host"])
    host_entry.pack()

    tk.Label(config_window, text="Porta:").pack()
    port_entry = tk.Entry(config_window)
    port_entry.insert(0, conf["port"])
    port_entry.pack()

    tk.Label(config_window, text="Nome do Banco:").pack()
    name_entry = tk.Entry(config_window)
    name_entry.insert(0, conf["name"])
    name_entry.pack()

    tk.Label(config_window, text="Usuário:").pack()
    user_entry = tk.Entry(config_window)
    user_entry.insert(0, conf["user"])
    user_entry.pack()

    tk.Label(config_window, text="Senha:").pack()
    password_entry = tk.Entry(config_window, show="*")
    password_entry.insert(0, conf["password"])
    password_entry.pack()

    def salvar():
        save_db_config(
            host_entry.get(),
            port_entry.get(),
            name_entry.get(),
            user_entry.get(),
            password_entry.get()
        )
        messagebox.showinfo("Configuração", "Configuração do banco salva com sucesso.")
        config_window.destroy()

    tk.Button(config_window, text="Salvar Configuração", command=salvar).pack(pady=10)

def iniciar_integracao(filepath):
    try:
        messagebox.showinfo("Processando", "Iniciando integração...")

        truncar_tabelas_auxiliares()
        importar_agendamento_excel(filepath)

        grupos = lista_codigo_grupo()
        for codigo in grupos:
            for grupo in fetch_group_data_by_code(codigo):
                save_group_data(grupo)

        refresh_tables()
        execution_id = processar_integracao_estagio()

        if execution_id:
            enviar_dados_api_ensalamento(execution_id)
            messagebox.showinfo("Sucesso", f"Execução {execution_id} finalizada com sucesso.")
        else:
            messagebox.showerror("Erro", "Falha ao gerar execução.")

    except Exception as e:
        messagebox.showerror("Erro", str(e))

def selecionar_arquivo():
    filepath = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
    if filepath:
        iniciar_integracao(filepath)

def abrir_gui():
    global app
    app = tk.Tk()
    app.title("Integração Ensalamento")
    app.geometry("460x280")

    tk.Label(app, text="Integração com sistema de Ensalamento", font=("Arial", 12, "bold")).pack(pady=10)

    tk.Button(app, text="⚙ Configurar Banco de Dados", command=abrir_config_banco, width=40).pack(pady=5)
    tk.Button(app, text="📥 Selecionar Planilha e Iniciar Integração", command=selecionar_arquivo, width=40).pack(pady=10)
    tk.Button(app, text="📄 Gerar Relatório por Data", command=gerar_relatorio_por_data, width=40).pack(pady=10)
    tk.Button(app, text="❌ Sair", command=app.destroy, width=40).pack(pady=10)

    app.mainloop()

if __name__ == "__main__":
    abrir_gui()
