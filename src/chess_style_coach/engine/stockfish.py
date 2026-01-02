from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import chess
import chess.engine

from chess_style_coach.config import DEFAULT_DEPTH, DEFAULT_MULTIPV, DEFAULT_TIME, STOCKFISH_PATH


@dataclass
class EngineLine:
    move_uci: str
    score_type: str  # "cp" ou "mate"
    score_value: int
    pv_uci: list[str]


def _score_to_simple(score: chess.engine.PovScore, turn: chess.Color) -> tuple[str, int]:
    """
    Convertit le score Stockfish en (type, valeur) du point de vue du camp au trait.
    - "mate": nombre de coups avant mat (positif = mat pour le camp au trait)
    - "cp": centipawns (positif = avantage camp au trait)
    """
    s = score.pov(turn)
    mate = s.mate()
    if mate is not None:
        return ("mate", int(mate))
    cp = s.score(mate_score=100000)
    return ("cp", int(cp))


def analyze_fen(
    fen: str,
    depth: int = DEFAULT_DEPTH,
    multipv: int = DEFAULT_MULTIPV,
    limit_time: float | None = None,
) -> dict[str, Any]:
    """
    Analyse une position (FEN) et renvoie les meilleures lignes (MultiPV).
    """
    if not STOCKFISH_PATH:
        raise RuntimeError("STOCKFISH_PATH n'est pas défini. Ajoute-le dans ton fichier .env.")

    board = chess.Board(fen)
    turn_str = "white" if board.turn == chess.WHITE else "black"

    if limit_time is None:
        limit_time = DEFAULT_TIME if DEFAULT_TIME > 0 else None

    limit = chess.engine.Limit(time=limit_time) if limit_time else chess.engine.Limit(depth=depth)

    lines: list[EngineLine] = []

    with chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH) as engine:

        info = engine.analyse(board, limit, multipv=int(multipv))
        infos = info if isinstance(info, list) else [info]

        for inf in infos:
            pv = inf.get("pv", [])
            if not pv:
                continue

            best_move = pv[0]
            score = inf.get("score")
            if score is None:
                continue

            score_type, score_value = _score_to_simple(score, board.turn)

            lines.append(
                EngineLine(
                    move_uci=best_move.uci(),
                    score_type=score_type,
                    score_value=score_value,
                    pv_uci=[m.uci() for m in pv],
                )
            )

    return {
        "fen": fen,
        "turn": turn_str,
        "depth": depth if not limit_time else None,
        "time": limit_time,
        "lines": lines,
    }
