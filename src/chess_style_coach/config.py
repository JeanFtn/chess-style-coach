from __future__ import annotations

import os
from pathlib import Path


def load_dotenv_if_present(path: str = ".env") -> None:
    """
    Charge un fichier .env minimal (sans dépendance externe).
    - Ignore les lignes vides et les commentaires (#)
    - Attend des lignes au format KEY=VALUE
    - Ne remplace pas les variables déjà définies dans l'environnement
    """
    env_path = Path(path)
    if not env_path.exists():
        return

    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


# On charge .env dès l'import du module config
load_dotenv_if_present()

STOCKFISH_PATH = os.environ.get("STOCKFISH_PATH", "")
DEFAULT_DEPTH = int(os.environ.get("STOCKFISH_DEPTH", "14"))
DEFAULT_MULTIPV = int(os.environ.get("STOCKFISH_MULTIPV", "3"))
DEFAULT_TIME = float(os.environ.get("STOCKFISH_TIME", "0"))  # 0 => on ignore le mode "time"

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")
OPENAI_MAX_TOKENS = int(os.environ.get("OPENAI_MAX_TOKENS", "600"))
OPENAI_TEMPERATURE = float(os.environ.get("OPENAI_TEMPERATURE", "0.6"))
