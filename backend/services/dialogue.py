import os
import anthropic
from backend.services.session import SessionState

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    return _client


MAX_HINTS = int(os.environ.get("MAX_HINTS", "5"))
MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-20250514")

SESSION_COMPLETE_TAG = "<!--SESSION_COMPLETE-->"

# Anthropic Messages API requires the first message to be role "user", not "assistant".
SEED_USER_MESSAGE = (
    "I ran my code in the editor and I'm looking at the output below. "
    "Please help me debug."
)


def build_initial_message(stderr: str, exit_code: int) -> str:
    """Deterministic first message — no API call needed."""
    if exit_code == 0 and not stderr:
        return (
            "Your code ran without errors! "
            "What output did you expect vs. what did you get?"
        )
    return "What do you think this error message is telling you?"


def _shared_rules(hint_count: int) -> str:
    return f"""2. Ask only ONE question or make ONE focused statement per response.
3. Never reveal the bug directly until the final hint.
4. When the student edits and reruns code, ask them what changed and what the new output tells them.
5. On the final hint (when hint_count equals {MAX_HINTS - 1}), you MUST reveal the bug clearly and give the fix directly. Do NOT ask any questions in this message (no question marks). Give the answer and explanation as clear statements/instructions.
6. A correct explanation of the bug does NOT complete the task. Keep helping until the student has actually fixed their code (e.g. they changed the code and re-ran, or clearly describe the fix applied to the code and you judge it sufficient).
7. If the student fixes the bug themselves, congratulate them briefly and explain what the bug was — but only after the fix is real, not after they only diagnosed it.
8. Keep responses concise — one focused question or statement per turn.
9. When the session is truly complete (the student's code is fixed and behavior is correct, or equivalent), end your reply with a new line containing only: {SESSION_COMPLETE_TAG}
   Do not include that tag until the fix is confirmed; never use it when the student has only explained the bug without fixing the code."""


def _build_system_prompt(session: SessionState) -> str:
    analysis = session.bug_analysis
    category = analysis.category if analysis else "Unknown"
    line = f"line {analysis.line}" if (analysis and analysis.line) else "unknown line"
    error = session.error or "(no error — logic or output bug)"

    if session.error:
        rules = f"""Rules:
1. Always start by asking the student what they think the error message means.
{_shared_rules(session.hint_count)}
10. Guide the student toward the bug using the error message and the bug category below."""
    else:
        rules = f"""Rules:
1. There is no crash — the bug is likely logic or wrong output. Focus on expected vs actual output, tracing execution, and control flow (e.g. order of if/elif branches). Do not ask what "the error message means" as the primary question — there may be no stderr.
{_shared_rules(session.hint_count)}
10. Guide the student using the bug category and code below; relate hints to concrete outputs or values."""

    return f"""You are a Socratic debugging tutor. Your job is to help a student find and fix a bug in their code WITHOUT directly telling them what the bug is — until they have used all their hints.

{rules}

Bug context:
- Language: {session.language}
- Error message: {error}
- Bug category: {category}
- Bug location: {line}
- Code:
```
{session.code}
```"""


def _extract_assistant_text(response: object) -> str:
    """Collect text from all text blocks (handles multi-block assistant messages)."""
    parts: list[str] = []
    for block in getattr(response, "content", None) or ():
        text = getattr(block, "text", None)
        if text:
            parts.append(text)
    return "".join(parts).strip()


def _strip_session_complete(reply: str) -> tuple[str, bool]:
    if SESSION_COMPLETE_TAG not in reply:
        return reply, False
    cleaned = reply.replace(SESSION_COMPLETE_TAG, "").strip()
    return cleaned, True


def get_tutor_reply(session: SessionState, student_message: str) -> tuple[str, bool]:
    """
    Call Claude and return (reply_text, resolved).
    resolved=True when the reply includes SESSION_COMPLETE_TAG (student's code is done).
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

    reply = _extract_assistant_text(response)
    if not reply:
        raise ValueError("Assistant response had no text content")
    reply, tag_resolved = _strip_session_complete(reply)

    # Prior chat turn could have set session.resolved; combine with sentinel from this reply
    resolved = session.resolved or tag_resolved

    return reply, resolved
