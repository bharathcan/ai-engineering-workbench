# Backend

FastAPI backend for the AI Engineering Workbench. As of Phase 4, it implements the Requirement Analyzer (Phase 3) and Task Decomposition (Phase 4) end-to-end. AI-assisted code generation, artifact management, the validation engine, and the URL shortener itself are not implemented yet — see [../ARCHITECTURE.md](../ARCHITECTURE.md) and [../docs/REQUIREMENTS.md](../docs/REQUIREMENTS.md) for the full intended scope.

## Setup

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Python 3.12 is used for this venv (not the system Python — see the Phase 2 engineering decisions in [AI_USAGE.md](../AI_USAGE.md)). Any Python 3.10+ interpreter should work since the codebase uses modern union type syntax (`str | None`).

## Run

```bash
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The application starts with no environment variables set and no external database service running — a local SQLite file (`workbench.db`, gitignored) is created automatically on startup. Requirement creation and retrieval work immediately; `/analyze` additionally needs `AI_PROVIDER`/`AI_API_KEY` configured (see Configuration below), and returns a clean `503` rather than failing silently if they're missing.

* Health check: [http://localhost:8000/health](http://localhost:8000/health)
* OpenAPI docs: [http://localhost:8000/docs](http://localhost:8000/docs)
* Requirement + Task API: see [../docs/api-design.md](../docs/api-design.md)

## Configuration

Configuration is read from environment variables (see [../.env.example](../.env.example)), all optional with safe defaults:

```text
APP_ENV=development
APP_HOST=0.0.0.0
APP_PORT=8000
DATABASE_URL=
REDIS_URL=
AI_PROVIDER=
AI_API_KEY=
AI_MODEL=
```

`DATABASE_URL` defaults to a local SQLite file when unset. Setting it to a `postgresql+psycopg://` URL switches to PostgreSQL (the proposed production database — see [../ARCHITECTURE.md](../ARCHITECTURE.md) Persistence) with no code change. `REDIS_URL` is still unused (no caching implemented yet). To enable `/analyze`, set `AI_PROVIDER=anthropic` and `AI_API_KEY=<your key>`; `AI_MODEL` defaults to `claude-sonnet-5` if unset.

## Tests

```bash
source .venv/bin/activate
pytest -v
```

Tests never call a real AI provider — see `tests/support/fake_ai_provider.py` and `tests/conftest.py` (which also isolates the test database from your local `workbench.db`). 44 tests cover the Requirement Analyzer, Task Decomposer (including dependency-graph validation — self/missing/circular dependencies, unknown requirement refs), and the full plan-generation/review-decision API.

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
│   └── routes/         # health.py, requirements.py, tasks.py
├── core/
│   ├── config.py        # Settings (env-var configuration)
│   ├── database.py      # SQLAlchemy engine/session, Base, get_db
│   └── exceptions.py     # Domain exceptions (RequirementNotFoundError, AIProviderError, ...)
├── models/            # SQLAlchemy ORM models: Requirement, RequirementAnalysis,
│                      #   EngineeringPlan, EngineeringTask, EngineerDecision
├── schemas/           # Pydantic schemas — API request/response and the two AI
│                      #   structured-output contracts (analysis, task decomposition)
├── services/           # requirement_service.py, requirement_analyzer.py,
│                      #   engineering_plan_service.py, task_decomposer.py
├── repositories/       # requirement_repository.py, engineering_plan_repository.py
│                      #   — the only DB-query layer
├── ai/                # AIProvider abstraction, AnthropicProvider, factory, prompts
├── validation/         # Reserved for the validation engine (not yet implemented)
└── utils/             # Reserved for shared utilities (not yet implemented)
```

`validation/` and `utils/` still contain only `__init__.py` — no validation engine or shared utilities exist yet.
