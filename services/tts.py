"""Text-to-speech gratuito com edge-tts (vozes neurais da Microsoft, sem chave).

A API do edge-tts já é assíncrona: chame `await synthesize_speech(...)` direto
no event loop (sem `to_thread`).
"""

import os
from pathlib import Path
from typing import Optional

import edge_tts
from dotenv import load_dotenv

load_dotenv()

DEFAULT_VOICE = "pt-BR-AntonioNeural"


async def synthesize_speech(text: str, out_path: Path, voice: Optional[str] = None) -> Path:
    """Gera um mp3 falando `text` e salva em `out_path`.

    Raises:
        Exception: qualquer falha de rede/serviço — o chamador decide degradar para texto.
    """
    voice = voice or os.getenv("TTS_VOICE", DEFAULT_VOICE)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(out_path))
    return out_path
