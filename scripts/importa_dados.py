import pandas as pd
import requests
import json

# Configurações da API
API_URL = "https://radeestagio.com.br/api/v1/activity"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer 5Xf4IYXlV1TTpAUsJL10y3BTEMlqGT6p"
}

# Carregar a planilha
df = pd.read_excel("data/agendamento.xlsx", sheet_name="Planilha1")

# Criar estrutura para envio
payloads = []
grouped = df.groupby(["cnpj", "codigo curso", "Código grupo", "Codigo da Tarefa", "Data", "Hora início", "Hora Final"])

for (cnpj, codcurso, codgrupo, atividade, date, start, end), group_df in grouped:
    
    students = group_df["CPF Estudante"].astype(str).tolist()  # Garantir que todos sejam string

    payload = {
        "entityCode": 6407,
        "courseCode": str(codcurso),
        "groupCode": str(codgrupo),
        "place": str(cnpj),
        "taskCode": str(atividade),
        "date": str(date.date()),
        "startTime": str(start),
        "endTime": str(end),
        "students": students
    }

    payloads.append(payload)

# Salvar o payload em um arquivo JSON
payload_file = "payload.json"
with open(payload_file, "w", encoding="utf-8") as f:
    json.dump(payloads, f, indent=4, ensure_ascii=False)

# Criar o comando curl
curl_command = f"""curl --location '{API_URL}' \\
--header 'Content-Type: application/json' \\
--header 'Authorization: Bearer 5Xf4IYXlV1TTpAUsJL10y3BTEMlqGT6p' \\
--data '@{payload_file}'
"""

# Salvar o comando curl em um arquivo TXT
curl_file = "curl_command.txt"
with open(curl_file, "w", encoding="utf-8") as f:
    f.write(curl_command)

# Exibir resposta da API

# Enviar os dados automaticamente para a API
response = requests.post(API_URL, json=payloads, headers=HEADERS)

print(f"Status Code: {response.status_code}")
print(f"Resposta: {response.text}")    

print(f"Payload salvo em: {payload_file}")
print(f"Comando curl salvo em: {curl_file}")
