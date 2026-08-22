"""Ferramentas (tools) de integração com o Trello usadas pelos agentes.

Todas as funções retornam dados simples (dict/list/str). Em caso de falha HTTP
ou de rede elas devolvem uma string começando com "Erro Trello" em vez de
levantar exceção — assim o agente consegue reagir ao erro e nenhuma URL com
credenciais vai parar nos logs.
"""

import os
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.trello.com/1"
TIMEOUT = 15

API_KEY = os.getenv("TRELLO_API_KEY")
TOKEN = os.getenv("TRELLO_TOKEN")
BOARD_ID = os.getenv("TRELLO_BOARD_ID")
TODO_LIST_ID = os.getenv("TRELLO_TODO_LIST_ID")
DOING_LIST_ID = os.getenv("TRELLO_DOING_LIST_ID")
DONE_LIST_ID = os.getenv("TRELLO_DONE_LIST_ID")

MAX_CARDS_PER_LIST = 30


def _list_names() -> dict[str, str]:
    """Mapa idList -> nome lógico (TODO/DOING/DONE)."""
    return {TODO_LIST_ID: "TODO", DOING_LIST_ID: "DOING", DONE_LIST_ID: "DONE"}


def _request(method: str, path: str, **kwargs):
    """Executa uma chamada à API do Trello injetando key/token.

    Retorna o JSON da resposta ou uma string "Erro Trello (...)" — nunca a URL,
    que contém as credenciais.
    """
    params = {"key": API_KEY, "token": TOKEN, **kwargs.pop("params", {})}
    try:
        response = requests.request(
            method, f"{BASE_URL}{path}", params=params, timeout=TIMEOUT, **kwargs
        )
        response.raise_for_status()
        return response.json()
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else "?"
        body = exc.response.text[:200] if exc.response is not None else ""
        return f"Erro Trello (HTTP {status}): {body}"
    except requests.RequestException as exc:
        return f"Erro Trello (rede): {type(exc).__name__}"


def _is_error(result) -> bool:
    return isinstance(result, str) and result.startswith("Erro Trello")


# --------------------------------------------------------------------------- #
# Escrita
# --------------------------------------------------------------------------- #


def create_card(title: str, description: str):
    """Cria um card na lista TODO do board.

    Args:
        title: título curto da tarefa.
        description: descrição objetiva do que deve ser feito.

    Returns:
        dict com card_id, title e url do card criado, ou mensagem de erro.
    """
    card = _request(
        "POST",
        "/cards",
        params={"idList": TODO_LIST_ID, "name": title, "desc": description},
    )
    if _is_error(card):
        return card
    return {"card_id": card["id"], "title": card["name"], "url": card.get("shortUrl")}


def move_card(card_id: str, status: str):
    """Move um card para a lista TODO, DOING ou DONE.

    Args:
        card_id: id do card (use exatamente o valor retornado por find_card/create_card).
        status: "TODO", "DOING" ou "DONE".
    """
    lists = {"TODO": TODO_LIST_ID, "DOING": DOING_LIST_ID, "DONE": DONE_LIST_ID}
    list_id = lists.get(status.upper())
    if not list_id:
        return "Status inválido. Use TODO, DOING ou DONE."

    result = _request("PUT", f"/cards/{card_id}", params={"idList": list_id})
    if _is_error(result):
        return result
    return f"Card movido para {status.upper()}."


def add_comment(card_id: str, comment: str):
    """Adiciona um comentário em um card.

    Args:
        card_id: id do card.
        comment: texto do comentário.
    """
    result = _request("POST", f"/cards/{card_id}/actions/comments", params={"text": comment})
    if _is_error(result):
        return result
    return "Comentário adicionado."


def attach_file_to_card(card_id: str, file_path: str):
    """Anexa um arquivo local ao card do Trello.

    Args:
        card_id: id do card.
        file_path: caminho do arquivo (use o valor retornado por save_deliverable).
    """
    path = Path(file_path)
    if not path.is_file():
        return f"Erro: arquivo não encontrado: {path.name}"

    with path.open("rb") as fh:
        result = _request(
            "POST",
            f"/cards/{card_id}/attachments",
            files={"file": (path.name, fh)},
        )
    if _is_error(result):
        return result
    return f"Arquivo {path.name} anexado ao card."


# --------------------------------------------------------------------------- #
# Leitura
# --------------------------------------------------------------------------- #


def find_card(title: str):
    """Localiza um card pelo título (busca parcial, sem diferenciar maiúsculas).

    Se houver mais de um card compatível, retorna o de atividade mais recente.

    Args:
        title: título (ou parte dele) do card procurado.

    Returns:
        dict com card_id, title, status e url, ou None se nenhum card for encontrado.
    """
    cards = _request(
        "GET",
        f"/boards/{BOARD_ID}/cards",
        params={"fields": "name,idList,dateLastActivity,shortUrl"},
    )
    if _is_error(cards):
        return cards

    needle = title.lower()
    matches = [c for c in cards if needle in c["name"].lower()]
    if not matches:
        return None

    card = max(matches, key=lambda c: c.get("dateLastActivity") or "")
    return {
        "card_id": card["id"],
        "title": card["name"],
        "status": _list_names().get(card["idList"], "OUTRA"),
        "url": card.get("shortUrl"),
    }


def list_board_cards():
    """Lista os cards do board agrupados por status (TODO, DOING, DONE).

    Use para responder perguntas sobre o andamento do projeto.

    Returns:
        dict {"TODO": [...], "DOING": [...], "DONE": [...]} onde cada item tem
        card_id, title, url e last_activity.
    """
    cards = _request(
        "GET",
        f"/boards/{BOARD_ID}/cards",
        params={"fields": "name,idList,dateLastActivity,shortUrl"},
    )
    if _is_error(cards):
        return cards

    names = _list_names()
    grouped: dict[str, list] = {"TODO": [], "DOING": [], "DONE": []}
    for card in sorted(cards, key=lambda c: c.get("dateLastActivity") or "", reverse=True):
        status = names.get(card["idList"], "OUTRA")
        bucket = grouped.setdefault(status, [])
        if len(bucket) >= MAX_CARDS_PER_LIST:
            continue
        bucket.append(
            {
                "card_id": card["id"],
                "title": card["name"],
                "url": card.get("shortUrl"),
                "last_activity": card.get("dateLastActivity"),
            }
        )
    return grouped


def get_card_comments(card_id: str, limit: int = 5):
    """Retorna os últimos comentários de um card (mais recentes primeiro).

    Args:
        card_id: id do card.
        limit: quantidade máxima de comentários.
    """
    actions = _request(
        "GET",
        f"/cards/{card_id}/actions",
        params={"filter": "commentCard", "limit": limit},
    )
    if _is_error(actions):
        return actions
    return [{"date": a.get("date"), "text": a["data"].get("text", "")} for a in actions]
