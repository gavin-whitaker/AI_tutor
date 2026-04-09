from pydantic import BaseModel
from typing import Optional


class BugAnalysis(BaseModel):
    category: str
    line: Optional[int] = None
    description: str


class RunRequest(BaseModel):
    session_id: str
    language: str  # "python" or "java"
    code: str


class RunResponse(BaseModel):
    stdout: str
    stderr: str
    exit_code: int
    bug_analysis: Optional[BugAnalysis] = None
    tutor_message: str


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    reply: str
    hint_count: int
    max_hints: int
    resolved: bool
