from logging import root
import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from dotenv import load_dotenv
from src.integration_service import executar_integracao_terminal
import src.ies_service
from src.api_context import set_api_context

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

EXCEL_DIR = os.getenv("INPUT_EXCEL_DIR", os.path.join(BASE_DIR, "dados"))
LOG_DIR = os.getenv("LOG_DIR", os.path.join(EXCEL_DIR, "logs"))
EXCEL_OLD_DIR = os.getenv("EXCEL_OLD_DIR", os.path.join(EXCEL_DIR, "old"))

for path in [EXCEL_DIR, LOG_DIR, EXCEL_OLD_DIR]:
    os.makedirs(path, exist_ok=True)

def abrir_ultimo_csv_erro():
    try:
        import psycopg2
        from config.conn import conectar

        conn = conectar()
        if conn is None:
            messagebox.showerror("Erro", "Não foi possível conectar ao banco.")
            return

        cursor = conn.cursor()
        cursor.execute("""
            SELECT execution_id 
            FROM ensalamento."tbexecucaointegracao"
            ORDER BY data_execucao DESC 
            LIMIT 1
        """)
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        if not row:
            messagebox.showinfo("Resumo", "Nenhuma execução encontrada no histórico.")
            return

        ultimo_execution_id = row[0]

        arquivos = [
            f for f in os.listdir(LOG_DIR)
            if f.startswith(f"resumo_envio_{ultimo_execution_id}") and f.endswith(".csv")
        ]

        if not arquivos:
            messagebox.showinfo("Resumo", f"Nenhum resumo encontrado para execução {ultimo_execution_id}.")
            return

        arquivos.sort(reverse=True)
        caminho_arquivo = os.path.join(LOG_DIR, arquivos[0])
        os.startfile(caminho_arquivo)

    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao abrir CSV da última execução: {e}")

def selecionar_arquivo():
    filepath = filedialog.askopenfilename(
        filetypes=[("Excel files", "*.xlsx")],
        title="Selecione a planilha de agendamento"
    )
    if filepath:
        try:
            sucesso, mensagem = executar_integracao_terminal(filepath)
            if sucesso:
                messagebox.showinfo("Integração Finalizada", mensagem)
            else:
                messagebox.showwarning("Falha na Integração", mensagem)

        except Exception as e:
            log_erro_fatal(f"Erro durante a execução da integração: {e}")
            messagebox.showerror("Erro", f"Erro durante a execução: {e}")

# --- DROPLIST IES (seleção única) ---
def on_ies_selected(_event=None):
    idx = ies_combo.current()
    if idx < 0:
        return
    # objeto dataclass IES
    ies = ies_list[idx]
    # define o contexto global para a API
    set_api_context(
        id=ies.id,
        entity_code=ies.entity_code,
        entity_name=ies.entity_name,
        api_key=ies.api_key,   # cru; os módulos montam "Bearer ..." se precisarem
    )
    ies_status_var.set(f"IES selecionada: {ies.entity_code} - {ies.entity_name}")
    btn_integrar.config(state="normal")  # libera o botão principal

def abrir_gui():
    global app, progress_bar, btn_integrar
    global ies_combo, ies_list, ies_status_var


    app = tk.Tk()
    app.title("Integração de Ensalamento - RADE")
    app.geometry("600x450")
    app.resizable(False, False)

    # === Bloco IES no topo ===
    ies_frame = tk.Frame(app)
    ies_frame.pack(pady=(10, 5), fill="x")

    tk.Label(ies_frame, text="Selecione a IES:", font=("Arial", 10, "bold")).pack(anchor="w", padx=12)

    ies_list = src.ies_service.list_active()  # retorna dataclasses
    display_values = [f"{i.entity_code} - {i.entity_name}" for i in ies_list]

    ies_combo = ttk.Combobox(ies_frame, values=display_values, state="readonly", width=48)
    ies_combo.pack(padx=12, pady=(2, 6), fill="x")
    ies_combo.bind("<<ComboboxSelected>>", on_ies_selected)

    ies_status_var = tk.StringVar(value="Nenhuma IES selecionada")
    tk.Label(ies_frame, textvariable=ies_status_var, font=("Arial", 9)).pack(anchor="w", padx=12)


    tk.Label(
        app,
        text="Integração com Sistema de Ensalamento RADE",
        font=("Arial", 14, "bold")
    ).pack(pady=15)

    frame = tk.Frame(app)
    frame.pack(pady=5)    

    btn_integrar = tk.Button(
        frame, text="Selecionar Planilha e Iniciar Integração",
        command=selecionar_arquivo,
        width=45,
        state="disabled"   # só habilita após selecionar IES
    )
    btn_integrar.pack(pady=5)

    tk.Button(
        frame, text="Abrir Último CSV de Resumo de Envio",
        command=abrir_ultimo_csv_erro,
        width=45
    ).pack(pady=5)

    tk.Button(
        frame, text="Sair",
        command=app.destroy,
        width=45,
        fg="red"
    ).pack(pady=20)

    progress_bar = ttk.Progressbar(app, mode='indeterminate', length=400)
    progress_bar.pack(pady=5)
    progress_bar.pack_forget()

    tk.Label(app, text="Desenvolvido por thcesar85 - v2.0", font=("Arial", 8)).pack(side="bottom", pady=5)

    app.mainloop()

def log_erro_fatal(mensagem):
    try:
        erro_path = os.path.join(LOG_DIR, "erro_fatal.log")
        with open(erro_path, "w", encoding="utf-8") as f:
            f.write(mensagem)
    except Exception as e:
        print(f"Erro ao salvar log: {e}")

if __name__ == "__main__":
    try:
        abrir_gui()
    except Exception as e:
        log_erro_fatal(f"Erro fatal ao iniciar a aplicação:\n{e}")
