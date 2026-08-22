# Política de Segurança

## Versões suportadas

| Versão | Suportada |
|---|:---:|
| 0.1.x | ✅ |
| < 0.1 | ❌ |

Apenas a versão mais recente publicada recebe correções de segurança.

## Reportando uma vulnerabilidade

**Não abra uma issue pública** para problemas de segurança.

Use o [Private Vulnerability Reporting](https://github.com/bgarciamoura/agno-discord-lab/security/advisories/new)
do GitHub ou envie uma mensagem direta ao mantenedor
([@bgarciamoura](https://github.com/bgarciamoura)). Inclua:

- descrição do problema e impacto potencial;
- passos para reproduzir (mensagem enviada ao bot, anexos, configuração);
- versão/commit afetado;
- se possível, uma sugestão de correção.

Você receberá uma confirmação em até **7 dias**. Correções são publicadas
como patch (`0.1.x`) e registradas no [CHANGELOG](CHANGELOG.md). Pedimos
que a divulgação pública aguarde a correção.

## O que consideramos vulnerabilidade

- Vazamento de credenciais (`DISCORD_TOKEN`, `GROQ_API_KEY`, `TRELLO_*`) em
  logs, mensagens do Discord, comentários do Trello ou arquivos gerados.
- Escrita de arquivos fora da pasta de saída da execução (*path traversal*)
  ou com extensões executáveis via `save_deliverable`.
- Execução de ações no Trello sem a autorização esperada (ex.: usuários não
  autorizados acionando o bot).
- *Prompt injection* por mensagem, áudio transcrito, imagem ou conteúdo de
  cards que leve os agentes a executar ações fora do fluxo previsto.
- Qualquer problema nas dependências que afete este projeto.

## Modelo de ameaças e mitigações atuais

Este é um projeto didático; conheça os limites antes de expô-lo.

| Risco | Mitigação existente | Limitação |
|---|---|---|
| Credenciais em logs | `tools/trello.py` nunca retorna a URL da requisição (que carrega `key`/`token`) nas mensagens de erro; logging em nível INFO | Logs em DEBUG do `requests`/`httpx` podem expor query strings |
| Segredos no repositório | `.env`, `data/` e `outputs/` no `.gitignore`; `.env.example` sem valores | Depende da disciplina de quem clona |
| Path traversal / arquivos perigosos | `save_deliverable` usa só o nome-base do arquivo, lista de extensões permitidas e limite de tamanho | Os arquivos gerados são enviados ao Discord e ao Trello sem análise de conteúdo |
| Quem pode acionar o bot | Apenas mensagens que mencionam o bot | **Qualquer membro** de um servidor onde o bot está pode criar cards e entregáveis — use um servidor/canal restrito |
| Prompt injection | Instruções dos agentes exigem `card_id` vindo das ferramentas e proíbem inventar dados; `tool_call_limit=25` no Team | Modelos ainda podem ser manipulados por texto, transcrição ou imagem; o bot não valida intenções maliciosas |
| Abuso / custo | Limite de tool calls por execução | Sem rate limit por usuário; mensagens em excesso consomem a cota do Groq |
| Serviços externos | TTS com `try/except` e degradação para texto | edge-tts usa um endpoint não oficial da Microsoft; Whisper/LLM enviam o conteúdo das mensagens, áudios e imagens ao Groq |

## Boas práticas para quem executa o bot

- Crie o bot do Discord com as **permissões mínimas** (ler/enviar mensagens e
  anexos) e convide-o apenas para servidores de confiança.
- Use um **token do Trello com escopo de leitura/escrita** restrito ao board
  do projeto e um board dedicado ao bot.
- Rotacione as chaves (`DISCORD_TOKEN`, `GROQ_API_KEY`, `TRELLO_TOKEN`) se
  houver qualquer suspeita de exposição — inclusive em capturas de tela de
  tracebacks.
- Mantenha as dependências atualizadas: `uv lock --upgrade && uv sync` e
  revise o `CHANGELOG` das bibliotecas críticas (`agno`, `discord.py`, `groq`).
- Não rode o bot com privilégios administrativos no sistema operacional; a
  pasta `outputs/` é a única que ele precisa escrever (além de `data/`).
