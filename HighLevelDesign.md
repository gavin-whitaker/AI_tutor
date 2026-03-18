# Socratic Debugging Tutor — High Level Design
 
## Project Overview
 
A web-based intelligent tutoring system that guides students through debugging their own code using Socratic dialogue. Instead of revealing bugs directly, the system asks targeted questions — starting from the error message itself — to teach students how to reason about and fix their own code. The system supports **Python** and **Java**, runs code in a sandbox to capture real errors, and limits hints to 5 before revealing the answer.
 
---
 
## Goals
 
- Teach students to read and interpret error messages
- Guide students to find and fix bugs through self-directed reasoning
- Support Python and Java codebases
- Keep sessions stateless (no login, no database)
 
---
 
## Tech Stack
 
| Layer | Technology |
|---|---|
| Frontend | React + Monaco Editor |
| Backend | FastAPI (Python 3.11+) |
| Code Execution | Docker sandbox (isolated subprocess per run) |
| Static Analysis (Python) | `pylint`, `ast` (stdlib) |
| Static Analysis (Java) | `javac` compiler stderr output |
| LLM | Anthropic Claude API (`claude-sonnet-4-20250514`) |
| Session State | In-memory (Python dict keyed by session ID) |
| Styling | Tailwind CSS |
 
---
 
## Repository Structure
 
```
socratic-debugger/
├── backend/
│   ├── main.py                  # FastAPI app entrypoint
│   ├── routers/
│   │   ├── run.py               # POST /run — executes code, returns error
│   │   └── chat.py              # POST /chat — sends message, returns tutor reply
│   ├── services/
│   │   ├── executor.py          # Sandbox code execution (Python + Java)
│   │   ├── analyzer.py          # Static analysis + bug classification
│   │   ├── dialogue.py          # LLM prompt construction + hint tracking
│   │   └── session.py           # In-memory session store
│   ├── models/
│   │   └── schemas.py           # Pydantic request/response models
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # Root component
│   │   ├── components/
│   │   │   ├── CodePanel.jsx    # Monaco editor + language selector + Run button
│   │   │   ├── ChatPanel.jsx    # Messaging-style dialogue UI
│   │   │   └── ErrorDisplay.jsx # Shows raw error output below editor
│   │   ├── hooks/
│   │   │   └── useSession.js    # Manages session ID + API calls
│   │   └── api/
│   │       └── client.js        # Axios API client
│   ├── package.json
│   └── tailwind.config.js
├── docker/
│   ├── Dockerfile.python        # Python sandbox image
│   ├── Dockerfile.java          # Java sandbox image
│   └── docker-compose.yml       # Orchestrates frontend + backend + sandboxes
└── README.md
```
 
---
 
## UI Layout
 
```
┌─────────────────────────────┬──────────────────────────────┐
│        LEFT PANEL           │        RIGHT PANEL           │
│                             │                              │
│  [ Python ] [ Java ]        │   Tutor: What do you think   │
│                             │   this error is telling you? │
│  ┌─────────────────────┐    │                              │
│  │  Monaco Code Editor  │    │   Student: I think it's a   │
│  │  (syntax highlight)  │    │   variable not defined?      │
│  │                      │    │                              │
│  └─────────────────────┘    │   Tutor: Good. Where in the  │
│                             │   code is that variable first │
│  [ ▶ Run Code ]             │   referenced?                │
│                             │                              │
│  ── Error Output ──         │   [ Type a message...  ] [→] │
│  NameError: name 'x' is     │                              │
│  not defined on line 4      │                              │
└─────────────────────────────┴──────────────────────────────┘
```
 
---
 
## Core User Flow
 
1. Student pastes or writes buggy code in the Monaco editor
2. Student selects language (Python or Java checkbox)
3. Student clicks **Run Code**
4. Backend executes code in sandbox, captures stdout/stderr
5. Error output is displayed below the editor
6. Tutor opens dialogue: *"What do you think this error is telling you?"*
7. Student responds in the chat panel
8. Tutor asks follow-up Socratic questions (max 5 hints)
9. Student edits code mid-conversation and re-runs at any time
10. On re-run, tutor asks: *"What changed? What does the new output tell you?"*
11. If bug is fixed → tutor congratulates, session ends
12. If hint limit (5) is reached → tutor reveals the answer with a full explanation
 
