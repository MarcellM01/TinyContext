from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from pipelines.memory_recall import memory_recall_run
from services.context_config_service import (
    context_tokenizer_name,
    load_context_config,
    resolve_memory_db_path,
)
from services.memory_store_service import MemoryRow, insert_memories
from services.token_counter_service import token_count


class MemoryError(Exception):
    pass


class EmptyMemoryError(MemoryError):
    pass


class SessionNotFoundError(MemoryError):
    pass


class RecallBudgetError(MemoryError):
    pass


MEMORY_ERROR_MAP: dict[type[Exception], tuple[str, int]] = {
    EmptyMemoryError: ("empty_memory", 400),
    SessionNotFoundError: ("session_not_found", 404),
    RecallBudgetError: ("recall_budget", 400),
}


@dataclass(frozen=True)
class MemoryInput:
    content: str
    tags: list[str] | None = None
    metadata: dict[str, Any] | None = None


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def save_memories(
    memories: list[MemoryInput],
    *,
    session_id: str | None = None,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not memories:
        raise EmptyMemoryError("memories must not be empty")
    config = load_context_config() if config is None else config
    db_path = resolve_memory_db_path(config)
    encoding_name = context_tokenizer_name(config)
    rows: list[MemoryRow] = []
    saved: list[dict[str, Any]] = []
    for item in memories:
        content = item.content.strip()
        if not content:
            raise EmptyMemoryError("memory content must not be empty")
        memory_id = str(uuid.uuid4())
        created_at = _utc_now_iso()
        tags = list(item.tags or [])
        metadata = dict(item.metadata or {})
        rows.append(
            MemoryRow(
                id=memory_id,
                session_id=session_id,
                content=content,
                tags=tags,
                metadata=metadata,
                created_at=created_at,
            )
        )
        saved.append(
            {
                "id": memory_id,
                "session_id": session_id,
                "content_tokens": token_count(content, encoding_name),
                "created_at": created_at,
            }
        )
    insert_memories(db_path, rows)
    return {"saved": saved}


def recall_memories(
    query: str,
    *,
    session_id: str | None = None,
    max_tokens: int | None = None,
    top_k: int | None = None,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    query = query.strip()
    if not query:
        raise EmptyMemoryError("query must not be empty")
    config = load_context_config() if config is None else config
    if max_tokens is not None and max_tokens < 1:
        raise RecallBudgetError("max_tokens must be at least 1")
    if top_k is not None and top_k < 1:
        raise RecallBudgetError("top_k must be at least 1")
    return memory_recall_run(
        query=query,
        session_id=session_id,
        max_tokens=max_tokens or int(config["recall_max_tokens"]),
        top_k=top_k or int(config["recall_top_k"]),
        config=config,
    )
