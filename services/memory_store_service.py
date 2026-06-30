from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any


_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS memories (
  id TEXT PRIMARY KEY,
  session_id TEXT,
  content TEXT NOT NULL,
  tags TEXT,
  metadata TEXT,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_memories_session ON memories(session_id);
CREATE INDEX IF NOT EXISTS idx_memories_created ON memories(created_at);
"""


@dataclass(frozen=True)
class MemoryRow:
    id: str
    session_id: str | None
    content: str
    tags: list[str]
    metadata: dict[str, Any]
    created_at: str


def _connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path) -> None:
    with _connect(db_path) as conn:
        conn.executescript(_SCHEMA_SQL)


def insert_memories(db_path: Path, rows: list[MemoryRow]) -> None:
    init_db(db_path)
    with _connect(db_path) as conn:
        conn.executemany(
            """
            INSERT INTO memories (id, session_id, content, tags, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    row.id,
                    row.session_id,
                    row.content,
                    json.dumps(row.tags),
                    json.dumps(row.metadata),
                    row.created_at,
                )
                for row in rows
            ],
        )
        conn.commit()


def _row_to_memory(row: sqlite3.Row) -> MemoryRow:
    tags_raw = row["tags"]
    metadata_raw = row["metadata"]
    tags = json.loads(tags_raw) if tags_raw else []
    metadata = json.loads(metadata_raw) if metadata_raw else {}
    if not isinstance(tags, list):
        tags = []
    if not isinstance(metadata, dict):
        metadata = {}
    return MemoryRow(
        id=str(row["id"]),
        session_id=row["session_id"],
        content=str(row["content"]),
        tags=[str(tag) for tag in tags],
        metadata=metadata,
        created_at=str(row["created_at"]),
    )


def fetch_candidates(
    db_path: Path,
    *,
    session_id: str | None = None,
    limit: int | None = None,
) -> list[MemoryRow]:
    init_db(db_path)
    query = "SELECT id, session_id, content, tags, metadata, created_at FROM memories"
    params: list[Any] = []
    if session_id is not None:
        query += " WHERE session_id = ?"
        params.append(session_id)
    query += " ORDER BY created_at DESC"
    if limit is not None:
        query += " LIMIT ?"
        params.append(int(limit))
    with _connect(db_path) as conn:
        rows = conn.execute(query, params).fetchall()
    return [_row_to_memory(row) for row in rows]


def session_exists(db_path: Path, session_id: str) -> bool:
    init_db(db_path)
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT 1 FROM memories WHERE session_id = ? LIMIT 1",
            (session_id,),
        ).fetchone()
    return row is not None
