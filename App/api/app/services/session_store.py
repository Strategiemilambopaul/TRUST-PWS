"""Sessions d'évaluation upload (mémoire processus) pour export / nettoyage."""

from __future__ import annotations

from typing import Any

_SESSIONS: dict[str, dict[str, Any]] = {}


def save_session(evaluation_id: str, payload: dict[str, Any]) -> None:
    _SESSIONS[evaluation_id] = payload


def get_session(evaluation_id: str) -> dict[str, Any] | None:
    return _SESSIONS.get(evaluation_id)


def update_session(evaluation_id: str, **kwargs: Any) -> dict[str, Any] | None:
    session = _SESSIONS.get(evaluation_id)
    if not session:
        return None
    session.update(kwargs)
    return session
