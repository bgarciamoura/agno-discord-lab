"""Bot Discord multimodal do lab: texto, notas de voz e imagens viram tarefas no Trello.

Fluxo por mensagem (ver README):
  1. INTAKE  — áudio → Whisper → texto; imagem → Vision Analyst → tarefas em texto.
  2. TEAM    — Team do agno (PM / Executor / Reporter) com memória por canal.
  3. OUTPUT  — texto em pedaços de 2000, arquivos gerados e, se a entrada foi áudio, um mp3.
"""

import asyncio
import logging
import os
from pathlib import Path

import discord
from dotenv import load_dotenv

from agents.team import project_team
from agents.vision import describe_image_as_tasks
from services.stt import transcribe_audio
from services.text import (
    chunk_text,
    classify_attachments,
    make_spoken_summary,
    strip_audio_request,
    strip_think,
    wants_audio_reply,
)
from services.tts import synthesize_speech

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("bot")

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OUTPUT_ROOT = Path("outputs")
MAX_FILES_PER_MESSAGE = 10
MAX_FILE_BYTES = 8 * 1024 * 1024  # limite do Discord sem Nitro

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


async def send_long(channel: discord.abc.Messageable, text: str) -> None:
    """Envia texto respeitando o limite de 2000 caracteres por mensagem."""
    for chunk in chunk_text(text):
        if chunk.strip():
            await channel.send(chunk)


async def safe_reply(message: discord.Message, content: str = "", **kwargs) -> None:
    """message.reply com fallback para channel.send (a mensagem original pode ter sumido)."""
    try:
        await message.reply(content, **kwargs)
    except discord.HTTPException:
        await message.channel.send(content, **kwargs)


def collect_files(run_dir: Path) -> list[discord.File]:
    """Arquivos gerados nesta execução (exceto o mp3, adicionado à parte)."""
    files = []
    for path in sorted(run_dir.iterdir()) if run_dir.exists() else []:
        if not path.is_file() or path.suffix == ".mp3":
            continue
        if path.stat().st_size > MAX_FILE_BYTES:
            log.warning("Arquivo %s excede o limite do Discord, não será enviado", path.name)
            continue
        files.append(discord.File(path))
    return files[:MAX_FILES_PER_MESSAGE]


# --------------------------------------------------------------------------- #
# Intake multimodal
# --------------------------------------------------------------------------- #


async def build_prompt(message: discord.Message, text: str) -> tuple[str, bool]:
    """Converte texto + anexos (áudio/imagem) em um único prompt de texto.

    Returns:
        (prompt, reply_with_audio)
    """
    reply_with_audio = wants_audio_reply(text)
    prompt = strip_audio_request(text)  # o pedido de áudio é tratado aqui, não pelo Team
    media = classify_attachments(message.attachments)

    if media.audio is not None:
        data = await media.audio.read()
        transcript = await asyncio.to_thread(transcribe_audio, data, media.audio.filename)
        if not transcript:
            await safe_reply(message, "🎙️ Não consegui entender o áudio. Pode repetir?")
        else:
            await safe_reply(message, f"🎙️ **Transcrição:** _{transcript}_")
            prompt = f"{prompt}\n\n[Mensagem de voz transcrita]: {transcript}" if prompt else transcript
            reply_with_audio = True

    for att in media.images:
        data = await att.read()
        tasks_md = await asyncio.to_thread(describe_image_as_tasks, data, att.content_type, text)
        await safe_reply(message, f"🖼️ **Análise de {att.filename}:**\n{tasks_md[:1800]}")
        if "nenhuma tarefa identificada" in tasks_md.lower():
            continue
        if not prompt:
            prompt = "Crie e execute as tarefas abaixo:"
        prompt += f"\n\n[Tarefas extraídas da imagem {att.filename}]:\n{tasks_md}"

    return prompt.strip(), reply_with_audio


# --------------------------------------------------------------------------- #
# Eventos
# --------------------------------------------------------------------------- #


@client.event
async def on_ready():
    log.info("Bot conectado como %s", client.user)


@client.event
async def on_message(message: discord.Message):
    if message.author == client.user:
        return
    if client.user not in message.mentions:
        return

    text = message.content.replace(f"<@{client.user.id}>", "").strip()
    run_dir = OUTPUT_ROOT / str(message.channel.id) / str(message.id)
    run_dir.mkdir(parents=True, exist_ok=True)

    try:
        async with message.channel.typing():
            prompt, reply_with_audio = await build_prompt(message, text)
            if not prompt:
                await safe_reply(message, "Me envie um pedido em texto, uma nota de voz ou uma imagem com as tarefas.")
                return

            log.info("[%s] prompt: %.120s", message.channel.id, prompt)

            # Team é síncrono: roda em thread para não travar o heartbeat do Discord.
            response = await asyncio.to_thread(
                project_team.run,
                prompt,
                session_id=f"discord-{message.channel.id}",
                user_id=str(message.author.id),
                dependencies={"output_dir": str(run_dir)},
            )

            reply_text = strip_think(response.content or "") or "Concluído, mas o time não retornou texto."
            files = collect_files(run_dir)

            if reply_with_audio:
                try:
                    mp3 = await synthesize_speech(make_spoken_summary(reply_text), run_dir / "resposta.mp3")
                    files.append(discord.File(mp3))
                except Exception:  # TTS é opcional: degrada para texto
                    log.exception("Falha no TTS; respondendo só em texto")

        chunks = chunk_text(reply_text)
        await safe_reply(message, chunks[0], files=files[:MAX_FILES_PER_MESSAGE])
        for chunk in chunks[1:]:
            await message.channel.send(chunk)

    except Exception as exc:
        log.exception("Falha ao processar mensagem %s", message.id)
        await safe_reply(message, f"❌ Não consegui concluir: `{type(exc).__name__}`. Veja o log do bot.")


if __name__ == "__main__":
    if not DISCORD_TOKEN:
        raise SystemExit("DISCORD_TOKEN não definido no .env")
    client.run(DISCORD_TOKEN, log_handler=None)
