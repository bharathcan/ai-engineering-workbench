# Backend

FastAPI backend for the AI Engineering Workbench. Implements the full pipeline: Requirement Analyzer, Task Decomposer, AI-assisted task execution, Artifact Generator, and the Validation Engine — plus the mandatory URL shortener use case built through that same pipeline. See [../README.md](../README.md) and [../ARCHITECTURE.md](../ARCHITECTURE.md) for the full system picture; this file covers backend-specific setup and structure.

## Setup

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Python 3.12+ works; 3.13 is also verified. Python 3.14 currently has no compatible `pydantic-core` wheel at the pinned dependency version.

## Run

```bash
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Starts with no environment variables set and no external database service running — a local SQLite file (`workbench.db`, gitignored) is created automatically on startup. Requirement creation and retrieval work immediately; `/analyze` and AI-assist endpoints additionally need `AI_PROVIDER`/`AI_API_KEY` configured (see Configuration below), and return a clean `503` rather than failing silently if missing.

* Health check: [http://localhost:8000/health](http://localhost:8000/health)
* OpenAPI docs: [http://localhost:8000/docs](http://localhost:8000/docs)

## Configuration

Read from environment variables (see [../.env.example](../.env.example)), all optional with safe defaults:

```text
APP_ENV=development
APP_HOST=0.0.0.0
APP_PORT=8000
DATABASE_URL=
REDIS_URL=
CORS_ORIGINS=
AI_PROVIDER=
AI_API_KEY=
AI_MODEL=
```

* `DATABASE_URL` defaults to local SQLite when unset. A `postgresql+psycopg://` URL switches to PostgreSQL with no code change — this is what runs in production on Render.
* `REDIS_URL` is unused — no caching is implemented yet.
* To enable `/analyze` and AI-assist, set `AI_PROVIDER=anthropic` and `AI_API_KEY=<your key>`; `AI_MODEL` defaults to `claude-sonnet-5` if unset.

## Tests

```bash
source .venv/bin/activate
pytest -v
```

188 tests. Tests never call a real AI provider — see `tests/support/fake_ai_provider.py` and `tests/conftest.py` (which also isolates the test database from your local `workbench.db`). Coverage spans the Requirement Analyzer, Task Decomposer (dependency-graph validation — self/missing/circular dependencies), AI-assist and artifact generation, the validation engine, the URL shortener, and `AnthropicProvider` itself (mocked-client tests covering the two defects found during live-API testing — see `tests/test_anthropic_provider.py`).

## Lint

```bash
source .venv/bin/activate
ruff check .
```

## Structure

```text
app/
├── main.py            # FastAPI app instance, middleware, startup (create tables), routers
├── api/
│   ├── deps.py         # Shared FastAPI dependencies (e.g. AI provider factory)
│   └── routes/         # health, requirements, tasks, ai_runs, artifacts, validations, urls
├── core/
│   ├── config.py        # Settings (env-var configuration)
│   ├── database.py      # SQLAlchemy engine/session, Base, get_db
│   └── exceptions.py     # Domain exceptions (RequirementNotFoundError, AIProviderError, ...)
├── models/            # SQLAlchemy ORM: Requirement, RequirementAnalysis, EngineeringPlan,
│                      #   EngineeringTask, EngineerDecision, AIRun, Artifact, Validation,
│                      #   ShortenedUrl, ClickEvent
├── schemas/           # Pydantic request/response schemas + AI structured-output contracts
│                      #   (analysis, task decomposition, AI recommendation, artifact generation)
├── services/           # One service per pipeline stage: requirement_analyzer, task_decomposer,
│                      #   task_assistant, artifact_generator, validation_runner (the allowlist)
│                      #   + validation_service, url_service, click_analytics, short_code, ...
├── repositories/       # The only DB-query layer — one repository per model family
├── ai/                # AIProvider abstraction, AnthropicProvider, factory, prompts
└── utils/             # safe_path.py — sandboxed artifact-write path validation
```

## Deployment

`Dockerfile` + `../render.yaml` define the live Render deployment (`workbench-backend`, Docker web service, backed by managed PostgreSQL `workbench-db`). See [../README.md](../README.md) §9 for the full deploy walkthrough.