---
 
## Backend API
 
### `POST /run`
Executes the student's code and returns the output/error.
 
**Request:**
```json
{
  "session_id": "abc123",
  "language": "python",
  "code": "x = 1\nprint(y)"
}
```
 
**Response:**
```json
{
  "stdout": "",
  "stderr": "NameError: name 'y' is not defined on line 2",
  "exit_code": 1,
  "bug_analysis": {
    "category": "NameError",
    "line": 2,
    "description": "Undefined variable referenced"
  }
}
```
 
---
 
### `POST /chat`
Sends a student message and returns the tutor's next Socratic question.
 
**Request:**
```json
{
  "session_id": "abc123",
  "message": "I think the variable isn't defined?",
  "code": "x = 1\nprint(y)",
  "language": "python",
  "error": "NameError: name 'y' is not defined on line 2"
}
```
 
**Response:**
```json
{
  "reply": "Good observation. Where in your code do you first try to use that variable?",
  "hint_count": 1,
  "max_hints": 5,
  "resolved": false
}
```
 
---
 
## Services
 
### `executor.py` — Sandbox Code Execution
 
- Runs code inside a **Docker container** with no network access, limited CPU/memory, and a 10-second timeout
- Python: runs via `python3 -c` or writes to a temp file and executes
- Java: writes to a temp `.java` file, compiles with `javac`, then runs with `java`
- Captures both `stdout` and `stderr`
- Returns exit code so the system knows if execution succeeded or failed
 
```python
# Pseudocode
def run_code(language: str, code: str) -> ExecutionResult:
    if language == "python":
        result = subprocess.run(
            ["python3", "-"],
            input=code,
            capture_output=True,
            timeout=10,
            # run inside Docker sandbox
        )
    elif language == "java":
        # write to Main.java, compile, then run
        ...
    return ExecutionResult(stdout, stderr, exit_code)
```
 
---
 
### `analyzer.py` — Static Analysis + Bug Classification
 
Classifies the error into a structured category to guide the LLM.
 
**Python bug categories:**
| Category | Detection Method |
|---|---|
| `SyntaxError` | `ast.parse()` exception |
| `NameError` | pylint + runtime stderr |
| `TypeError` | pylint + runtime stderr |
| `IndexError` | pylint + runtime stderr |
| `LogicError` | pylint warnings (no exception thrown) |
| `IndentationError` | `ast.parse()` exception |
 
**Java bug categories:**
| Category | Detection Method |
|---|---|
| `CompileError` | `javac` stderr |
| `NullPointerException` | runtime stderr |
| `ArrayIndexOutOfBounds` | runtime stderr |
| `ClassCastException` | runtime stderr |
| `LogicError` | no exception, wrong output |
 
```python
def analyze(language: str, code: str, stderr: str) -> BugAnalysis:
    # Returns: { category, line_number, description }
```
 
---
 
### `dialogue.py` — LLM Prompt Construction
 
Builds the system prompt and message history for each LLM call.
 
**System prompt structure:**
```
You are a Socratic debugging tutor. Your job is to help a student find and fix a bug in their code WITHOUT directly telling them what the bug is — until they have used all their hints.
 
Rules:
1. Always start by asking the student what they think the error message means.
2. Ask only ONE question per response.
3. Never reveal the bug directly until hint {hint_count} reaches {max_hints} (currently {hint_count}/{max_hints}).
4. Guide the student toward the bug using the error message and the bug category below.
5. When the student edits and reruns code, ask them what changed and what the new output tells them.
6. On hint {max_hints}, reveal the bug clearly and explain why it happened and how to fix it.
7. If the student fixes the bug themselves, congratulate them warmly and briefly explain what the bug was.
 
Bug context:
- Language: {language}
- Error message: {error}
- Bug category: {bug_category}
- Bug location: line {line_number}
 
Conversation so far:
{conversation_history}
```
 
---
 
