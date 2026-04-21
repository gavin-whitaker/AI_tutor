import logging

import anthropic
from fastapi import APIRouter, HTTPException
from backend.models.schemas import ChatRequest, ChatResponse
from backend.services import dialogue, session as session_store

logger = logging.getLogger(__name__)

router = APIRouter()
MAX_HINTS = dialogue.MAX_HINTS


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    sess = session_store.get_session(req.session_id)
    if sess is None:
        raise HTTPException(
            status_code=404,
            detail="Session not found. Please run your code first.",
        )

    if sess.resolved:
        return ChatResponse(
            reply="You've already solved this one! Run new code to start a fresh session.",
            hint_count=sess.hint_count,
            max_hints=MAX_HINTS,
            resolved=True,
        )

    if sess.hint_count >= MAX_HINTS:
        return ChatResponse(
            reply="You've used all your hints. The answer has already been revealed above.",
            hint_count=sess.hint_count,
            max_hints=MAX_HINTS,
            resolved=False,
        )

    try:
        reply, resolved = dialogue.get_tutor_reply(sess, req.message)
    except anthropic.NotFoundError:
        logger.exception("Claude model not found — check CLAUDE_MODEL in backend/.env")
        return ChatResponse(
            reply=(
                "The Claude model in CLAUDE_MODEL was not found (404). "
                "Update backend/.env to a valid model ID, e.g. claude-sonnet-4-20250514 "
                "or claude-haiku-4-5, then restart the backend. "
                "See backend/.env.example."
            ),
            hint_count=sess.hint_count,
            max_hints=MAX_HINTS,
            resolved=False,
        )
    except anthropic.AuthenticationError:
        logger.exception("Anthropic authentication failed")
        return ChatResponse(
            reply=(
                "Anthropic API authentication failed. Check ANTHROPIC_API_KEY in backend/.env "
                "and restart the backend."
            ),
            hint_count=sess.hint_count,
            max_hints=MAX_HINTS,
            resolved=False,
        )
    except Exception:
        logger.exception("get_tutor_reply failed")
        return ChatResponse(
            reply="I'm having trouble responding right now, please try again.",
            hint_count=sess.hint_count,
            max_hints=MAX_HINTS,
            resolved=False,
        )

    sess.hint_count += 1
    sess.conversation_history.append({"role": "user", "content": req.message})
    sess.conversation_history.append({"role": "assistant", "content": reply})
    if resolved:
        sess.resolved = True
    session_store.update_session(sess)

    return ChatResponse(
        reply=reply,
        hint_count=sess.hint_count,
        max_hints=MAX_HINTS,
        resolved=sess.resolved,
    )
