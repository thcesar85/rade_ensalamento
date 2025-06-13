import psycopg2
import pandas as pd
from config.conn import conectar


class ValidadorIntegracao:

    def __init__(self):
        self.conn = conectar()

    def validar_escola(self):
        query = """
            SELECT DISTINCT A.escola AS escola_na_planilha
            FROM ensalamento."aux_agendamento" A
            LEFT JOIN ensalamento."tbEntity" E 
              ON lower(trim(E.entity_name)) = lower(trim(A.escola))
            WHERE E.entity_code IS NULL;
        """
        return pd.read_sql(query, self.conn)

    def validar_grupo(self):
        query = """
            SELECT DISTINCT A.grupo, A.escola
            FROM ensalamento."aux_agendamento" A
            JOIN ensalamento."tbEntity" E 
              ON lower(trim(E.entity_name)) = lower(trim(A.escola))
            LEFT JOIN ensalamento."tbGroup" G 
              ON G.group_name = A.grupo AND G.entity_code = E.entity_code
            WHERE G.code IS NULL;
        """
        return pd.read_sql(query, self.conn)

    def validar_tarefa(self):
        query = """
            SELECT DISTINCT A.tarefa, A.grupo, A.escola
            FROM ensalamento."aux_agendamento" A
            JOIN ensalamento."tbEntity" E 
              ON lower(trim(E.entity_name)) = lower(trim(A.escola))
            JOIN ensalamento."tbGroup" G 
              ON G.group_name = A.grupo AND G.entity_code = E.entity_code
            LEFT JOIN ensalamento."tbTask" T 
              ON lower(trim(T.task_name)) = lower(trim(A.tarefa)) AND G.code = T.group_code
            WHERE T.task_code IS NULL;
        """
        return pd.read_sql(query, self.conn)

    def validar_place(self):
        query = """
            SELECT DISTINCT A.grupo, A.escola
            FROM ensalamento."aux_agendamento" A
            JOIN ensalamento."tbEntity" E 
              ON lower(trim(E.entity_name)) = lower(trim(A.escola))
            JOIN ensalamento."tbGroup" G 
              ON G.group_name = A.grupo AND G.entity_code = E.entity_code
            LEFT JOIN ensalamento."tbPlace" P 
              ON G.code = P.group_code 
             AND P.entity_code = G.entity_code 
             AND P.course_code = G.course_code
            WHERE P.id_place IS NULL;
        """
        return pd.read_sql(query, self.conn)

    def fechar_conexao(self):
        if self.conn:
            self.conn.close()


# 🔥 Exemplo de uso:

if __name__ == "__main__":
    validador = ValidadorIntegracao()

    print("🔍 Validando Escolas...")
    df_escola = validador.validar_escola()
    print(df_escola)

    print("🔍 Validando Grupos...")
    df_grupo = validador.validar_grupo()
    print(df_grupo)

    print("🔍 Validando Tarefas...")
    df_tarefa = validador.validar_tarefa()
    print(df_tarefa)

    print("🔍 Validando Places...")
    df_place = validador.validar_place()
    print(df_place)

    validador.fechar_conexao()
