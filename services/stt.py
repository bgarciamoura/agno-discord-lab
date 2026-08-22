"""Speech-to-text com Whisper hospedado no Groq.

Chamada síncrona — em código async use `asyncio.to_thread(transcribe_audio, ...)`.
"""

import os

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

DEFAULT_STT_MODEL = "whisper-large-v3-turbo"
MIN_TRANSCRIPT_CHARS = 3


def transcribe_audio(data: bytes, filename: str = "audio.ogg", language: str = "pt") -> str:
    """Transcreve bytes de áudio (ogg/mp3/wav/m4a) em texto.

    Returns:
        Texto transcrito, ou string vazia se o áudio não tiver fala reconhecível.
    """
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    result = client.audio.transcriptions.create(
        file=(filename, data),
        model=os.getenv("GROQ_STT_MODEL", DEFAULT_STT_MODEL),
        language=language,
        response_format="text",
    )
    text = result if isinstance(result, str) else getattr(result, "text", "")
    text = (text or "").strip()
    return text if len(text) >= MIN_TRANSCRIPT_CHARS else ""
