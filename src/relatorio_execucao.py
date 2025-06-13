import pandas as pd
from config.conn import conectar
from tkinter import filedialog, messagebox
from tkinter.simpledialog import askstring

def gerar_relatorio_por_data():
    try:
        data_input = askstring("Data da Execução", "Informe a data da execução (YYYY-MM-DD):")
        if not data_input:
            return

        conn = conectar()
        query = """
            SELECT 
                l.execution_id, 
                l.entitycode, l.coursecode, l.groupcode,
                l.taskcode, l.place, l.data, l.start_time, l.end_time,
                l.cpf_estudante,
                CASE WHEN l.integrated THEN 'SUCESSO' ELSE 'ERRO' END AS status_envio,
                COALESCE(i.mensagem, '') as mensagem
            FROM ensalamento."tblobbyensalamento" l
            LEFT JOIN ensalamento."tblogintegracao" i ON i.execution_id = l.execution_id
            WHERE cast(i.data_log as date) = %s
            ORDER BY l.execution_id, l.groupcode, l.taskcode, l.data, l.start_time
        """

        df = pd.read_sql(query, conn, params=(data_input,))

        if df.empty:
            messagebox.showinfo("Relatório", "Nenhum dado encontrado para a data informada.")
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            title="Salvar relatório como..."
        )

        if filepath:
            df.to_excel(filepath, index=False)
            messagebox.showinfo("Relatório", f"Relatório salvo em:\n{filepath}")

    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao gerar relatório:\n{e}")
    finally:
        if conn:
            conn.close()