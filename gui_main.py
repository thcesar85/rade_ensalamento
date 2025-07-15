import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from dotenv import load_dotenv
from src.integration_service import executar_integracao_terminal

if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

dotenv_path = os.path.join(BASE_DIR, '.env')
load_dotenv(dotenv_path)

EXCEL_DIR = os.getenv("INPUT_EXCEL_DIR", os.path.join(BASE_DIR, "dados"))
LOG_DIR = os.getenv("LOG_DIR", os.path.join(BASE_DIR, "dados", "logs"))
EXCEL_OLD_DIR = os.getenv("EXCEL_OLD_DIR", os.path.join(BASE_DIR, "dados", "old"))

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
            if f.startswith(f"resumo_envio_{ultimo_execution_id}_") and f.endswith(".csv")
        ]

        if not arquivos:
            messagebox.showinfo("Resumo", f"Nenhum resumo encontrado para execução {ultimo_execution_id}.")
            return

        arquivos.sort(reverse=True)
        caminho_arquivo = os.path.join(LOG_DIR, arquivos[0])
        os.startfile(caminho_arquivo)

    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao abrir CSV da última execução: {e}")

def abrir_ultimo_txt_validacao():
    try:
        arquivos = [
            f for f in os.listdir(LOG_DIR)
            if f.startswith("validacao_erros_") and f.endswith(".txt")
        ]
        if not arquivos:
            messagebox.showinfo("Validação", "Nenhum arquivo de erro de validação encontrado.")
            return

        arquivos.sort(reverse=True)
        caminho_arquivo = os.path.join(LOG_DIR, arquivos[0])
        os.startfile(caminho_arquivo)

    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao abrir arquivo de erros de validação: {e}")

def selecionar_arquivo():
    filepath = filedialog.askopenfilename(
        filetypes=[("Excel files", "*.xlsx")],
        title="Selecione a planilha de agendamento"
    )
    if filepath:
        try:
            progress_bar.pack(pady=5)
            progress_bar.start()
            app.update_idletasks()

            sucesso, mensagem = executar_integracao_terminal(filepath)

            progress_bar.stop()
            progress_bar.pack_forget()

            if sucesso:
                messagebox.showinfo("Integração Finalizada", mensagem)
            else:
                messagebox.showwarning("Falha na Integração", mensagem)

        except Exception as e:
            progress_bar.stop()
            progress_bar.pack_forget()
            log_erro_fatal(f"Erro durante a execução da integração: {e}")
            messagebox.showerror("Erro", f"Erro durante a execução: {e}")

def abrir_gui():
    global app, progress_bar
    app = tk.Tk()
    app.title("Integração de Ensalamento - RADE")
    app.geometry("500x330")
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
        frame, text="Abrir Último CSV de Resumo de Envio",
        command=abrir_ultimo_csv_erro,
        width=45
    ).pack(pady=5)

    tk.Button(
        frame, text="Abrir Último TXT de Erros de Validação",
        command=abrir_ultimo_txt_validacao,
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

    tk.Label(app, text="Desenvolvido por thcesar85 - v1.0", font=("Arial", 8)).pack(side="bottom", pady=5)

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
