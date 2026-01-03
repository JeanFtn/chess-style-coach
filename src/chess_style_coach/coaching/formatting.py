from __future__ import annotations

from typing import Any

import chess

from chess_style_coach.engine.stockfish import EngineLine


def _cp_to_human(score_cp: int) -> str:
    """
    Convertit une évaluation centipawn en une phrase simple.
    Convention : score du point de vue du camp au trait.
    """
    # seuils "pédagogiques" (approximatifs)
    if score_cp >= 200:
        return "gros avantage"
    if score_cp >= 80:
        return "avantage clair"
    if score_cp >= 30:
        return "léger avantage"
    if score_cp <= -200:
        return "gros désavantage"
    if score_cp <= -80:
        return "désavantage clair"
    if score_cp <= -30:
        return "léger désavantage"
    return "position équilibrée"


def _score_summary(line: EngineLine) -> str:
    """Formate une évaluation (cp ou mate) en texte humain."""
    if line.score_type == "mate":
        m = line.score_value
        if m > 0:
            return f"mat en {m}"
        return f"mat subi en {abs(m)}"
    # cp
    pawns = line.score_value / 100.0
    sign = "+" if pawns > 0 else ""
    return f"{sign}{pawns:.2f}"


def _uci_line_to_san(board: chess.Board, pv_uci: list[str], max_moves: int = 6) -> list[str]:
    """
    Convertit une PV UCI en SAN lisible.
    On limite la longueur pour garder ça pédagogique.
    """
    b = board.copy()
    san_moves: list[str] = []
    for uci in pv_uci[:max_moves]:
        move = chess.Move.from_uci(uci)
        san_moves.append(b.san(move))
        b.push(move)
    return san_moves


def _simple_move_idea(board: chess.Board, move: chess.Move) -> str:
    """
    Heuristique très simple pour donner une 'idée' derrière un coup.
    Ce n'est pas parfait, mais suffisant pour une V1 sans LLM.
    """
    # check ?
    if board.gives_check(move):
        return "met le roi adverse sous pression (échec)"

    # capture ?
    if board.is_capture(move):
        return "gagne du matériel ou simplifie (capture)"

    # roque ?
    if board.is_castling(move):
        return "met le roi en sécurité et connecte les tours (roque)"

    # développement pièces
    piece = board.piece_at(move.from_square)
    if piece is not None and piece.piece_type in (chess.KNIGHT, chess.BISHOP):
        # si la pièce sort de la 1ère/8ème rangée
        from_rank = chess.square_rank(move.from_square)
        to_rank = chess.square_rank(move.to_square)
        if piece.color == chess.WHITE and from_rank == 0 and to_rank > 0:
            return "développe une pièce et améliore l’activité"
        if piece.color == chess.BLACK and from_rank == 7 and to_rank < 7:
            return "développe une pièce et améliore l’activité"

    # poussée de pion au centre
    if piece is not None and piece.piece_type == chess.PAWN:
        file_ = chess.square_file(move.to_square)
        if file_ in (3, 4):  # d/e files
            return "prend de l’espace et lutte pour le centre"

    return "améliore la position (idée générale)"


def explain_from_engine_output(engine_output: dict[str, Any]) -> str:
    """
    Transforme la sortie Stockfish en explication lisible 'type coach'.
    Attendu : dict retourné par analyze_fen.
    """
    fen = engine_output["fen"]
    lines: list[EngineLine] = engine_output["lines"]

    board = chess.Board(fen)
    side = "Blancs" if board.turn == chess.WHITE else "Noirs"

    if not lines:
        return "Je n’ai pas pu récupérer de ligne d’analyse depuis le moteur."

    best = lines[0]

    # 1) Résumé évaluation
    if best.score_type == "cp":
        eval_human = _cp_to_human(best.score_value)
        eval_str = _score_summary(best)
        header = f"Au trait : {side}. Évaluation : {eval_str} ({eval_human})."
    else:
        header = f"Au trait : {side}. Évaluation : {_score_summary(best)}."

    # 2) Coups candidats
    bullets: list[str] = []
    for i, line in enumerate(lines, start=1):
        move = chess.Move.from_uci(line.move_uci)
        move_san = board.san(move)

        idea = _simple_move_idea(board, move)
        pv_san = _uci_line_to_san(board, line.pv_uci, max_moves=6)
        pv_text = " ".join(pv_san)

        bullets.append(
            f"{i}. **{move_san}** ({_score_summary(line)}) — {idea}. "
            f"Variante principale : {pv_text}"
        )

    # 3) Mini-conseil (V1)
    tip = (
        "Conseil : essaie de comprendre l’idée (sécurité du roi / centre / activité des pièces) "
        "plutôt que de mémoriser seulement le coup."
    )

    return "\n".join([header, "", "Coups candidats :", *bullets, "", tip])
