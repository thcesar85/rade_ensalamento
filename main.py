from src.integration_service import executar_integracao_terminal
from config.config import EXCEL_DIR

def main():
    excel_file = f"{EXCEL_DIR}/agendamento.xlsx"
    sucesso, mensagem = executar_integracao_terminal(excel_file)
    print(mensagem)

if __name__ == "__main__":
    main()