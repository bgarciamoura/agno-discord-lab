"""Tool que permite ao Executor salvar entregáveis reais (código, SQL, docs) em disco.

O parâmetro `run_context` é injetado automaticamente pelo agno (ele NÃO aparece
no schema que o modelo enxerga — veja FRAMEWORK_INJECTED_PARAMS em
agno/tools/function.py). Por ele chegam o session_id, o run_id e o dicionário
`dependencies` passado em Team.run(...), que usamos para saber em qual pasta
o main.py espera encontrar os arquivos desta mensagem.
"""

from pathlib import Path
from typing import Optional

from agno.run.base import RunContext

ALLOWED_EXT = {".md", ".txt", ".sql", ".py", ".js", ".ts", ".json", ".csv", ".yaml", ".yml", ".html"}
MAX_CHARS = 20_000
DEFAULT_ROOT = Path("outputs")


def _resolve_output_dir(run_context: Optional[RunContext]) -> Path:
    """Pasta onde salvar: dependencies["output_dir"] > outputs/<session>/<run> > outputs/adhoc."""
    if run_context is not None:
        deps = run_context.dependencies or {}
        if deps.get("output_dir"):
            out = Path(deps["output_dir"])
        else:
            out = DEFAULT_ROOT / (run_context.session_id or "sessao") / (run_context.run_id or "run")
    else:
        out = DEFAULT_ROOT / "adhoc"

    out.mkdir(parents=True, exist_ok=True)
    return out


def save_deliverable(filename: str, content: str, run_context: RunContext = None) -> str:
    """Salva um entregável (código, script SQL, documento markdown etc.) em arquivo.

    Args:
        filename: nome simples com extensão, ex.: "schema.sql", "relatorio.md".
        content: conteúdo completo do arquivo.

    Returns:
        Caminho absoluto do arquivo salvo (use em attach_file_to_card), ou "Erro: ...".
    """
    safe_name = Path(filename).name.strip().replace(" ", "_")
    if not safe_name or safe_name.startswith("."):
        return "Erro: nome de arquivo inválido."

    ext = Path(safe_name).suffix.lower()
    if ext not in ALLOWED_EXT:
        return f"Erro: extensão '{ext or '(nenhuma)'}' não permitida. Use uma de: {', '.join(sorted(ALLOWED_EXT))}."

    if not content or not content.strip():
        return "Erro: conteúdo vazio."

    if len(content) > MAX_CHARS:
        content = content[:MAX_CHARS] + "\n\n[... conteúdo truncado ...]\n"

    try:
        out_dir = _resolve_output_dir(run_context)
        path = out_dir / safe_name
        path.write_text(content, encoding="utf-8")
    except OSError as exc:
        return f"Erro ao salvar arquivo: {type(exc).__name__}"

    return str(path.resolve())
