# Zelash

Zelash is an autonomous project synthesis framework. A user enters a plain-language goal, Zelash runs a staged build pipeline, records checkpoints and logs, tests the generated application, and returns a live local URL.

## What Works Now

- FastAPI backend with build endpoints:
  - `POST /api/build`
  - `GET /api/build/{id}/status`
  - `GET /api/build/{id}/logs`
  - `GET /api/build/{id}/logs?stream=true`
  - `POST /api/build/{id}/retry`
  - `GET /api/builds`
  - `GET /api/build/{id}/result`
- Checkpointed pipeline stages:
  Requirements Gathering, Architecture Planning, Backend Generation, Middleware Generation, Frontend Generation, Integration, Testing, Debugging, Deployment.
- Local deployment fallback using a generated static app and `file://` URL.
- Provider layer for Gemini, OpenAI, Anthropic, and AWS Bedrock with clear missing-key errors and basic retry handling.
- Specialized agents for backend, frontend, middleware, design, research, analysis, and writing.
- Next.js/TypeScript/Tailwind frontend in `web_ui`.

## Install

Python 3.11+ is recommended.

```bash
python -m venv venv_312
source venv_312/bin/activate
pip install -r requirements.txt
playwright install chromium
cp .env.example .env
```

Then edit `.env` and set `LLM_PROVIDER` plus the matching API key.

For the frontend:

```bash
cd web_ui
npm install
```

## Run

Start the API:

```bash
python -m src.main --mode api --port 8000
```

Start the frontend:

```bash
cd web_ui
npm run dev
```

Open `http://localhost:3000`, enter a goal, and watch the live build timeline and logs.

## Configuration

Important `.env` variables:

- `LLM_PROVIDER`: `gemini`, `openai`, `anthropic`, or `bedrock`
- `GEMINI_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, or AWS credentials
- `AUTOMATION_WORKSPACE`: generated build state and artifacts
- `BROWSER_HEADLESS`, `BROWSER_TIMEOUT`: Playwright behavior
- `NEXT_PUBLIC_API_BASE_URL`: backend URL for the frontend

See `.env.example` for the complete list.

## Frontend

The mission-control UI includes:

- Home page with goal input and example prompts
- Live build page with animated stage timeline and streamed logs
- Results page with live URL, tech stack, files, stage timings, and preview actions
- History page for previous builds
- Settings page for provider/deployment preferences

## Testing

```bash
pytest tests/test_build_api.py tests/test_integration.py -q
cd web_ui && npm run build && npm audit --omit=dev
```

Current verification:

- Backend build API smoke/integration tests pass.
- Frontend production build passes.
- Frontend production dependency audit reports zero vulnerabilities.

## Repository Notes

- `AUDIT.md` records the initial broken state and fixes targeted in this pass.
- `integrations/browser-use` and `integrations/mcp-browser-use` are vendored integration trees with their own optional dependencies and live-network tests. They are not part of the default core test command.
