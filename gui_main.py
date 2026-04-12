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

class GuiApp:
    def __init__(self):
        self.app = tk.Tk()
        self.app.title("Integração de Ensalamento - RADE")
        self.app.geometry("600x450")
        self.app.resizable(False, False)

        self.ies_list = src.ies_service.list_active()
        self.ies_combo = None
        self.ies_status_var = tk.StringVar(value="Nenhuma IES selecionada")
        self.btn_integrar = None
        self.progress_bar = ttk.Progressbar(self.app, mode='indeterminate', length=400)
        self.progress_bar.pack_forget()

        self.setup_ui()

    def setup_ui(self):
        self.setup_ies_frame()
        self.setup_main_label()
        self.setup_buttons_frame()
        self.setup_footer()

    def setup_ies_frame(self):
        ies_frame = tk.Frame(self.app)
        ies_frame.pack(pady=(10, 5), fill="x")

        tk.Label(ies_frame, text="Selecione a IES:", font=("Arial", 10, "bold")).pack(anchor="w", padx=12)

        display_values = [f"{i.entity_code} - {i.entity_name}" for i in self.ies_list]

        self.ies_combo = ttk.Combobox(ies_frame, values=display_values, state="readonly", width=48)
        self.ies_combo.pack(padx=12, pady=(2, 6), fill="x")
        self.ies_combo.bind("<<ComboboxSelected>>", self.on_ies_selected)

        tk.Label(ies_frame, textvariable=self.ies_status_var, font=("Arial", 9)).pack(anchor="w", padx=12)

    def setup_main_label(self):
        tk.Label(
            self.app,
            text="Integração com Sistema de Ensalamento RADE",
            font=("Arial", 14, "bold")
        ).pack(pady=15)

    def setup_buttons_frame(self):
        frame = tk.Frame(self.app)
        frame.pack(pady=5)

        self.btn_integrar = tk.Button(
            frame, text="Selecionar Planilha e Iniciar Integração",
            command=self.selecionar_arquivo,
            width=45,
            state="disabled"
        )
        self.btn_integrar.pack(pady=5)

        tk.Button(
            frame, text="Abrir Último CSV de Resumo de Envio",
            command=self.abrir_ultimo_csv_erro,
            width=45
        ).pack(pady=5)

        tk.Button(
            frame, text="Sair",
            command=self.app.destroy,
            width=45,
            fg="red"
        ).pack(pady=20)

        self.progress_bar.pack(pady=5)

    def setup_footer(self):
        tk.Label(self.app, text="Desenvolvido por thcesar85 - v2.0", font=("Arial", 8)).pack(side="bottom", pady=5)

    def on_ies_selected(self, _event=None):
        idx = self.ies_combo.current()
        if idx < 0:
            return
        ies = self.ies_list[idx]
        set_api_context(
            id=ies.id,
            entity_code=ies.entity_code,
            entity_name=ies.entity_name,
            api_key=ies.api_key,
        )
        self.ies_status_var.set(f"IES selecionada: {ies.entity_code} - {ies.entity_name}")
        self.btn_integrar.config(state="normal")

    def selecionar_arquivo(self):
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
                self.log_erro_fatal(f"Erro durante a execução da integração: {e}")
                messagebox.showerror("Erro", f"Erro durante a execução: {e}")

    def abrir_ultimo_csv_erro(self):
        try:
            from utils.db_utils import execute_query

            query = """
                SELECT execution_id
                FROM ensalamento."tbexecucaointegracao"
                ORDER BY data_execucao DESC
                LIMIT 1
            """
            row = execute_query(query, fetch_one=True)

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

    def log_erro_fatal(self, mensagem):
        try:
            erro_path = os.path.join(LOG_DIR, "erro_fatal.log")
            with open(erro_path, "w", encoding="utf-8") as f:
                f.write(mensagem)
        except Exception as e:
            print(f"Erro ao salvar log: {e}")

    def run(self):
        self.app.mainloop()

def abrir_gui():
    app = GuiApp()
    app.run()

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
