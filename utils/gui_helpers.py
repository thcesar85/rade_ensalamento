import os
from tkinter import messagebox
import sys


def abrir_ultimo_csv_erro(LOG_DIR):
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

def abrir_ultimo_txt_validacao(LOG_DIR):
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

def log_erro_fatal(mensagem, LOG_DIR):
    try:
        erro_path = os.path.join(LOG_DIR, "erro_fatal.log")
        with open(erro_path, "w", encoding="utf-8") as f:
            f.write(mensagem)
    except Exception as e:
        print(f"Erro ao salvar log: {e}")
