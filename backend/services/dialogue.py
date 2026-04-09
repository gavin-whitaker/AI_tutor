import os
import anthropic
from backend.services.session import SessionState
from backend.models.schemas import BugAnalysis

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    return _client


MAX_HINTS = int(os.environ.get("MAX_HINTS", "5"))
MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-20250514")


def build_initial_message(stderr: str, exit_code: int) -> str:
    """Deterministic first message — no API call needed."""
    if exit_code == 0 and not stderr:
        return (
            "Your code ran without errors! "
            "What output did you expect vs. what did you get?"
        )
    return "What do you think this error message is telling you?"


def _build_system_prompt(session: SessionState) -> str:
    analysis = session.bug_analysis
    category = analysis.category if analysis else "Unknown"
    line = f"line {analysis.line}" if (analysis and analysis.line) else "unknown line"
    error = session.error or "(no error — logic bug)"

    return f"""You are a Socratic debugging tutor. Your job is to help a student find and fix a bug in their code WITHOUT directly telling them what the bug is — until they have used all their hints.

Rules:
1. Always start by asking the student what they think the error message means.
2. Ask only ONE question per response.
3. Never reveal the bug directly until hint_count reaches max_hints (currently {session.hint_count}/{MAX_HINTS}).
4. Guide the student toward the bug using the error message and the bug category below.
5. When the student edits and reruns code, ask them what changed and what the new output tells them.
6. On hint {MAX_HINTS} (when hint_count equals max_hints), reveal the bug clearly and explain why it happened and how to fix it.
7. If the student fixes the bug themselves, congratulate them warmly and briefly explain what the bug was.
8. Keep responses concise — one focused question or statement per turn.

Bug context:
- Language: {session.language}
- Error message: {error}
- Bug category: {category}
- Bug location: {line}
- Code:
```
{session.code}
```"""


def get_tutor_reply(session: SessionState, student_message: str) -> tuple[str, bool]:
    """
    Call Claude and return (reply_text, resolved).
    resolved=True if Claude's response indicates the bug is fixed.
    """
    client = _get_client()
    system_prompt = _build_system_prompt(session)

    messages = list(session.conversation_history)
    messages.append({"role": "user", "content": student_message})

    response = client.messages.create(
        model=MODEL,
        max_tokens=512,
        system=system_prompt,
        messages=messages,
    )

    reply = response.content[0].text.strip()

    # Detect resolution: session already marked resolved by executor (exit_code==0)
    # but also check if Claude's reply contains congratulatory signals
    resolved = session.resolved
    if not resolved:
        lower = reply.lower()
        resolved = any(
            phrase in lower
            for phrase in [
                "great job", "well done", "you fixed it", "congratulations",
                "that's correct", "bug is fixed", "no more errors",
            ]
        )

    return reply, resolved
