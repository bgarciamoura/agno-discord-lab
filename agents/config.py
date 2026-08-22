"""Fábricas compartilhadas pelos agentes: modelo Groq e banco de sessões."""

import os
from pathlib import Path

from agno.db.sqlite import SqliteDb
from agno.models.groq import Groq
from dotenv import load_dotenv

load_dotenv()

DB_FILE = Path("data") / "agno.db"


def make_model() -> Groq:
    """Modelo Groq configurado pelo .env (GROQ_MODEL), sem raciocínio estendido."""
    model_id = os.getenv("GROQ_MODEL")
    if not model_id:
        raise RuntimeError("GROQ_MODEL não definido no .env")
    return Groq(id=model_id, request_params={"reasoning_effort": "none"})


def make_db() -> SqliteDb:
    """Banco SQLite local onde o agno guarda o histórico das sessões (memória)."""
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    return SqliteDb(db_file=str(DB_FILE))
