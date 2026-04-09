from fastapi import APIRouter, HTTPException
from backend.models.schemas import RunRequest, RunResponse
from backend.services import executor, analyzer, dialogue, session as session_store

router = APIRouter()


@router.post("/run", response_model=RunResponse)
def run_code(req: RunRequest):
    if req.language not in ("python", "java"):
        raise HTTPException(status_code=400, detail="language must be 'python' or 'java'")

    result = executor.run_code(req.language, req.code)

    bug = None
    if result.exit_code != 0 or result.stderr:
        bug = analyzer.analyze(req.language, req.code, result.stderr)

    sess = session_store.create_or_reset_session(req.session_id)
    sess.language = req.language
    sess.code = req.code
    sess.error = result.stderr
    sess.bug_analysis = bug
    sess.hint_count = 0
    sess.resolved = result.exit_code == 0 and not result.stderr

    initial_msg = dialogue.build_initial_message(result.stderr, result.exit_code)
    sess.conversation_history = [{"role": "assistant", "content": initial_msg}]
    session_store.update_session(sess)

    return RunResponse(
        stdout=result.stdout,
        stderr=result.stderr,
        exit_code=result.exit_code,
        bug_analysis=bug,
        tutor_message=initial_msg,
    )
