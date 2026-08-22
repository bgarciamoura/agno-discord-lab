# agno-discord-lab

Laboratório da disciplina **IA Generativa & Engenharia de Prompt (aula 004)**: um bot do Discord que
coordena um **time de agentes** (framework [agno](https://docs.agno.com)) para transformar pedidos em
**cards no Trello** e **entregáveis reais**, aceitando entrada por **texto, nota de voz ou imagem**.

## Arquitetura

```
Discord (texto | nota de voz | imagem)
   │
   ▼  main.py — camada de INTAKE (percepção → texto)
   ├─ áudio  → services/stt.py  (Groq Whisper)           → transcrição
   ├─ imagem → agents/vision.py (Agent Groq com visão)    → lista de tarefas em markdown
   └─ texto  → direto
   │   prompt único + session_id = "discord-<canal>" + dependencies = {"output_dir": ...}
   ▼
agents/team.py — Team (memória SQLite por canal, 3 membros, roteia por intenção)
   ├─ PM Agent        create_card                                    → NOVA TAREFA
   ├─ Executor Agent  find/move/comment + save_deliverable + attach   → ENTREGÁVEL REAL
   └─ Reporter Agent  list_board_cards, get_card_comments, find/move  → STATUS / AÇÃO EM CARD
   │
   ▼  main.py — camada de OUTPUT
   ├─ texto (pedaços de 2000 caracteres)
   ├─ arquivos gerados em outputs/<canal>/<msg_id>/ → anexos no Discord
   └─ se a entrada foi áudio (ou pediu "responda em áudio") → services/tts.py → resposta.mp3
```

**Por que o intake fica fora do Team?** O Team delega por texto aos membros, e o Whisper nem é um
modelo de chat. Convertendo toda mídia em texto *antes*, o Team e os três agentes continuam
text-first, determinísticos e testáveis — "percepção" separada de "raciocínio/ação".

### Os agentes

| Agente | Papel | Ferramentas |
|---|---|---|
| **PM Agent** | Cria o card no Trello (lista TODO) com título e descrição objetivos | `create_card` |
| **Executor Agent** | Move para DOING, **produz o entregável real** (SQL, código, doc), salva, anexa ao card, comenta e move para DONE | `find_card`, `move_card`, `add_comment`, `save_deliverable`, `attach_file_to_card` |
| **Reporter Agent** | Responde "como está o projeto?", traz comentários de um card e executa ações em cards existentes ("move essa para DONE") | `list_board_cards`, `get_card_comments`, `find_card`, `move_card`, `add_comment` |
| **Vision Analyst** | *Sensor* (não é membro do Team): extrai tarefas de fotos de quadro/prints | — |

O **Team** classifica cada mensagem em uma intenção — *nova tarefa*, *status* ou *ação em card* —
e usa o histórico da sessão (5 runs) para resolver referências como "essa tarefa".

## Pré-requisitos

- Python 3.12 e [uv](https://docs.astral.sh/uv/)
- Conta no [Groq](https://console.groq.com) (chat com visão + Whisper — gratuito)
- Trello: API key + token e um board com listas **TODO**, **DOING**, **DONE**
- Bot no [Discord Developer Portal](https://discord.com/developers/applications) com o
  **Message Content Intent** habilitado e permissão para enviar mensagens/anexos
- Voz falada: [edge-tts](https://pypi.org/project/edge-tts/) (gratuito, sem chave)

## Setup

```bash
uv sync
cp .env.example .env            # preencha as chaves
uv run python scripts/list_boards.py   # descobre TRELLO_BOARD_ID
uv run python scripts/list_lists.py    # descobre os IDs das listas TODO/DOING/DONE
```

Executar o bot:

```bash
uv run python main.py
```

## Como usar (mencione o bot)

| Entrada | Exemplo | O que acontece |
|---|---|---|
| Texto | `@bot crie o schema SQL de clientes e pedidos` | PM cria o card → Executor gera `schema.sql`, anexa ao card, comenta, move para DONE → arquivo chega no Discord |
| Nota de voz | 🎙️ "crie uma tarefa para documentar a API" | Bot mostra a transcrição, executa o fluxo e responde em texto **+ `resposta.mp3`** |
| Imagem | 📷 foto do quadro com 3 post-its | Vision Analyst lista as tarefas → um card e um entregável por tarefa |
| Status | `@bot como está o projeto?` | Reporter resume TODO/DOING/DONE com títulos e links |
| Follow-up | `@bot move essa para DONE` | Reporter usa o histórico do canal para achar o card e movê-lo |
| Áudio sob demanda | `@bot responda em áudio: como está o projeto?` | Resposta em texto + mp3 |

## Estrutura

```
agents/      config.py (modelo + db), pm.py, executor.py, reporter.py, vision.py, team.py
tools/       trello.py (tools do Trello), deliverables.py (save_deliverable)
services/    stt.py (Whisper), tts.py (edge-tts), text.py (funções puras de texto/intake)
scripts/     utilitários para descobrir IDs do Trello
tests/       pytest sem rede (tools mockadas)
outputs/     arquivos gerados por mensagem  (ignorado pelo git)
data/        agno.db com o histórico das sessões (ignorado pelo git)
```

## Testes

```bash
uv run pytest -q
```

Os testes não acessam rede: `requests` é simulado e as variáveis de ambiente são falsas
(`tests/conftest.py`).

## Limites conhecidos

- **Groq**: o plano gratuito tem rate limit; uma imagem com 3 tarefas gera ~15–20 chamadas.
  O Team tem `tool_call_limit=25`.
- **TTS** só via edge-tts (o TTS do Groq é apenas em inglês). Sem geração de imagens.
- **Discord**: 2000 caracteres por mensagem, 10 anexos por mensagem, 8 MB por arquivo.
- Duas mensagens simultâneas no mesmo canal compartilham a mesma sessão/histórico.
- `find_card` busca por trecho do título; em empate retorna o card de atividade mais recente.
