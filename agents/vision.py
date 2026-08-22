"""Agente "sensor" de visão: transforma uma imagem em uma lista de tarefas em texto.

Não é membro do Team — roda antes dele (camada de intake em main.py). Assim o
Team e os demais agentes continuam trabalhando só com texto.
"""

from agno.agent import Agent
from agno.media import Image

from agents.config import make_model
from services.text import strip_think

vision_agent = Agent(
    name="Vision Analyst",
    model=make_model(),
    role="Analista de Requisitos Visuais",
    instructions=[
        "Você analisa imagens (fotos de quadro branco, prints de requisitos, diagramas, post-its).",
        "Responda sempre em português.",
        "Extraia as tarefas / itens de trabalho presentes na imagem.",
        "Saída OBRIGATÓRIA em markdown, sem comentários extras, neste formato:",
        "## Contexto: <1 linha sobre o que a imagem mostra>",
        "## Tarefas:",
        "- <título curto>: <descrição objetiva em 1 linha>",
        "Se não houver tarefas identificáveis, responda apenas: 'Nenhuma tarefa identificada.'",
        "Não invente itens que não estejam visíveis na imagem.",
    ],
)


def describe_image_as_tasks(data: bytes, mime_type: str, user_hint: str = "") -> str:
    """Roda o agente de visão sobre os bytes de uma imagem e devolve o markdown de tarefas.

    Args:
        data: bytes da imagem.
        mime_type: ex. "image/png", "image/jpeg".
        user_hint: texto que o usuário enviou junto (ajuda a direcionar a extração).
    """
    fmt = (mime_type or "image/png").split("/")[-1]
    image = Image(content=data, mime_type=mime_type or "image/png", format=fmt)

    prompt = "Extraia as tarefas desta imagem."
    if user_hint:
        prompt += f"\nContexto dado pelo usuário: {user_hint}"

    response = vision_agent.run(prompt, images=[image])
    return strip_think(response.content or "").strip() or "Nenhuma tarefa identificada."
