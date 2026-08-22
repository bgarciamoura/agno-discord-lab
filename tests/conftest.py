"""Configuração comum dos testes: variáveis de ambiente falsas, nenhuma rede."""

import os
import sys
from pathlib import Path

import pytest

# Permite `import tools`, `import services` rodando pytest da raiz ou de tests/.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

FAKE_ENV = {
    "GROQ_API_KEY": "fake-groq-key",
    "GROQ_MODEL": "fake/model",
    "TRELLO_API_KEY": "fake-trello-key",
    "TRELLO_TOKEN": "SUPER-SECRET-TOKEN",
    "TRELLO_BOARD_ID": "board123",
    "TRELLO_TODO_LIST_ID": "list-todo",
    "TRELLO_DOING_LIST_ID": "list-doing",
    "TRELLO_DONE_LIST_ID": "list-done",
}

# Os módulos leem o env no import, então setamos antes de qualquer import deles.
os.environ.update(FAKE_ENV)


@pytest.fixture(autouse=True)
def fake_env(monkeypatch):
    for key, value in FAKE_ENV.items():
        monkeypatch.setenv(key, value)
