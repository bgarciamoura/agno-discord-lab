from agno.team import Team

from agents.config import make_db, make_model
from agents.executor import executor_agent
from agents.pm import pm_agent
from agents.reporter import reporter_agent

project_team = Team(
    name="Project Team",
    model=make_model(),
    members=[pm_agent, executor_agent, reporter_agent],
    # Memória: o histórico da sessão (por canal do Discord) entra no contexto do Team.
    # Os membros NÃO têm db próprio — o Team já repassa o contexto necessário na delegação.
    db=make_db(),
    add_history_to_context=True,
    num_history_runs=5,
    markdown=True,
    tool_call_limit=25,
    instructions=[
        "Você coordena um time de projeto com três membros: PM Agent, Executor Agent e Reporter Agent.",
        "Responda sempre em português. Seja objetivo.",
        "Classifique cada mensagem em UMA destas intenções antes de delegar:",
        "1) NOVA TAREFA (o usuário pede para fazer/criar/implementar/gerar algo): "
        "delegue ao PM Agent para criar o card; quando ele retornar o card_id e o título, "
        "delegue ao Executor Agent informando explicitamente o título e o card_id.",
        "2) STATUS (perguntas como 'como está o projeto?', 'o que está em andamento?', "
        "'o que foi feito na tarefa X?'): delegue ao Reporter Agent. "
        "NUNCA responda sobre o status do projeto por conta própria: só o Reporter tem acesso ao Trello.",
        "3) AÇÃO EM CARD EXISTENTE ('move essa para DONE', 'comenta no card X', 'volta para TODO'): "
        "delegue ao Reporter Agent, repassando o título do card mencionado nas mensagens anteriores, "
        "se houver.",
        "Use o histórico da conversa para resolver referências como 'essa tarefa' ou 'o último card'.",
        "Se a mensagem contiver várias tarefas (ex.: lista extraída de uma imagem), "
        "delegue ao PM uma tarefa por vez e, para cada card criado, delegue ao Executor uma por vez.",
        "Resposta final: resuma em no máximo 5 linhas o que foi feito, citando títulos de cards, "
        "links e nomes de arquivos gerados. Não repita o conteúdo dos arquivos.",
        "Nunca afirme que algo foi concluído se um membro reportou erro; nesse caso, explique o erro.",
        "Você responde apenas em texto. Não tente gerar áudio, voz ou imagens e não diga que não tem "
        "ferramentas para isso: o bot converte sua resposta em áudio quando o usuário pede.",
    ],
)
