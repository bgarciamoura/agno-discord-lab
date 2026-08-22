"""Testes das tools do Trello com `requests.request` simulado (sem rede)."""

import requests

from tools import trello


class FakeResponse:
    def __init__(self, status=200, payload=None, text=""):
        self.status_code = status
        self._payload = payload
        self.text = text

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} error", response=self)


def fake_request(payload, status=200, text="", calls=None):
    def _request(method, url, **kwargs):
        if calls is not None:
            calls.append({"method": method, "url": url, **kwargs})
        return FakeResponse(status, payload, text)

    return _request


BOARD_CARDS = [
    {"id": "c1", "name": "Tela de Login v2", "idList": "list-doing", "dateLastActivity": "2026-08-20", "shortUrl": "u1"},
    {"id": "c2", "name": "Login", "idList": "list-todo", "dateLastActivity": "2026-08-22", "shortUrl": "u2"},
    {"id": "c3", "name": "Relatório mensal", "idList": "list-done", "dateLastActivity": "2026-08-01", "shortUrl": "u3"},
    {"id": "c4", "name": "Card em lista extra", "idList": "list-x", "dateLastActivity": "2026-08-02", "shortUrl": "u4"},
]


def test_find_card_substring_case_insensitive_returns_most_recent(monkeypatch):
    monkeypatch.setattr(trello.requests, "request", fake_request(BOARD_CARDS))
    result = trello.find_card("login")
    assert result == {"card_id": "c2", "title": "Login", "status": "TODO", "url": "u2"}


def test_find_card_returns_none_when_no_match(monkeypatch):
    monkeypatch.setattr(trello.requests, "request", fake_request(BOARD_CARDS))
    assert trello.find_card("inexistente") is None


def test_list_board_cards_groups_by_env_list_ids(monkeypatch):
    monkeypatch.setattr(trello.requests, "request", fake_request(BOARD_CARDS))
    grouped = trello.list_board_cards()
    assert [c["card_id"] for c in grouped["TODO"]] == ["c2"]
    assert [c["card_id"] for c in grouped["DOING"]] == ["c1"]
    assert [c["card_id"] for c in grouped["DONE"]] == ["c3"]
    assert [c["card_id"] for c in grouped["OUTRA"]] == ["c4"]


def test_create_card_returns_compact_dict_and_sends_auth(monkeypatch):
    calls = []
    payload = {"id": "new1", "name": "Título", "shortUrl": "https://trello.com/c/x"}
    monkeypatch.setattr(trello.requests, "request", fake_request(payload, calls=calls))

    result = trello.create_card("Título", "desc")

    assert result == {"card_id": "new1", "title": "Título", "url": "https://trello.com/c/x"}
    assert calls[0]["method"] == "POST"
    assert calls[0]["params"]["idList"] == "list-todo"
    assert calls[0]["params"]["token"] == "SUPER-SECRET-TOKEN"
    assert calls[0]["timeout"] == trello.TIMEOUT


def test_move_card_rejects_unknown_status(monkeypatch):
    monkeypatch.setattr(trello.requests, "request", fake_request({}))
    assert "inválido" in trello.move_card("c1", "BLOCKED")
    assert trello.move_card("c1", "todo") == "Card movido para TODO."


def test_http_error_is_returned_without_leaking_token(monkeypatch):
    monkeypatch.setattr(
        trello.requests,
        "request",
        fake_request(None, status=401, text="invalid token https://api.trello.com/1/cards?token=SUPER-SECRET-TOKEN"[:30]),
    )
    result = trello.add_comment("c1", "oi")
    assert result.startswith("Erro Trello (HTTP 401)")
    assert "SUPER-SECRET-TOKEN" not in result


def test_network_error_is_returned_as_message(monkeypatch):
    def boom(*args, **kwargs):
        raise requests.ConnectionError("down")

    monkeypatch.setattr(trello.requests, "request", boom)
    assert trello.list_board_cards() == "Erro Trello (rede): ConnectionError"


def test_get_card_comments_flattens_actions(monkeypatch):
    actions = [{"date": "2026-08-22", "data": {"text": "Execução iniciada."}}]
    monkeypatch.setattr(trello.requests, "request", fake_request(actions))
    assert trello.get_card_comments("c1") == [{"date": "2026-08-22", "text": "Execução iniciada."}]


def test_attach_file_to_card_missing_file():
    assert trello.attach_file_to_card("c1", "/nao/existe.md").startswith("Erro")
