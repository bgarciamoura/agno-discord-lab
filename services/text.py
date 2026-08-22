"""Funções puras de texto usadas pelo intake/output (fáceis de testar sem rede)."""

import re
from types import SimpleNamespace
from typing import Iterable

_THINK_RE = re.compile(r"<think>.*?</think>\s*", flags=re.DOTALL | re.IGNORECASE)
_MD_LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")
_URL_RE = re.compile(r"https?://\S+")
_EMOJI_RE = re.compile(r"[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\uFE0F]")

_AUDIO_REQUEST_RE = re.compile(
    r"(?:me\s+)?respond[ae]\s+em\s+[áa]udio(?:\s+por\s+favor)?\s*[:,.-]?\s*|\s*em\s+voz\b\s*[:,.-]?\s*",
    flags=re.IGNORECASE,
)

DISCORD_MSG_LIMIT = 2000


def strip_think(text: str) -> str:
    """Remove blocos <think>...</think> que alguns modelos (ex. qwen) emitem no conteúdo."""
    if not text:
        return ""
    return _THINK_RE.sub("", text).strip()


def chunk_text(text: str, limit: int = DISCORD_MSG_LIMIT) -> list[str]:
    """Divide o texto em pedaços de até `limit` caracteres (limite do Discord)."""
    return [text[i : i + limit] for i in range(0, len(text), limit)] or [""]


def make_spoken_summary(text: str, limit: int = 600) -> str:
    """Prepara o texto para o TTS: sem <think>, sem markdown/links, cortado em uma frase."""
    text = strip_think(text)
    text = _MD_LINK_RE.sub(r"\1", text)
    text = _URL_RE.sub("", text)
    text = _EMOJI_RE.sub("", text)
    text = re.sub(r"[`*_#>|]+", "", text)
    text = re.sub(r"^\s*[-•]\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\s+", " ", text).strip()

    if len(text) <= limit:
        return text

    cut = text[:limit]
    last_stop = max(cut.rfind(". "), cut.rfind("! "), cut.rfind("? "))
    return (cut[: last_stop + 1] if last_stop > limit // 3 else cut).strip()


def classify_attachments(attachments: Iterable) -> SimpleNamespace:
    """Separa anexos do Discord em áudio (no máximo um) e imagens (até 3).

    Aceita qualquer objeto com `content_type` e `is_voice_message()` (discord.Attachment
    ou um SimpleNamespace nos testes).
    """
    audio = None
    images = []
    for att in attachments:
        ctype = (getattr(att, "content_type", None) or "").lower()
        is_voice = getattr(att, "is_voice_message", lambda: False)()
        if audio is None and (is_voice or ctype.startswith("audio/")):
            audio = att
        elif ctype.startswith("image/") and len(images) < 3:
            images.append(att)
    return SimpleNamespace(audio=audio, images=images)


def wants_audio_reply(prompt: str) -> bool:
    """Detecta pedidos explícitos de resposta falada."""
    return bool(_AUDIO_REQUEST_RE.search(prompt or ""))


def strip_audio_request(prompt: str) -> str:
    """Remove o pedido de 'responda em áudio' do texto.

    O áudio é gerado pelo bot (main.py), não pelo Team — se a frase chegasse ao
    Team ele tentaria "gerar áudio" e ignoraria o pedido real.
    """
    return _AUDIO_REQUEST_RE.sub(" ", prompt or "").strip(" :,.-").strip()
