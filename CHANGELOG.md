# Changelog

Todas as mudanças relevantes deste projeto são documentadas neste arquivo.

O formato segue o [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/)
e o projeto adota o [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [Unreleased]

### Planejado
- Agente Revisor (QA) que valida o entregável antes de mover o card para DONE
- Progresso em tempo real no Discord a partir dos eventos do Team
- Slash commands (`/tarefa`, `/status`)
- Geração de imagens (diagramas) para os entregáveis

## [0.1.0] - 2026-08-22

Primeira versão publicada: bot Discord multimodal com um time de três agentes
(agno + Groq) integrado ao Trello.

### Added
- **Bot Discord** (`main.py`) acionado por menção, com camada de intake
  multimodal (texto, nota de voz e imagem), sessão por canal, envio dos
  arquivos gerados como anexos e tratamento de erros com logging.
- **Time de agentes** (`agents/`):
  - `PM Agent` cria o card no Trello a partir do pedido.
  - `Executor Agent` produz o entregável real (SQL, código, markdown…),
    salva em disco, anexa ao card, comenta e move para DONE; interrompe o
    fluxo se alguma ferramenta falhar.
  - `Reporter Agent` resume o status do board, traz comentários de um card e
    executa ações em cards existentes (mover, comentar).
  - `Vision Analyst` extrai tarefas de imagens (fotos de quadro, prints de
    requisitos) antes de o Team ser acionado.
  - `Team` roteia cada mensagem por intenção (nova tarefa / status / ação em
    card), com histórico de sessão em SQLite e `tool_call_limit`.
- **Ferramentas do Trello** (`tools/trello.py`): `create_card`, `find_card`,
  `move_card` (TODO/DOING/DONE), `add_comment`, `attach_file_to_card`,
  `list_board_cards` e `get_card_comments`.
- **`save_deliverable`** (`tools/deliverables.py`): grava o entregável na
  pasta da execução usando o `run_context` injetado pelo agno, com nome
  sanitizado, lista de extensões permitidas e limite de tamanho.
- **Voz** (`services/`): transcrição com Whisper hospedado no Groq e resposta
  falada em português com edge-tts, acionada por nota de voz ou pelo pedido
  "responda em áudio".
- **Utilitários de texto**: remoção de blocos `<think>`, divisão em mensagens
  de 2000 caracteres, classificação de anexos e preparação do resumo falado
  (sem markdown, links ou emojis).
- **Testes** com pytest, sem acesso à rede, cobrindo as ferramentas do Trello,
  `save_deliverable` e as funções de intake.
- **Documentação**: README completo, `.env.example` documentado, scripts para
  descobrir os IDs do Trello, licença MIT e este changelog.

### Security
- Erros da API do Trello são devolvidos aos agentes como mensagens sem a URL
  da requisição, evitando o vazamento de `key`/`token` nos logs.
- `.env`, `data/` e `outputs/` são ignorados pelo git.
- `save_deliverable` bloqueia path traversal e extensões executáveis.

[Unreleased]: https://github.com/bgarciamoura/agno-discord-lab/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/bgarciamoura/agno-discord-lab/releases/tag/v0.1.0
