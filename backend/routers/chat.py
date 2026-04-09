from fastapi import APIRouter, HTTPException
from backend.models.schemas import ChatRequest, ChatResponse
from backend.services import dialogue, session as session_store

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
    except Exception:
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
