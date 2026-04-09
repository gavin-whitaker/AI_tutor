import time
import asyncio
from dataclasses import dataclass, field
from typing import Optional
from backend.models.schemas import BugAnalysis

_sessions: dict[str, "SessionState"] = {}


@dataclass
class SessionState:
    session_id: str
    language: str = ""
    code: str = ""
    error: str = ""
    bug_analysis: Optional[BugAnalysis] = None
    conversation_history: list[dict] = field(default_factory=list)
    hint_count: int = 0
    resolved: bool = False
    last_active: float = field(default_factory=time.time)

    def touch(self):
        self.last_active = time.time()


def get_session(session_id: str) -> Optional[SessionState]:
    session = _sessions.get(session_id)
    if session:
        session.touch()
    return session


def create_or_reset_session(session_id: str) -> SessionState:
    session = SessionState(session_id=session_id)
    _sessions[session_id] = session
    return session


def update_session(session: SessionState) -> None:
    session.touch()
    _sessions[session.session_id] = session


async def _cleanup_loop(expiry_minutes: int):
    while True:
        await asyncio.sleep(300)  # check every 5 minutes
        cutoff = time.time() - expiry_minutes * 60
        expired = [sid for sid, s in _sessions.items() if s.last_active < cutoff]
        for sid in expired:
            del _sessions[sid]


def start_cleanup_task(expiry_minutes: int):
    asyncio.create_task(_cleanup_loop(expiry_minutes))
