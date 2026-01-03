from __future__ import annotations

from typing import Any


def build_chess_prompt(question: str, fen: str | None, engine_out: dict[str, Any] | None) -> str:
    """
    Construit un prompt clair pour un assistant d'échecs.
    On inclut :
    - la question utilisateur
    - la FEN si disponible
    - l'analyse Stockfish structurée si disponible
    """
    parts = []
    parts.append("Tu es un coach d'échecs très pédagogique. Réponds en français, clairement, avec des étapes.")
    parts.append("Ne donne pas seulement 'le meilleur coup' : explique les idées (plans, menaces, sécurité du roi).")
    parts.append("Si tu n'es pas sûr, dis-le. N'invente pas des variantes impossibles.")

    parts.append("\nQuestion utilisateur :")
    parts.append(question.strip())

    if fen:
        parts.append("\nPosition (FEN) :")
        parts.append(fen)

    if engine_out:
        parts.append("\nAnalyse moteur (Stockfish, structurée) :")
        # Version compact pour limiter les tokens
        lines = engine_out.get("lines", [])[:3]
        compact_lines = []
        for line in lines:
            compact_lines.append(
                {
                    "move_uci": line.move_uci,
                    "score_type": line.score_type,
                    "score_value": line.score_value,
                    "pv_uci": line.pv_uci[:10],
                }
            )
        parts.append(str(compact_lines))

    return "\n".join(parts)
