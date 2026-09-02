# Validation Strategy

> Reflects what's actually implemented as of Phase 7. Validates approved *artifacts* (Phase 6) — not tasks, requirements, or the live URL shortener directly.

## Model

`Validation`: id (`VALIDATION-*`), artifact_id, task_id, validation_type, command, status, output, error, duration_ms, metadata, created_at. Statuses: `PENDING`, `RUNNING`, `PASSED`, `FAILED`, `NOT_VALIDATED`. In practice only `PASSED`/`FAILED`/`NOT_VALIDATED` are ever persisted — the runner (`app/services/validation_runner.py`) is synchronous, so no row is ever written mid-flight in a transient state.

## Controlled execution

The API accepts only a `validation_type` from a fixed set — **never a raw command**. Each type maps to exactly one hardcoded command in `validation_runner.RUNNERS`:

| Type | Command actually run | What it checks |
|---|---|---|
| `UNIT_TEST` | `pytest -q` | The full backend test suite (this repo has no unit/integration marker split — see `INTEGRATION_TEST`) |
| `INTEGRATION_TEST` | `pytest -q` (same) | Documented, not fabricated as distinct — every test here already exercises the FastAPI app + a real DB via `TestClient` |
| `STATIC_ANALYSIS` | `ruff check .` | Lint |
| `API_CONTRACT` | `app.openapi()` structural check | Required top-level keys, every path has ≥1 operation, every operation has `responses` |
| `BUILD` | `python -c "import app.main"` | Backend imports/boots cleanly — **not** a frontend bundle build |
| `SECURITY` | static heuristic scan of `backend/**/*.py` (excl. `tests/`) | A small set of hardcoded-secret regex patterns (AWS keys, OpenAI-style keys, PEM blocks) — **not** a dependency CVE scan (no network access to a vulnerability DB here) and **not** comprehensive |
| `PERFORMANCE` | none | Always `NOT_VALIDATED` at this generic level — a artifact has no running endpoint to load-test; see `app/services/performance_probe.py` (Phase 8K) for the utility used against real live endpoints |

## Evidence

Every response includes a short `evidence` line (e.g. the last line of pytest/ruff output) distinct from the full `output`. `NOT_VALIDATED` always carries a stated `error` reason — never silently blank.

## Known limitations

- No dependency vulnerability scanning (no network access to a CVE database in this environment).
- `SECURITY` is a narrow heuristic, not an audit.
- `PERFORMANCE` requires a concrete live endpoint and isn't wired to a generic artifact.
- No background job queue — validations run synchronously and block the request for their duration (pytest can take ~1s in this repo; a much larger suite would need this reconsidered).
