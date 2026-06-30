from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from services.context_config_service import (
    DEFAULT_CONTEXT_CONFIG,
    load_context_config,
    resolve_memory_db_path,
)


class ContextConfigServiceTests(unittest.TestCase):
    def test_load_defaults_when_missing_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "missing.json"
            config = load_context_config(missing)
            self.assertEqual(config, DEFAULT_CONTEXT_CONFIG)

    def test_load_overrides_from_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "context.json"
            path.write_text(
                json.dumps(
                    {
                        "recall_top_k": 5,
                        "recall_max_tokens": 500,
                    }
                ),
                encoding="utf-8",
            )
            config = load_context_config(path)
            self.assertEqual(config["recall_top_k"], 5)
            self.assertEqual(config["recall_max_tokens"], 500)

    def test_memory_db_path_env_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "custom.db"
            previous = os.environ.get("TINYCONTEXT_MEMORY_DB_PATH")
            os.environ["TINYCONTEXT_MEMORY_DB_PATH"] = str(db_path)
            try:
                resolved = resolve_memory_db_path()
            finally:
                if previous is None:
                    os.environ.pop("TINYCONTEXT_MEMORY_DB_PATH", None)
                else:
                    os.environ["TINYCONTEXT_MEMORY_DB_PATH"] = previous
            self.assertEqual(resolved, db_path)
