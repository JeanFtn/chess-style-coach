from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import chess

from chess_style_coach.engine.stockfish import analyze_fen
from chess_style_coach.coaching.formatting import explain_from_engine_output

from chess_style_coach.llm.client import generate_with_llm, llm_enabled
from chess_style_coach.llm.prompts import build_chess_prompt


@dataclass
class ChatRequest:
    question: str
    fen: Optional[str] = None
    mode: str = "detailed"  # "short" ou "detailed"
    depth: int | None = None
    multipv: int | None = None


@dataclass
class ChatMemory:
    last_fen: Optional[str] = None
    last_engine_out: Optional[dict] = None


def _normalize_fen(fen: str) -> str:
    """Valide et normalise une FEN (raises si invalide)."""
    b = chess.Board(fen)
    return b.fen()


def _short_answer(engine_output: dict) -> str:
    """Version courte (lisible en chat)."""
    lines = engine_output["lines"]
    if not lines:
        return "Je n’ai pas pu récupérer de lignes d’analyse depuis le moteur."

    board = chess.Board(engine_output["fen"])
    side = "Blancs" if board.turn == chess.WHITE else "Noirs"

    best = lines[0]
    move_san = board.san(chess.Move.from_uci(best.move_uci))

    if best.score_type == "cp":
        eval_pawns = best.score_value / 100.0
        sign = "+" if eval_pawns > 0 else ""
        eval_text = f"{sign}{eval_pawns:.2f}"
    else:
        m = best.score_value
        eval_text = f"mat en {m}" if m > 0 else f"mat subi en {abs(m)}"

    # top 3 coups en SAN
    top_moves = []
    for line in lines[:3]:
        mv = chess.Move.from_uci(line.move_uci)
        top_moves.append(board.san(mv))

    return (
        f"Au trait : {side}. Évaluation : {eval_text}.\n"
        f"Meilleur coup : **{move_san}**.\n"
        f"Autres options : {', '.join(top_moves[1:]) if len(top_moves) > 1 else '—'}"
    )


def generate_answer(req: ChatRequest, memory: ChatMemory) -> tuple[str, ChatMemory]:
    """
    Orchestrateur du chat.
    - Si FEN fournie : analyse Stockfish + réponse
    - Mémoire : réutilise la dernière FEN et la dernière analyse si possible
    - Optionnel : si LLM activé, génération via LLM, sinon fallback local
    """
    question = req.question.strip()

    # Choix de la FEN : celle de la requête, sinon celle en mémoire
    effective_fen = req.fen.strip() if req.fen else None
    if not effective_fen:
        effective_fen = memory.last_fen

    if not effective_fen:
        return (
            "Pour l’instant, je peux surtout répondre à partir d’une position.\n"
            "Colle une FEN dans la sidebar, puis pose ta question."
        ), memory

    fen = _normalize_fen(effective_fen)

    # Analyse Stockfish : on réutilise la dernière analyse si la FEN n’a pas changé
    reuse_engine = (
        memory.last_fen == fen and memory.last_engine_out is not None
    )

    if reuse_engine:
        engine_out = memory.last_engine_out
    else:
        kwargs = {}
        if req.depth is not None:
            kwargs["depth"] = req.depth
        if req.multipv is not None:
            kwargs["multipv"] = req.multipv
        engine_out = analyze_fen(fen, **kwargs)

    # Met à jour la mémoire
    memory.last_fen = fen
    memory.last_engine_out = engine_out

    # Si LLM activé, préparation du prompt (mais l'appel n'est pas encore implémenté)
    if llm_enabled():
        prompt = build_chess_prompt(question=question, fen=fen, engine_out=engine_out)
        # Pour l'instant, ça lèvera NotImplementedError tant que l'API n'est pas branchée
        try:
            answer = generate_with_llm(prompt)
            return answer, memory
        except NotImplementedError:
            # Tant que l'API n'est pas branchée, on retombe en local
            pass

    # Génération de la réponse
    if req.mode == "short":
        return _short_answer(engine_out), memory

    return explain_from_engine_output(engine_out), memory
