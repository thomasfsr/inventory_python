# Gerenciador de Inventário com Streamlit e Bot do Telegram

Este projeto é um gerenciador de inventário desenvolvido com Streamlit para a interface web e um bot do Telegram para manipulação de dados via chat. A modelagem de dados é realizada com LangGraph.

Resumo rápido
- Frontend: Streamlit
- Backend: Python (lógica de negócio e integração com Telegram)
- Integração: Bot do Telegram para operações de CRUD no inventário
- Modelagem de dados: LangGraph
- Idioma: Português (Brasil)

Recursos principais
- Visualização e gerenciamento de itens do inventário (CRUD)
- Filtros, busca e visualizações simples via UI do Streamlit
- Operações via bot do Telegram para adicionar, listar, atualizar e remover itens
- Estrutura modular para facilitar extensões futuras

Arquitetura (alto nível)
- streamlit_app/          — UI principal (Streamlit)
- telegram_bot/           — Lógica do bot e handlers (Telegram)
- models/                  — Definições de grafos/entidades (LangGraph)
- config/                  — Configurações e secrets (ex.: .env, settings.yaml)
- tests/                   — Testes (se aplicável)
- scripts/                 — Seeds e utilitários (opcional)

Como rodar localmente
- Pré-requisitos: Python 3.8+, virtualenv (ou use poetry/poetry env)
- Clone o repositório e ative o ambiente virtual:
  python -m venv venv
  source venv/bin/activate  # Linux/macOS
  # Windows: venv\Scripts\activate
- Instale as dependências:
  pip install -r requirements.txt
- Inicie o Streamlit:
  streamlit run streamlit_app/app.py
- Inicie o Bot Telegram (token necessário):
  python telegram_bot/bot.py

Configuração de segredos
- Crie um arquivo .env com as variáveis necessárias, por exemplo:
  TELEGRAM_BOT_TOKEN=seu_token_aqui
  STREAMLIT_PORT=8501
- Opcional: configure DATABASE_URL, LANGGRAPH_CONFIG, etc., conforme sua implementação

Modelagem de dados (LangGraph)
- LangGraph representa entidades do inventário (Item, Categoria, Local, Movimento) como grafos para facilitar consultas relacionais.
- Exemplo de entidades:
  - Item: id, nome, quantidade, localização, categoria, status
  - Categoria: id, nome
  - Local: id, nome, armazém
  - Movimento: id, item_id, quantidade, data, tipo

Estrutura de diretórios sugerida (conforme o projeto real pode variar)
- streamlit_app/
  - app.py
  - pages/
- telegram_bot/
  - bot.py
  - handlers/
- models/
  - graph_model.py
- config/
- tests/
- scripts/
- README.md
- requirements.txt

Notas
- Adapte nomes de pastas/arquivos aos seus nomes reais antes de usar este README.
- Adicione badges de CI, licença e screenshots quando apropriado.

Versões seguintes (opcionais)
- Versão completa com exemplos detalhados de comandos do bot e consultas LangGraph.

Licença
- Este projeto pode ser distribuído sob a licença de sua escolha (em branco aqui).
