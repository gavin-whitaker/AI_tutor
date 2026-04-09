# Socratic Debugging Tutor

A web-based intelligent tutoring system that guides students through debugging their own code using Socratic dialogue. Instead of revealing bugs directly, the system asks targeted questions — starting from the error message itself — to teach students how to reason about and fix their own code.

## Features

- Python and Java support
- Monaco code editor with syntax highlighting
- Docker-sandboxed code execution (no network, limited CPU/memory)
- Anthropic Claude-powered Socratic dialogue
- 5-hint limit with automatic answer reveal
- In-memory sessions (no login required)

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) running
- An Anthropic API key

## Setup

1. **Clone the repo** (if you haven't already):
   ```bash
   git clone <repo-url>
   cd cs-5620-project
   ```

2. **Add your API key** to `backend/.env`:
   ```bash
   cp backend/.env.example backend/.env
   # Edit backend/.env and set ANTHROPIC_API_KEY=your_key_here
   ```

3. **Start everything** with Docker Compose:
   ```bash
   docker-compose up --build
   ```

4. Open **http://localhost:3000** in your browser.

## Usage

1. Select a language (Python or Java)
2. Write or paste buggy code in the editor
3. Click **Run Code**
4. The tutor will ask you what you think the error means
5. Respond in the chat — the tutor guides you with up to 5 Socratic questions
6. Edit your code and re-run at any time
7. After 5 hints, the answer is revealed

### Java note

Java code must have a `public class Main` with a `main` method:
```java
public class Main {
    public static void main(String[] args) {
        // your code here
    }
}
```

## Architecture

```
Browser → Frontend (React + Monaco, :3000)
             ↓  POST /run  ↓  POST /chat
         Backend (FastAPI, :8000)
             ↓ executor.py → docker run python-sandbox / java-sandbox
             ↓ analyzer.py → classify bug
             ↓ dialogue.py → Claude API
```

## Development

To run services separately (without Docker):

**Backend:**
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env  # fill in your key
uvicorn backend.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

Note: When running without Docker, code execution won't be sandboxed. The executor will still try to call `docker run` — make sure Docker is running and the sandbox images are built:
```bash
docker build -t python-sandbox -f docker/Dockerfile.python docker/
docker build -t java-sandbox -f docker/Dockerfile.java docker/
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | required | Anthropic API key |
| `MAX_HINTS` | `5` | Max Socratic hints before revealing answer |
| `CODE_TIMEOUT_SECONDS` | `10` | Sandbox execution timeout |
| `SESSION_EXPIRY_MINUTES` | `120` | Idle session TTL |
| `CLAUDE_MODEL` | `claude-sonnet-4-20250514` | Claude model ID |
