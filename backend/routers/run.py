from fastapi import APIRouter, HTTPException
from backend.models.schemas import RunRequest, RunResponse
from backend.services import executor, analyzer, dialogue, session as session_store

router = APIRouter()


def _apply_run_result(sess, language: str, code: str, stderr: str, bug) -> None:
    sess.language = language
    sess.code = code
    sess.error = stderr
    sess.bug_analysis = bug
    sess.resolved = False


@router.post("/run", response_model=RunResponse)
def run_code(req: RunRequest):
    if req.language not in ("python", "java"):
        raise HTTPException(status_code=400, detail="language must be 'python' or 'java'")

    result = executor.run_code(req.language, req.code)

    bug = None
    if result.exit_code != 0 or result.stderr:
        bug = analyzer.analyze(req.language, req.code, result.stderr)

    initial_msg = dialogue.build_initial_message(result.stderr, result.exit_code)
    seed = [
        {"role": "user", "content": dialogue.SEED_USER_MESSAGE},
        {"role": "assistant", "content": initial_msg},
    ]

    existing = session_store.get_session(req.session_id)
    if req.keep_chat and existing is not None:
        _apply_run_result(existing, req.language, req.code, result.stderr, bug)
        session_store.update_session(existing)
        return RunResponse(
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.exit_code,
            bug_analysis=bug,
            tutor_message="",
            conversation_reset=False,
        )

    sess = session_store.create_or_reset_session(req.session_id)
    _apply_run_result(sess, req.language, req.code, result.stderr, bug)
    sess.hint_count = 0
    sess.conversation_history = seed
    session_store.update_session(sess)

    return RunResponse(
        stdout=result.stdout,
        stderr=result.stderr,
        exit_code=result.exit_code,
        bug_analysis=bug,
        tutor_message=initial_msg,
        conversation_reset=True,
    )
