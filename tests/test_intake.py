"""Testes das funções puras de texto/intake (services/text.py)."""

from types import SimpleNamespace

from services.text import (
    chunk_text,
    classify_attachments,
    make_spoken_summary,
    strip_think,
    wants_audio_reply,
)


def att(content_type=None, voice=False, name="f"):
    return SimpleNamespace(content_type=content_type, is_voice_message=lambda: voice, filename=name)


def test_strip_think_removes_reasoning_block():
    assert strip_think("<think>\nraciocínio...\n</think>\nResposta final") == "Resposta final"
    assert strip_think("sem think") == "sem think"
    assert strip_think("") == ""


def test_chunk_text_respects_discord_limit():
    chunks = chunk_text("x" * 4500)
    assert [len(c) for c in chunks] == [2000, 2000, 500]
    assert chunk_text("") == [""]


def test_classify_attachments_picks_one_audio_and_up_to_three_images():
    media = classify_attachments(
        [
            att("image/png", name="i1"),
            att("audio/ogg", voice=True, name="voz"),
            att("audio/mpeg", name="mp3-ignorado"),
            att("image/jpeg", name="i2"),
            att("image/webp", name="i3"),
            att("image/gif", name="i4-ignorada"),
            att("application/pdf", name="pdf"),
        ]
    )
    assert media.audio.filename == "voz"
    assert [i.filename for i in media.images] == ["i1", "i2", "i3"]


def test_classify_attachments_handles_missing_content_type():
    media = classify_attachments([att(None, voice=True, name="voz")])
    assert media.audio.filename == "voz"
    assert media.images == []


def test_make_spoken_summary_strips_markdown_links_and_cuts_at_sentence():
    text = (
        "<think>x</think>## Resumo\n- Card **Login** criado ([link](https://trello.com/c/1)). "
        "Arquivo `schema.sql` gerado. " + "Frase longa de enchimento. " * 40
    )
    spoken = make_spoken_summary(text, limit=120)
    assert "<think>" not in spoken and "http" not in spoken and "*" not in spoken and "`" not in spoken
    assert "✅" not in make_spoken_summary("1. ✅ **Feito** 🎉")
    assert spoken.startswith("Resumo Card Login criado (link). Arquivo schema.sql gerado.")
    assert len(spoken) <= 120
    assert spoken.endswith(".")


def test_wants_audio_reply():
    assert wants_audio_reply("Responda em áudio: como está o projeto?")
    assert wants_audio_reply("me responde em audio por favor")
    assert not wants_audio_reply("crie uma tarefa")


def test_strip_audio_request_removes_only_the_request():
    from services.text import strip_audio_request

    assert strip_audio_request("Responda em áudio: como está o projeto?") == "como está o projeto?"
    assert strip_audio_request("me responde em audio por favor, crie uma tarefa X") == "crie uma tarefa X"
    assert strip_audio_request("crie uma tarefa X, em voz") == "crie uma tarefa X"
    assert strip_audio_request("crie uma tarefa") == "crie uma tarefa"
