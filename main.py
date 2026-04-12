import argparse
import os
import sys
from src.integration_service import executar_integracao_terminal
from config.config import EXCEL_DIR

def main():
    parser = argparse.ArgumentParser(description="Executa a integração de ensalamento.")
    parser.add_argument(
        "excel_file",
        nargs="?",
        default=f"{EXCEL_DIR}/agendamento.xlsx",
        help="Caminho para o arquivo Excel de agendamento (padrão: dados/agendamento.xlsx)"
    )
    args = parser.parse_args()

    excel_file = args.excel_file

    if not os.path.exists(excel_file):
        print(f"Erro: Arquivo '{excel_file}' não encontrado.")
        sys.exit(1)

    try:
        sucesso, mensagem = executar_integracao_terminal(excel_file)
        print(mensagem)
        sys.exit(0 if sucesso else 1)
    except Exception as e:
        print(f"Erro inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()