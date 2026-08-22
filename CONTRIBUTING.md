# Contribuindo com o agno-discord-lab

Obrigado pelo interesse em contribuir! Este guia explica como preparar o
ambiente, o que esperamos de uma mudança e como abrir um pull request.

## Sumário

- [Código de conduta](#código-de-conduta)
- [Como posso contribuir?](#como-posso-contribuir)
- [Preparando o ambiente](#preparando-o-ambiente)
- [Fluxo de trabalho](#fluxo-de-trabalho)
- [Padrões de código](#padrões-de-código)
- [Testes](#testes)
- [Mensagens de commit](#mensagens-de-commit)
- [Pull requests](#pull-requests)
- [Adicionando um agente ou uma ferramenta](#adicionando-um-agente-ou-uma-ferramenta)
- [Segurança](#segurança)

## Código de conduta

Este projeto adota o [Contributor Covenant](CODE_OF_CONDUCT.md). Ao
participar, você concorda em seguir seus termos. Críticas são sobre o código,
nunca sobre as pessoas.

## Como posso contribuir?

- **Reportando bugs** — abra uma issue com: o que você fez (mensagem enviada
  ao bot, anexos), o que esperava, o que aconteceu e o trecho relevante do log
  do terminal. **Nunca cole o `.env` nem tokens.**
- **Sugerindo melhorias** — descreva o problema que a ideia resolve antes da
  solução. Veja o [roadmap no README](README.md#-roadmap) e a seção
  *Unreleased* do [CHANGELOG](CHANGELOG.md) para ideias já mapeadas.
- **Enviando código** — siga o fluxo abaixo.
- **Melhorando a documentação** — READMEs, docstrings e comentários contam
  tanto quanto código.

## Preparando o ambiente

Pré-requisitos: Python 3.12, [uv](https://docs.astral.sh/uv/) e as contas
descritas no [README](README.md#-começando) (Groq, Trello, Discord).

```bash
git clone git@github.com:<seu-usuario>/agno-discord-lab.git
cd agno-discord-lab
uv sync                 # instala dependências, incluindo as de desenvolvimento
cp .env.example .env    # preencha com as suas chaves
uv run pytest -q        # deve passar sem rede
```

> Use um **board de testes** no Trello e um servidor de Discord próprio.
> Os agentes criam, movem e comentam cards de verdade.

## Fluxo de trabalho

1. Faça um fork e crie uma branch a partir de `main`:
   `git checkout -b feat/nome-curto` (ou `fix/`, `docs/`, `test/`, `chore/`).
2. Faça commits pequenos e focados (veja [Mensagens de commit](#mensagens-de-commit)).
3. Garanta que `uv run pytest -q` passa.
4. Atualize a documentação afetada (README, `.env.example`, docstrings) e
   adicione uma linha na seção *Unreleased* do `CHANGELOG.md`.
5. Abra o pull request.

## Padrões de código

- **Python 3.12**, type hints nas assinaturas públicas, docstrings em português.
- **Ferramentas (tools) dos agentes** são funções simples com docstring — o
  agno usa a docstring e a assinatura para gerar o schema que o modelo vê.
  Escreva docstrings pensando em quem vai ler: o modelo.
- Tools **retornam mensagens de erro em vez de levantar exceção**
  (`"Erro Trello (HTTP 401): ..."`), para que o agente possa reagir. Nunca
  inclua URLs de requisição nas mensagens: elas carregam credenciais.
- Código **síncrono** (Team, Whisper, `requests`) roda em
  `asyncio.to_thread`; APIs **assíncronas** (edge-tts, discord.py) são
  aguardadas diretamente no event loop.
- Mantenha a separação de camadas: **intake** (mídia → texto) em `main.py` /
  `services/`, **raciocínio e ação** nos agentes, **integrações** em `tools/`.
- Instruções de agentes são listas de frases curtas e imperativas, em
  português. Ao mudar uma instrução, teste o comportamento de ponta a ponta
  pelo menos uma vez — prompts são código.
- Nenhum segredo em código, testes ou fixtures. Use `.env` e
  `tests/conftest.py` (valores falsos).

## Testes

```bash
uv run pytest -q            # todos
uv run pytest -q -k trello  # filtro por nome
```

- Testes **não acessam a rede**: `requests` é substituído por `monkeypatch`
  e as variáveis de ambiente vêm de `tests/conftest.py`.
- Toda tool nova precisa de teste cobrindo o caminho feliz e um erro
  (incluindo a garantia de que o erro não vaza credenciais).
- Funções puras (`services/text.py`) devem ser testadas sem Discord.
- Scripts que batem em APIs reais ficam em `scripts/`, nunca em `tests/`.

## Mensagens de commit

Seguimos o [Conventional Commits](https://www.conventionalcommits.org/pt-br/):

```
<tipo>(<escopo opcional>): <descrição no imperativo, minúscula, sem ponto>

<corpo opcional explicando o porquê>
```

| Tipo | Uso |
|---|---|
| `feat` | nova funcionalidade |
| `fix` | correção de bug |
| `docs` | documentação |
| `test` | testes |
| `refactor` | mudança sem alterar comportamento |
| `chore` | configuração, dependências, build |

Escopos usados: `bot`, `agents`, `tools`, `services`, `tests`, `docs`.
Exemplos: `feat(agents): adiciona agente revisor`, `fix(tools): trata lista inexistente em move_card`.

## Pull requests

- Um PR resolve **uma** coisa. Mudanças grandes: abra uma issue antes para
  alinhar o desenho.
- Descreva **o quê** e **por quê**, como testou (comando e, se for o caso,
  print da conversa no Discord) e o que fica de fora.
- Marque mudanças que exigem nova variável no `.env` ou nova dependência.
- O PR precisa passar em `uv run pytest -q`.

## Adicionando um agente ou uma ferramenta

**Nova ferramenta (tool)**

1. Crie a função em `tools/` com docstring clara e parâmetros tipados.
2. Integre ao Trello (ou outro serviço) via `tools.trello._request` ou um
   helper equivalente que não vaze credenciais.
3. Escreva os testes em `tests/`.
4. Adicione a função à lista `tools=[...]` do agente que deve usá-la e ajuste
   as instruções dele.

**Novo agente**

1. Crie `agents/<nome>.py` usando `make_model()` de `agents/config.py`.
2. Defina `role` e `instructions` curtas; dê apenas as tools necessárias.
3. Adicione-o a `members=[...]` em `agents/team.py` e inclua a nova intenção
   nas instruções do Team (o roteamento é feito por elas).
4. Documente o agente na tabela do README e no CHANGELOG.

## Segurança

Encontrou uma vulnerabilidade (ex.: vazamento de token, execução de arquivo
não permitido)? **Não abra uma issue pública.** Siga a
[política de segurança](SECURITY.md), que descreve o canal de reporte, o
prazo de resposta e o modelo de ameaças do projeto.
