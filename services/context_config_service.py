from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONTEXT_CONFIG_PATH = PROJECT_ROOT / "configs" / "context_config.json"

DEFAULT_CONTEXT_CONFIG: dict[str, Any] = {
    "memory_db_path": "data/memories.db",
    "recall_top_k": 10,
    "recall_max_tokens": 2000,
    "encoding_name": "o200k_base",
}

_INT_FIELDS = {"recall_top_k", "recall_max_tokens"}
_STR_FIELDS = {"memory_db_path", "encoding_name"}


def _coerce_config(raw: dict[str, Any]) -> dict[str, Any]:
    config = dict(DEFAULT_CONTEXT_CONFIG)
    config.update(raw)
    for key in _INT_FIELDS:
        config[key] = int(config[key])
    for key in _STR_FIELDS:
        config[key] = str(config[key])
    return config


def resolve_memory_db_path(config: dict[str, Any] | None = None) -> Path:
    config = load_context_config() if config is None else config
    env_path = os.environ.get("TINYCONTEXT_MEMORY_DB_PATH", "").strip()
    if env_path:
        path = Path(env_path)
    else:
        path = Path(str(config["memory_db_path"]))
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path


def load_context_config(path: str | Path | None = None) -> dict[str, Any]:
    raw_path = path if path is not None else os.environ.get("TINYCONTEXT_CONFIG_PATH")
    config_path = Path(raw_path) if raw_path else DEFAULT_CONTEXT_CONFIG_PATH
    if not config_path.is_absolute():
        config_path = PROJECT_ROOT / config_path
    if not config_path.exists():
        return dict(DEFAULT_CONTEXT_CONFIG)
    raw = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"context config must be a JSON object: {config_path}")
    return _coerce_config(raw)


def context_tokenizer_name(config: dict[str, Any] | None = None) -> str:
    config = load_context_config() if config is None else config
    return str(config["encoding_name"])
