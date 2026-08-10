"""Narrative LLM optionnelle via Ollama (local, souverain) — best-effort.

EN: Optional local-LLM narrative. Retourne None si OLLAMA_URL non défini ou
en cas d'échec — le rapport CSR reste complet avec les paragraphes factuels.
"""
from __future__ import annotations

from typing import Any

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

log = structlog.get_logger()

DEFAULT_MODEL = "llama3.1:8b"

_PROMPT_FR = """Tu es un rédacteur ESG. Résume en 5 phrases maximum, en français
professionnel, ce contexte de conformité environnementale pour un rapport CSR.
Ne crée aucun chiffre : utilise uniquement ceux fournis.

Contexte JSON :
{context}
"""


@retry(stop=stop_after_attempt(2), wait=wait_exponential(min=1, max=5), reraise=True)
def _generate(ollama_url: str, model: str, prompt: str) -> str:
    resp = httpx.post(
        f"{ollama_url.rstrip('/')}/api/generate",
        json={"model": model, "prompt": prompt, "stream": False},
        timeout=120.0,
    )
    resp.raise_for_status()
    return str(resp.json()["response"]).strip()


def generate_narrative(
    ollama_url: str | None,
    context: dict[str, Any],
    model: str = DEFAULT_MODEL,
) -> str | None:
    """Narrative FR générée localement, ou None si désactivée/en échec.

    EN: Best-effort — failures are logged, never raised.
    """
    if not ollama_url:
        log.info("ollama_disabled")
        return None
    try:
        import json

        narrative = _generate(
            ollama_url, model, _PROMPT_FR.format(context=json.dumps(context, ensure_ascii=False))
        )
        log.info("ollama_narrative_generated", model=model)
        return narrative
    except (httpx.HTTPError, KeyError) as exc:
        log.error("ollama_failed", error=str(exc))
        return None
