from __future__ import annotations

from dataclasses import dataclass

from chess_style_coach.config import OPENAI_API_KEY, OPENAI_MAX_TOKENS, OPENAI_MODEL, OPENAI_TEMPERATURE


@dataclass
class LLMConfig:
    model: str = OPENAI_MODEL
    max_tokens: int = OPENAI_MAX_TOKENS
    temperature: float = OPENAI_TEMPERATURE


def llm_enabled() -> bool:
    return bool(OPENAI_API_KEY.strip())


def generate_with_llm(prompt: str, cfg: LLMConfig | None = None) -> str:
    """
    Stub LLM : volontairement non fonctionnel tant que l'API n'est pas branchée.
    L'idée est d'avoir une interface stable, prête à être implémentée plus tard.
    """
    if not llm_enabled():
        raise RuntimeError("LLM non activé : OPENAI_API_KEY manquant.")

    # Implémentation ici de l'appel API plus tard
    raise NotImplementedError("LLM backend pas encore implémenté.")
