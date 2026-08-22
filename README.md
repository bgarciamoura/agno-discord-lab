<div align="center">

# 🤖 agno-discord-lab

**Um time de agentes de IA no Discord que transforma texto, voz e imagens em tarefas no Trello — e as executa.**

[![Python](https://img.shields.io/badge/python-3.12-blue?logo=python&logoColor=white)](https://www.python.org/)
[![agno](https://img.shields.io/badge/agno-2.9-6e40c9)](https://docs.agno.com)
[![discord.py](https://img.shields.io/badge/discord.py-2.7-5865F2?logo=discord&logoColor=white)](https://discordpy.readthedocs.io/)
[![Groq](https://img.shields.io/badge/LLM-Groq-f55036)](https://console.groq.com)
[![uv](https://img.shields.io/badge/package%20manager-uv-DE5FE9)](https://docs.astral.sh/uv/)
[![tests](https://img.shields.io/badge/tests-pytest-0A9EDC?logo=pytest&logoColor=white)](#-testes)

Projeto da disciplina **IA Generativa & Engenharia de Prompt** (aula 004).

[Funcionalidades](#-funcionalidades) •
[Como funciona](#-como-funciona) •
[Começando](#-começando) •
[Uso](#-uso) •
[Configuração](#-configuração) •
[Testes](#-testes) •
[Solução de problemas](#-solução-de-problemas)

</div>

---

## 📖 Sobre

Você menciona o bot no Discord e descreve o que precisa — **digitando, mandando uma nota de voz ou uma foto do quadro branco**. Um time de três agentes (framework [agno](https://docs.agno.com)) assume a partir daí:

1. o **PM** cria o card no Trello;
2. o **Executor** produz o entregável de verdade (um arquivo `.sql`, `.py`, `.md`…), anexa ao card e o move para **DONE**;
3. o **Reporter** responde perguntas como *"como está o projeto?"* e executa pedidos como *"move essa para DONE"*.

O bot responde com texto, os arquivos gerados e — quando a entrada foi em voz — um **áudio em português**.

## ✨ Funcionalidades

| | Funcionalidade | Como |
|---|---|---|
| 💬 | **Texto → card + entregável** | `@bot crie o schema SQL de clientes e pedidos` |
| 🎙️ | **Nota de voz** | Transcrição com Whisper (Groq); resposta em texto **e** mp3 |
| 🖼️ | **Imagem → tarefas** | Foto de quadro, post-its ou print de requisitos vira um card por tarefa |
| 📊 | **Status do projeto** | `@bot como está o projeto?` resume TODO / DOING / DONE com links |
| 🧠 | **Memória por canal** | `@bot move essa para DONE` entende "essa" pelo histórico da conversa |
| 🔊 | **Resposta falada sob demanda** | `@bot responda em áudio: …` |
| 📎 | **Arquivos reais** | Entregáveis anexados ao card do Trello e enviados no Discord |
| 🆓 | **Custo zero** | Groq (free tier) + edge-tts (gratuito, sem chave) |

## 🧩 Como funciona

```
Discord (texto | nota de voz | imagem)
   │
   ▼  main.py — INTAKE: percepção → texto
   ├─ áudio  → services/stt.py   (Whisper no Groq)          → transcrição
   ├─ imagem → agents/vision.py  (agente de visão, Groq)    → lista de tarefas em markdown
   └─ texto  → direto
   │
   ▼  agents/team.py — TEAM (memória SQLite por canal, roteia por intenção)
   ├─ PM Agent        cria o card                       ──▶ NOVA TAREFA
   ├─ Executor Agent  gera arquivo, anexa, move p/ DONE ──▶ NOVA TAREFA
   └─ Reporter Agent  lê o board, move/comenta cards    ──▶ STATUS · AÇÃO EM CARD
   │
   ▼  main.py — OUTPUT
   ├─ texto (em pedaços de 2000 caracteres)
   ├─ arquivos gerados em outputs/<canal>/<mensagem>/
   └─ resposta.mp3 (edge-tts) quando a entrada foi áudio ou o usuário pediu
```

**Por que a mídia é convertida em texto *antes* do Team?** O Team delega tarefas aos membros em texto, e o Whisper nem é um modelo de chat. Separando *percepção* (intake) de *raciocínio e ação* (Team), os agentes continuam simples, determinísticos e testáveis — e trocar o modelo de voz ou de visão não mexe em nenhum agente.

### Os agentes

| Agente | Papel | Ferramentas |
|---|---|---|
| **PM Agent** | Transforma o pedido em um card com título curto e descrição objetiva | `create_card` |
| **Executor Agent** | Move para DOING → **produz o entregável** → salva → anexa ao card → comenta → move para DONE. Se uma ferramenta falhar, para e reporta | `find_card` `move_card` `add_comment` `save_deliverable` `attach_file_to_card` |
| **Reporter Agent** | Resume o board, traz os comentários de um card e executa ações em cards existentes | `list_board_cards` `get_card_comments` `find_card` `move_card` `add_comment` |
| **Vision Analyst** | *Sensor*, não é membro do Team: extrai tarefas de uma imagem no formato `- <título>: <descrição>` | — |

O **Team** classifica cada mensagem em uma intenção — *nova tarefa*, *status* ou *ação em card* — e usa os últimos 5 turnos da sessão para resolver referências como "essa tarefa".

## 🚀 Começando

### Pré-requisitos

- [Python 3.12](https://www.python.org/) e [uv](https://docs.astral.sh/uv/)
- Conta no [Groq](https://console.groq.com) — chat com visão + Whisper, gratuito
- [Trello](https://trello.com): API key, token e um board com as listas **TODO**, **DOING** e **DONE**
- Um bot no [Discord Developer Portal](https://discord.com/developers/applications) com **Message Content Intent** habilitado e permissão de enviar mensagens e anexos

### Instalação

```bash
git clone git@github.com:bgarciamoura/agno-discord-lab.git
cd agno-discord-lab
uv sync
cp .env.example .env
```

Preencha o `.env` (veja [Configuração](#-configuração)). Para descobrir os IDs do Trello:

```bash
uv run python scripts/list_boards.py   # → TRELLO_BOARD_ID
uv run python scripts/list_lists.py    # → TRELLO_TODO_LIST_ID, TRELLO_DOING_LIST_ID, TRELLO_DONE_LIST_ID
```

### Executar

```bash
uv run python main.py
```

Convide o bot para o servidor e mencione-o em qualquer canal.

## 💡 Uso

| Você envia | O bot faz |
|---|---|
| `@bot crie o schema SQL de clientes e pedidos` | PM cria o card → Executor gera `schema.sql`, anexa ao card, comenta e move para DONE → o arquivo chega no Discord |
| 🎙️ nota de voz: *"crie uma tarefa para documentar a API"* | Mostra a transcrição, executa o fluxo e responde em texto **+ `resposta.mp3`** |
| 📷 foto do quadro com 3 post-its + `@bot` | Lista as tarefas extraídas → cria 3 cards e 3 entregáveis |
| `@bot como está o projeto?` | Reporter resume TODO / DOING / DONE com títulos e links |
| `@bot o que foi feito na tarefa de login?` | Reporter traz os últimos comentários do card |
| `@bot move essa para DONE` | Reporter acha o card pelo histórico do canal e move |
| `@bot responda em áudio: como está o projeto?` | Status em texto + mp3 |

> **Dica para demos:** comece com 2–3 tarefas por imagem. Cada tarefa custa ~10 chamadas ao modelo e uma execução completa leva de 1 a 3 minutos no free tier do Groq.

### Testando voz e imagem sem o Discord

```bash
# TTS → STT (ida e volta)
uv run python -c "
import asyncio, pathlib
from services.tts import synthesize_speech
from services.stt import transcribe_audio
mp3 = asyncio.run(synthesize_speech('Crie uma tarefa para documentar a API.', pathlib.Path('data/teste.mp3')))
print(transcribe_audio(mp3.read_bytes(), 'teste.mp3'))
"

# Visão: o que o agente enxerga em uma imagem
uv run python -c "
import pathlib
from agents.vision import describe_image_as_tasks
print(describe_image_as_tasks(pathlib.Path('data/teste.png').read_bytes(), 'image/png'))
"
```

## ⚙️ Configuração

Todas as variáveis ficam no `.env` (modelo em [`.env.example`](.env.example)):

| Variável | Obrigatória | Descrição |
|---|:---:|---|
| `DISCORD_TOKEN` | ✅ | Token do bot (Developer Portal → Bot) |
| `GROQ_API_KEY` | ✅ | Chave da API do Groq |
| `GROQ_MODEL` | ✅ | Modelo de chat **com visão**. Padrão: `qwen/qwen3.6-27b` |
| `GROQ_STT_MODEL` | | Modelo de transcrição. Padrão: `whisper-large-v3-turbo` |
| `TTS_VOICE` | | Voz do edge-tts. Padrão: `pt-BR-AntonioNeural` (outras: `pt-BR-FranciscaNeural`, `pt-BR-ThalitaNeural`) |
| `TRELLO_API_KEY` / `TRELLO_TOKEN` | ✅ | Credenciais do Trello |
| `TRELLO_BOARD_ID` | ✅ | Board usado pelo time |
| `TRELLO_TODO_LIST_ID` / `TRELLO_DOING_LIST_ID` / `TRELLO_DONE_LIST_ID` | ✅ | IDs das três listas |

Listar todas as vozes em português: `uv run edge-tts --list-voices | grep pt-`

## 📁 Estrutura do projeto

```
agno-discord-lab/
├── main.py               # bot Discord: intake multimodal → Team → output
├── agents/
│   ├── config.py         # fábricas do modelo Groq e do SqliteDb
│   ├── pm.py             # PM Agent
│   ├── executor.py       # Executor Agent
│   ├── reporter.py       # Reporter Agent
│   ├── vision.py         # Vision Analyst (sensor de imagens)
│   └── team.py           # Team que coordena os três agentes
├── tools/
│   ├── trello.py         # ferramentas do Trello (sem vazar credenciais nos erros)
│   └── deliverables.py   # save_deliverable: grava o entregável na pasta da execução
├── services/
│   ├── stt.py            # Whisper (Groq)
│   ├── tts.py            # edge-tts
│   └── text.py           # funções puras: <think>, chunking, anexos, resumo falado
├── scripts/              # utilitários para descobrir IDs do Trello
├── tests/                # pytest, sem rede
├── outputs/              # arquivos gerados por mensagem   (ignorado pelo git)
└── data/                 # agno.db com o histórico das sessões (ignorado pelo git)
```

## 🧪 Testes

```bash
uv run pytest -q
```

Os testes não acessam a rede: `requests` é simulado e as variáveis de ambiente são falsas (`tests/conftest.py`). Cobrem as ferramentas do Trello (incluindo a garantia de que erros **não vazam o token**), o `save_deliverable` (path traversal, extensões, truncamento) e as funções de intake.

## 🔧 Solução de problemas

| Sintoma | Causa provável | O que fazer |
|---|---|---|
| `404 Not Found` ao criar card | `TRELLO_*_LIST_ID` errado | Rode `scripts/list_lists.py` e copie os IDs exatos |
| O bot não responde | Falta o **Message Content Intent** ou a menção | Habilite o intent no portal e mencione o bot com `@` |
| Resposta demora vários minutos | Free tier do Groq + muitas tool calls | Peça menos tarefas por mensagem; `tool_call_limit=25` no Team |
| `RateLimitError` | Limite do Groq | Aguarde ou reduza o número de tarefas |
| Texto com `<think>…</think>` | Modelo de raciocínio | Já é filtrado por `strip_think`; se aparecer, ajuste `reasoning_effort` em `agents/config.py` |
| Sem mp3 na resposta | Falha do edge-tts (serviço não oficial da Microsoft) | O bot degrada para texto e registra `Falha no TTS` no log |
| Imagem retorna "Nenhuma tarefa identificada" | Texto ilegível ou sem lista de itens | Use texto legível, 2–3 itens, boa iluminação |

## ⚠️ Limites conhecidos

- **TTS** depende do edge-tts, um serviço não oficial; o TTS do Groq só fala inglês.
- Não há **geração** de imagens — apenas leitura.
- Mensagens simultâneas no mesmo canal compartilham a mesma sessão/histórico.
- `find_card` busca por trecho do título; em empate retorna o card de atividade mais recente.
- Discord: 2000 caracteres por mensagem, 10 anexos por mensagem, 8 MB por arquivo.

## 🗺️ Roadmap

- [ ] Agente **Revisor (QA)** que valida o entregável antes de mover para DONE
- [ ] Progresso em tempo real no Discord a partir dos eventos do Team
- [ ] Slash commands (`/tarefa`, `/status`)
- [ ] Geração de imagens (diagramas) para os entregáveis

## 🤝 Contribuindo

1. Faça um fork e crie uma branch: `git checkout -b feat/minha-ideia`
2. Rode os testes: `uv run pytest -q`
3. Abra um pull request descrevendo a mudança

Use commits no padrão [Conventional Commits](https://www.conventionalcommits.org/pt-br/) (`feat:`, `fix:`, `docs:`…).

## 📄 Licença

Projeto acadêmico, livre para estudo e adaptação.
