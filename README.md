# 🏥 RADE - Integração de Ensalamento

Este projeto realiza a integração entre uma planilha de agendamento de estágios e a API da plataforma RADE, centralizando dados de alocação de estudantes, tarefas e campos de estágio em um banco de dados PostgreSQL.

---

## 📦 Funcionalidades

* 📤 Importa agendamentos a partir de uma planilha `.xlsx`
* 🔗 Busca dados complementares em uma API externa
* 🗃️ Armazena os dados em tabelas auxiliares PostgreSQL
* 📡 Envia dados integrados para a API RADE
* 🧾 Gera relatórios de execução por data com mensagens de retorno da API
* 💾 Registra logs de execução e integração
* 🧑‍💻 Interface gráfica amigável com configuração de banco de dados

---

## 🖥️ Como usar

### 1. Instalar dependências

```bash
pip install -r requirements.txt
```

### 2. Configurar o banco de dados

Ao abrir a interface, clique em `⚙ Configurar Banco de Dados` e preencha os dados de conexão. Eles serão salvos automaticamente no arquivo `.env`.


### 3. Executar a aplicação

Interface gráfica:

```bash
python gui_main.py
```

Terminal (execução direta):

```bash
python main.py
```

---

## 📄 Gerar Relatórios

Após uma execução, você pode gerar um relatório completo com base em uma data específica. O relatório inclui:

* Detalhes dos estudantes e tarefas enviados
* Status de integração
* Mensagens e códigos de retorno da API

---

## 🗂️ Estrutura do Projeto

```
rade_ensalamento/
├── config/               # Arquivos de conexão e configurações
├── src/                  # Scripts principais de leitura e envio
├── utils/                # Funções auxiliares de configuração e banco
├── gui_main.py           # Interface gráfica
├── main.py               # Execução em terminal
├── requirements.txt
├── .env
```

---

## 💡 Requisitos

* Python 3.8+
* PostgreSQL ativo e acessível
* Acesso à API RADE com token autorizado

---