### `session.py` — In-Memory Session Store
 
```python
# Simple dict, no persistence needed
sessions: dict[str, SessionState] = {}
 
class SessionState:
    session_id: str
    language: str
    code: str
    error: str
    bug_analysis: BugAnalysis
    conversation_history: list[dict]  # [{role, content}, ...]
    hint_count: int
    resolved: bool
```
 
Sessions are created on first `/run` call and expire after 2 hours of inactivity (use a simple timestamp check).
 
---
 
## Frontend Components
 
### `CodePanel.jsx`
- Monaco Editor instance with language set dynamically based on checkbox
- Language selector: two checkboxes, only one active at a time (radio behavior)
- "Run Code" button — calls `POST /run`, updates error display, triggers first tutor message if session is new
- Error output displayed below editor in a fixed-height scrollable box
 
### `ChatPanel.jsx`
- Scrollable message list, student messages right-aligned, tutor messages left-aligned
- Input box at bottom with send button
- Hint counter displayed subtly: *"Hints used: 2 / 5"*
- When `resolved: true` is returned, input is disabled and a success banner is shown
- When `hint_count === max_hints`, the tutor message containing the answer is styled differently (e.g. slightly highlighted) so the student knows this is the reveal
 
### `useSession.js`
- Generates a `session_id` on page load (UUID)
- Stores current code, language, error, and chat history in React state
- Exposes `runCode()` and `sendMessage()` functions that call the API
 
---
 
## Environment Variables
 
```env
# backend/.env
ANTHROPIC_API_KEY=your_key_here
MAX_HINTS=5
CODE_TIMEOUT_SECONDS=10
SESSION_EXPIRY_MINUTES=120
```
 
---
 
## Docker Setup
 
```yaml
# docker-compose.yml
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    env_file: ./backend/.env
 
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
 
  python-sandbox:
    build: ./docker/Dockerfile.python
    network_mode: none        # no internet access
    mem_limit: 128m
    cpus: 0.5
 
  java-sandbox:
    build: ./docker/Dockerfile.java
    network_mode: none
    mem_limit: 256m
    cpus: 0.5
```
 
---
 
## Implementation Order (Recommended)
 
1. **Set up FastAPI backend** with `/run` and `/chat` stubs returning hardcoded responses
2. **Build frontend** with Monaco editor, language selector, error display, and chat panel connected to the stubs
3. **Implement Python sandbox execution** in `executor.py`
4. **Implement static analysis** for Python in `analyzer.py`
5. **Wire up LLM dialogue** in `dialogue.py` with the full system prompt
6. **Connect everything** — real `/run` and `/chat` responses flowing through the UI
7. **Add Java support** — executor + analyzer for Java
8. **Polish** — hint counter UI, session expiry, error handling, edge cases
 
---
 
## Edge Cases to Handle
 
| Scenario | Handling |
|---|---|
| Code runs successfully (no error) | Tutor says: "Your code ran without errors! What output did you expect vs. what did you get?" |
| Student submits empty code | Frontend validation — disable Run button if editor is empty |
| Code times out (infinite loop) | Sandbox kills process after 10s, return timeout error message |
| Student fixes bug on their own | `analyzer.py` detects no errors on re-run, tutor congratulates |
| LLM API failure | Return a fallback message: "I'm having trouble responding right now, please try again." |
| Session not found on `/chat` | Return 404, frontend prompts student to re-run their code first |
 
---
 
## Key Design Decisions
 
- **Error-message-first dialogue:** The tutor always opens by asking the student to interpret the error message. This teaches a generalizable real-world skill, not just how to fix one bug.
- **Rule-based + LLM hybrid:** Static analysis tells the LLM *where* the bug is and *what category* it falls into. This prevents the LLM from wandering or accidentally revealing the answer too early.
- **Real code execution:** Running actual code means errors are always accurate — no hallucinated or approximate feedback.
- **Stateless sessions:** No login or database needed. Sessions live in memory and expire after 2 hours. Keeps the project scope tight.
- **5 hint limit:** Creates a natural scaffolding curve. Students are incentivized to reason carefully rather than just spamming the chat for the answer.
