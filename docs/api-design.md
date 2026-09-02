# API Design

> **Status:** Reflects what is actually implemented as of Phase 7. Requirement Analyzer (Phase 3), Task Decomposition (Phase 4), task-level AI Assistance (Phase 5), controlled Artifact Generation (Phase 6), and the Validation Engine (Phase 7) endpoints are documented; nothing beyond that is implemented yet (see [REQUIREMENTS.md](REQUIREMENTS.md) and [../README.md](../README.md) for what's still ahead — no URL shortener). **AI never modifies the repository outside the sandboxed `generated/` workspace, executes anything, or applies its own output without an explicit engineer decision — see "No Automatic Code Execution" and "Controlled File Writes" further down.**

All endpoints are served by the FastAPI backend (see [../backend/README.md](../backend/README.md)). Interactive OpenAPI docs are always available at `/docs` when the backend is running.

## Base path

```text
/api/v1/requirements
```

The `/health` endpoint (Phase 2) has no prefix and is unchanged.

## POST /api/v1/requirements

Creates a requirement. Does not analyze it — analysis is a separate, explicit step (see FR-005/FR-006/FR-007 in [REQUIREMENTS.md](REQUIREMENTS.md): AI assists within a task, it does not run unsupervised the moment input arrives).

**Request body**

```json
{ "text": "Build a scalable URL shortener service with APIs, persistence, and analytics." }
```

`text` must be non-empty after trimming whitespace, and at most 10,000 characters.

**Response — `201 Created`**

```json
{
  "id": "REQ-001",
  "text": "Build a scalable URL shortener service with APIs, persistence, and analytics.",
  "status": "CREATED",
  "created_at": "2026-01-01T00:00:00+00:00",
  "latest_analysis": null
}
```

**Errors**

| Status | Cause |
|---|---|
| 422 | `text` missing, empty, whitespace-only, or over 10,000 characters |
| 500 | Persistence failure (no internal detail is returned to the client) |

## POST /api/v1/requirements/{requirement_id}/analyze

Runs the Requirement Analyzer against the stored requirement's text and persists the result. Can be called more than once; the requirement's `status` becomes `ANALYZED` and `GET` returns the most recent analysis.

**Response — `200 OK`** — a `RequirementResponse` (same shape as create) with `latest_analysis` populated:

```json
{
  "id": "REQ-001",
  "text": "Build a scalable URL shortener service with APIs, persistence, and analytics.",
  "status": "ANALYZED",
  "created_at": "2026-01-01T00:00:00+00:00",
  "latest_analysis": {
    "summary": "Build a URL shortener with APIs for creating and resolving short links, durable persistence, and usage analytics, with scalability considered in the design.",
    "functional_requirements": [
      { "id": "FR-001", "description": "Create shortened URL mappings." },
      { "id": "FR-002", "description": "Resolve short URLs to their destination." },
      { "id": "FR-003", "description": "Provide analytics on URL usage." }
    ],
    "non_functional_requirements": [
      { "id": "NFR-001", "description": "The architecture must consider scalability." }
    ],
    "ambiguities": [
      {
        "id": "AMB-001",
        "description": "Expected request volume is not specified.",
        "why_it_matters": "The scalability architecture depends on expected traffic.",
        "impact": "MEDIUM",
        "information_needed": "Expected average and peak requests per second."
      }
    ],
    "assumptions": [
      {
        "id": "ASM-001",
        "description": "URLs are assumed to be publicly accessible.",
        "reason": "The requirement does not specify authentication.",
        "impact": "Authentication requirements may change the API design."
      }
    ],
    "constraints": [],
    "success_criteria": [
      { "id": "SC-001", "description": "A submitted URL can be shortened and later resolved back to its destination." }
    ],
    "engineering_concerns": [
      { "id": "ENG-001", "description": "Short code collisions must be handled as usage grows." }
    ]
  }
}
```

(This example is the payload used in `backend/tests/support/analysis_payloads.py` — the exact response depends on the configured AI provider and is never guaranteed to be identical across calls.)

**Errors**

| Status | Cause |
|---|---|
| 404 | No requirement exists with that `requirement_id` |
| 503 | The AI provider call itself failed (unconfigured, timeout, network, rate limit, auth) |
| 502 | The AI provider responded, but its output failed schema validation — nothing is persisted |
| 500 | Persistence failure after a valid analysis was produced |

A failed analyze call never partially persists — the requirement's `status` stays `CREATED` and `latest_analysis` stays `null` until a call actually succeeds (see `backend/tests/test_requirements_api.py`, which asserts this for both the 503 and 502 cases).

## GET /api/v1/requirements/{requirement_id}

Retrieves a requirement and its most recent analysis, if any.

**Response — `200 OK`** — same `RequirementResponse` shape as above. `latest_analysis` is `null` if `analyze` has never been called (or never succeeded).

**Errors**

| Status | Cause |
|---|---|
| 404 | No requirement exists with that `requirement_id` |
| 500 | Persistence failure |

## POST /api/v1/requirements/{requirement_id}/tasks

Generates a draft engineering plan for the requirement's most recent analysis. Requires the requirement to have been analyzed first. Can be called more than once (e.g. after a re-analysis); `GET` always returns the most recent plan.

**Ambiguity gate:** if the analysis has any ambiguity with `impact: "HIGH"`, no AI call is made and no tasks are generated — a plan record is still created, with `status: "BLOCKED"` and a `blocked_reason` naming the offending ambiguity ids. `impact: "HIGH"` as the threshold for "material" is this codebase's own resolution of a term the phase instructions used but did not define — documented here rather than left implicit (see `app/services/engineering_plan_service.py::BLOCKING_AMBIGUITY_IMPACT`).

**Response — `201 Created`** — a `GENERATED` plan:

```json
{
  "id": "PLAN-001",
  "requirement_id": "REQ-001",
  "requirement_analysis_id": "ANALYSIS-001",
  "status": "GENERATED",
  "blocked_reason": null,
  "summary": "Implement the URL shortener's core flows: persistence schema, create/redirect APIs, and basic analytics capture.",
  "tasks": [
    {
      "id": "TASK-001",
      "plan_id": "PLAN-001",
      "title": "Define URL persistence schema",
      "description": "Design the database schema for storing short-code-to-destination-URL mappings.",
      "type": "DATABASE",
      "requirement_refs": ["FR-001", "FR-002"],
      "dependencies": [],
      "sequence": 1,
      "acceptance_criteria": [
        "Schema supports short code, destination URL, and creation timestamp.",
        "Schema reviewed by engineer."
      ],
      "ai_assistance_type": "DESIGN",
      "risks": [],
      "status": "REVIEW_REQUIRED",
      "review_status": "PENDING",
      "decisions": [],
      "created_at": "2026-01-01T00:00:00+00:00"
    }
  ],
  "assumptions": ["Tasks are grouped by API surface rather than by architectural layer."],
  "unresolved_ambiguities": ["AMB-001"],
  "risks": [
    { "id": "RISK-002", "description": "Expected traffic volume is unresolved (AMB-001)...", "impact": "MEDIUM" }
  ],
  "review_status": "DRAFT",
  "created_at": "2026-01-01T00:00:00+00:00"
}
```

A `BLOCKED` plan (e.g. for "Improve the analytics.") looks like:

```json
{
  "id": "PLAN-002",
  "requirement_id": "REQ-002",
  "requirement_analysis_id": "ANALYSIS-002",
  "status": "BLOCKED",
  "blocked_reason": "Material requirement ambiguities remain unresolved. Required engineer action: clarify AMB-001 before task generation. (An ambiguity is treated as material, and blocks planning, when its impact is HIGH.)",
  "summary": "",
  "tasks": [],
  "assumptions": [],
  "unresolved_ambiguities": ["AMB-001"],
  "risks": [],
  "review_status": "DRAFT",
  "created_at": "2026-01-01T00:00:00+00:00"
}
```

(Both examples come from `backend/tests/support/task_plan_payloads.py` and `backend/tests/support/analysis_payloads.py::AMBIGUOUS_ANALYTICS_ANALYSIS`.)

**Errors**

| Status | Cause |
|---|---|
| 404 | No requirement exists with that `requirement_id` |
| 409 | The requirement has not been analyzed yet |
| 503 | The AI provider call itself failed |
| 502 | The AI provider returned a plan that failed validation — schema (missing/extra/wrong-type fields, unsupported task type) or referential integrity (duplicate task id, self-dependency, dependency on an unknown task id, circular dependency, a `requirement_refs` id not present in the analysis, or a task's `sequence` not coming after its dependencies') — nothing is persisted |
| 500 | Persistence failure |

## GET /api/v1/requirements/{requirement_id}/tasks

Retrieves the requirement's most recent engineering plan (same shape as the `POST` response above, `GENERATED` or `BLOCKED`).

**Errors**

| Status | Cause |
|---|---|
| 404 | No requirement exists with that id, or no plan has been generated for it yet |
| 500 | Persistence failure |

## GET /api/v1/tasks/{task_id}

Retrieves a single task by its own id (not nested under a requirement).

**Response — `200 OK`** — a single task object, same shape as an entry in a plan's `tasks[]`.

**Errors**

| Status | Cause |
|---|---|
| 404 | No task exists with that `task_id` |
| 500 | Persistence failure |

## POST /api/v1/tasks/{task_id}/decision

Records an engineer's review decision on a task. Every decision is preserved in `decisions[]` (never overwritten); the task's `status`/`review_status` reflect the latest one.

**Request body**

```json
{ "decision": "ACCEPT" }
```
```json
{ "decision": "MODIFY", "rationale": "Acceptance criteria too vague.", "changes": "Add a specific edge case for empty destination URLs." }
```
```json
{ "decision": "REJECT", "rationale": "Out of scope for this milestone." }
```

`rationale` is required for `MODIFY` and `REJECT`; `changes` is additionally required for `MODIFY` — enforced with a `422` if missing.

**Status/review_status after each decision:**

| `decision` | `review_status` | `status` |
|---|---|---|
| `ACCEPT` | `ACCEPT` | `APPROVED` |
| `MODIFY` | `MODIFY` | `NEEDS_REVISION` |
| `REJECT` | `REJECT` | `REJECTED` |

`MODIFY` results in `NEEDS_REVISION` rather than `APPROVED`: this endpoint records the requested change as text, it does not apply it — the task genuinely still needs revision before it's ready, there's just no "apply the edit" capability yet.

**Response — `200 OK`** — the updated task, same shape as `GET /api/v1/tasks/{task_id}`.

**Errors**

| Status | Cause |
|---|---|
| 404 | No task exists with that `task_id` |
| 422 | `rationale`/`changes` missing where required |
| 500 | Persistence failure |

## POST /api/v1/tasks/{task_id}/ai-assist

Requests AI assistance for one specific task, per the Phase 5 workflow: `Approved Task → engineer requests assistance → task-specific prompt → AI provider → structured recommendation → engineer review`. **Requires the task's `status` to be `APPROVED`** (see the Phase 4 task lifecycle above) — this is the "Approved Task" precondition, enforced, not just documented.

**Request body**

```json
{ "assistance_type": "CODE_GENERATION", "instructions": "Implement the requested functionality." }
```

`assistance_type` must be one of `DESIGN`, `CODE_GENERATION`, `DEBUGGING`, `REFACTORING`, `TEST_GENERATION`, `DOCUMENTATION`, `SECURITY_REVIEW`, `PERFORMANCE_REVIEW` — deliberately **not** the same list as a task's own `ai_assistance_type` field (Phase 4), which additionally allows `NONE`; requesting assistance with type `NONE` isn't a meaningful action, so it's rejected with `422`. `instructions` is optional free text.

**Revision detection (automatic, no extra field needed):** if the task's most recent AI run was most recently decided `MODIFY`, this request is treated as a revision of it — the response's `revised_from_ai_run_id` is set, and the engineer's `rationale`/`changes` from that `MODIFY` decision are folded into the prompt as "Engineer feedback on the previous attempt". If the most recent run was `ACCEPT`ed, `REJECT`ed, or never decided, this is just an independent new run.

**Response — `201 Created`** — an `AIRun`:

```json
{
  "id": "AI-RUN-001",
  "task_id": "TASK-004",
  "provider": "anthropic",
  "model": "claude-sonnet-5",
  "assistance_type": "CODE_GENERATION",
  "instructions": "Implement the requested functionality.",
  "status": "COMPLETED",
  "response": {
    "summary": "Use a unique database constraint.",
    "approach": "Generate the code and retry on collision.",
    "files_to_change": ["url_service.py"],
    "proposed_changes": ["Add uniqueness constraint"],
    "tests_to_add": ["test_collision_retry"],
    "risks": ["High concurrency may require additional testing."],
    "assumptions": [],
    "confidence": "MEDIUM"
  },
  "error": null,
  "duration_ms": 1834,
  "revised_from_ai_run_id": null,
  "decisions": [],
  "created_at": "2026-01-01T00:00:00+00:00"
}
```

(This example is `backend/tests/support/ai_recommendation_payloads.py::VALID_RECOMMENDATION`.) Note: `prompt` is persisted (for audit) but **not** included in this response — see [validation/PHASE-5-SECURITY-REVIEW.md](validation/PHASE-5-SECURITY-REVIEW.md) "AI response storage".

**A failed run is still persisted** (unlike Phase 3/4's `analyze`/`.../tasks`, where a failed call persists nothing) — `status: "FAILED"`, `response: null`, and a generic, non-internal `error` classification (never the raw provider exception text — see the security review). This gives the AI run history an honest record of failed attempts, not just successes.

**Errors**

| Status | Cause |
|---|---|
| 404 | No task exists with that `task_id` |
| 409 | The task exists but isn't `APPROVED` |
| 422 | Invalid `assistance_type` |
| 503 | The AI provider call itself failed (run persisted as `FAILED`) |
| 502 | The AI provider's response failed schema validation (run persisted as `FAILED`) |
| 500 | Persistence failure |

## POST /api/v1/ai-runs/{ai_run_id}/decision

Records an engineer's review decision on a specific AI run's recommendation — distinct from `POST /api/v1/tasks/{task_id}/decision` (which reviews a task's place in the plan, Phase 4). Reuses the same `EngineerDecision` model and `ACCEPT`/`MODIFY`/`REJECT` request shape, with `ai_run_id` set (Phase 4's task decisions leave it `null`).

**Request body** — identical shape to the task-decision endpoint:

```json
{ "decision": "ACCEPT", "rationale": "The recommendation matches the task requirements." }
```
```json
{ "decision": "MODIFY", "rationale": "Need database uniqueness constraint.", "changes": "Add unique constraint and retry handling." }
```
```json
{ "decision": "REJECT", "rationale": "The proposed approach does not satisfy the scalability requirement." }
```

Same validation as the task-decision endpoint: `rationale` required for `MODIFY`/`REJECT`, `changes` additionally required for `MODIFY` — `422` if missing.

**What each decision means for this run:**

* **ACCEPT** — the recommendation is approved. It does not automatically become code — see "No Automatic Code Execution" below. It still requires actual validation whenever implementation occurs (not yet built — future phase).
* **MODIFY** — the recommendation needs changes. The original `AIRun` (and its original `response`) is never overwritten — the engineer's feedback becomes the `rationale`/`changes` on this decision, and the *next* `ai-assist` call for the task is automatically linked to this run via `revised_from_ai_run_id` (see above).
* **REJECT** — the recommendation is rejected. The task remains `APPROVED` and available for another `ai-assist` request with a different approach.

**Response — `200 OK`** — the updated `AIRun`, with the new decision appended to `decisions[]`.

**`reviewer` is always `null`** — no authentication exists anywhere in this system (see [validation/PHASE-4-SECURITY-REVIEW.md](validation/PHASE-4-SECURITY-REVIEW.md) "Authorization assumptions"). The field exists on the model for when identity becomes available; it is never accepted from the client, since an unauthenticated, self-reported reviewer name would be meaningless.

**Errors**

| Status | Cause |
|---|---|
| 404 | No AI run exists with that `ai_run_id` |
| 422 | `rationale`/`changes` missing where required |
| 500 | Persistence failure |

## AI run history

`GET /api/v1/tasks/{task_id}` (Phase 4) now additionally returns `ai_runs: AIRun[]` for that task, in creation order — this is how the frontend's "AI Run History" view (and `AI-RUN-001 → MODIFY → AI-RUN-002` traceability) is read back; there is no separate `GET .../ai-runs` endpoint, since embedding avoids a second round-trip for data that's always fetched together with its task.

## POST /api/v1/ai-runs/{ai_run_id}/artifacts

Generates draft artifacts (real proposed file content, not descriptive text) from an AI run's recommendation. **Requires the run's most recent decision to be `ACCEPT`** — a rejected or not-yet-decided recommendation cannot generate artifacts; this is the structural implementation of "Rejected AI recommendations must NOT become approved artifacts."

**No request body** — the recommendation to work from is already on the AI run.

**Response — `201 Created`** — a list of `Artifact`:

```json
[
  {
    "id": "ARTIFACT-001",
    "task_id": "TASK-004",
    "ai_run_id": "AI-RUN-001",
    "artifact_type": "SOURCE_CODE",
    "path": "backend/app/services/url_service.py",
    "content": "def create_short_url(destination_url: str) -> str:\n    ...\n",
    "description": "Adds a uniqueness constraint check with retry handling for short code collisions.",
    "status": "PENDING_REVIEW",
    "version": 1,
    "supersedes_artifact_id": null,
    "diff": "--- a/backend/app/services/url_service.py\n+++ b/backend/app/services/url_service.py\n@@ ...",
    "decisions": [],
    "created_at": "2026-01-01T00:00:00+00:00"
  }
]
```

One artifact is created per file the recommendation implies — see `backend/tests/support/artifact_payloads.py::MULTI_FILE_ARTIFACT_GENERATION` for a multi-file example. `diff` is computed at read time (not stored) — a unified diff against the version this one supersedes, or against an empty file for version 1.

**Controlled File Writes:** every proposed `path` is validated (`app.utils.safe_path.resolve_artifact_path`) before anything is written or persisted — absolute paths and `..` segments are rejected outright, and the fully resolved path must stay within the sandboxed `generated/` workspace (established as the workbench's designated artifact location since Phase 1A). **One unsafe path in the batch rejects the entire batch** (`422`) — nothing is written and nothing is persisted, rather than silently dropping just the bad one. See `backend/tests/test_safe_path.py` and `backend/tests/test_artifacts_api.py::test_unsafe_relative_path_traversal_is_rejected_and_not_persisted`.

**Errors**

| Status | Cause |
|---|---|
| 404 | No AI run exists with that `ai_run_id` |
| 409 | The run's most recent decision isn't `ACCEPT` (rejected, still pending, or never decided) |
| 422 | A proposed artifact path is unsafe (absolute, contains `..`, or resolves outside `generated/`) |
| 503 | The AI provider call itself failed |
| 502 | The AI provider's response failed schema validation |
| 500 | Persistence failure |

Unlike `POST /api/v1/tasks/{id}/ai-assist` (Phase 5), a failed generation attempt is **not** persisted — there is no natural "failed artifact" row to create (nothing was produced), so this simply surfaces as the error above with nothing written to the database or disk.

## GET /api/v1/tasks/{task_id}/artifacts

Retrieves every artifact version ever generated for a task, in creation order (all versions, not just the latest — so an engineer can see the full regeneration history, e.g. `ARTIFACT-001` version 1 and `ARTIFACT-002` version 2 superseding it, both present).

**Errors**

| Status | Cause |
|---|---|
| 404 | No task exists with that `task_id` |
| 500 | Persistence failure |

## GET /api/v1/artifacts/{artifact_id}

Retrieves a single artifact by its own id.

**Errors**

| Status | Cause |
|---|---|
| 404 | No artifact exists with that `artifact_id` |
| 500 | Persistence failure |

## POST /api/v1/artifacts/{artifact_id}/decision

Records an engineer's review decision on a generated artifact — reuses the same `EngineerDecision` model and request shape as the task-decision and AI-run-decision endpoints (`artifact_id` set, `ai_run_id` left `null`).

**Status after each decision:** `ACCEPT` → `APPROVED`, `MODIFY` → `NEEDS_REVISION`, `REJECT` → `REJECTED` — same mapping as `POST /api/v1/tasks/{task_id}/decision` (Phase 4). `MODIFY` records the requested change; regenerating the artifact (a new `POST .../artifacts` call) is what actually produces a new version — this endpoint alone does not.

**Errors**

| Status | Cause |
|---|---|
| 404 | No artifact exists with that `artifact_id` |
| 422 | `rationale`/`changes` missing where required |
| 500 | Persistence failure |

## POST /api/v1/artifacts/{artifact_id}/validate

Runs one controlled, allowlisted check against an artifact and persists the result. See [validation/validation-strategy.md](validation/validation-strategy.md) for exactly what each `validation_type` runs — the API never accepts a raw command.

**Request body**

```json
{ "validation_type": "STATIC_ANALYSIS" }
```

`validation_type` must be one of `UNIT_TEST`, `INTEGRATION_TEST`, `API_CONTRACT`, `STATIC_ANALYSIS`, `SECURITY`, `PERFORMANCE`, `BUILD`.

**Response — `201 Created`**

```json
{
  "id": "VALIDATION-001",
  "artifact_id": "ARTIFACT-001",
  "task_id": "TASK-004",
  "validation_type": "STATIC_ANALYSIS",
  "command": "ruff check .",
  "status": "PASSED",
  "output": "All checks passed!\n",
  "evidence": "All checks passed!",
  "error": null,
  "duration_ms": 42,
  "metadata": { "exit_code": 0 },
  "created_at": "2026-01-01T00:00:00+00:00"
}
```

`PERFORMANCE` always returns `status: "NOT_VALIDATED"` at this generic artifact level, with `error` stating why — a `NOT_VALIDATED` result is never presented as if it were a pass.

**Errors**

| Status | Cause |
|---|---|
| 404 | No artifact exists with that `artifact_id` |
| 422 | Invalid `validation_type` |
| 500 | Persistence failure |

## GET /api/v1/artifacts/{artifact_id}/validations

Retrieves every validation ever run against an artifact, in creation order.

**Errors**: `404` (unknown artifact), `500` (persistence failure).

## GET /api/v1/validations/{validation_id}

Retrieves a single validation by its own id.

**Errors**: `404` (unknown validation), `500` (persistence failure).

## No Automatic Code Execution

The workbench never modifies files, executes shell commands, installs dependencies, commits, pushes, or deploys **outside of an engineer-approved artifact write to the sandboxed `generated/` workspace** — and even that write only happens as the direct, visible result of a `POST /api/v1/ai-runs/{ai_run_id}/artifacts` call the engineer made after explicitly `ACCEPT`ing a recommendation, never automatically. This is structural, not just policy: `AIRecommendation`'s fields (Phase 5) are plain descriptive strings — no code path acts on them beyond persisting and returning them. `Artifact` content (Phase 6) is real proposed file content, but writing it is gated by the `ACCEPT`-only rule above, contained to `generated/` by `app.utils.safe_path`, and still lands in `PENDING_REVIEW` status — nothing is ever marked `APPROVED` without a further, separate engineer decision on the artifact itself. Applying an approved artifact to the *actual* project source (outside `generated/`) is not implemented — that remains manual, engineer-controlled work.

## Task lifecycle (this phase)

Only the planning/review portion of the lifecycle is implemented — no execution states (`READY`, `IN_PROGRESS`, `IMPLEMENTED`, `VALIDATION_*`) exist yet:

```text
REVIEW_REQUIRED  (set on generation — a distinct persisted DRAFT state is not modeled; a
                   generated task is a draft by definition and immediately needs review)
   │
   ├── ACCEPT → APPROVED
   ├── MODIFY → NEEDS_REVISION   (rationale + requested changes recorded, not applied)
   └── REJECT → REJECTED
```

`BLOCKED` and `VALIDATION_FAILED` (named in the phase's task-lifecycle spec) are not reachable by any code path in this phase — no dependency-based auto-blocking is implemented (a task whose dependency was rejected does not automatically change status; this is a deliberate scope deferral, not an oversight).

## Identifiers

`requirement_id` (e.g. `REQ-001`) is the requirement's database primary key formatted as `REQ-{id:03d}`, matching the `REQ-*` convention in [ENGINEERING_WORKFLOW.md](ENGINEERING_WORKFLOW.md)'s traceability model. The structured analysis items inside `latest_analysis` use their own prefixes per [REQUIREMENTS.md](REQUIREMENTS.md) §4: `FR-*`, `NFR-*`, `AMB-*`, `ASM-*`, `CON-*`, `SC-*`, `ENG-*`. These per-analysis IDs restart at `001` within each analysis — they are not globally unique across analyses (there is no cross-analysis traceability requirement yet).

`plan_id` (`PLAN-*`) and `task_id` (`TASK-*`) are likewise database primary keys formatted with their prefix — `TASK-*` is globally unique across all plans (not per-plan), since `GET /api/v1/tasks/{task_id}` is a top-level resource. `decision` records use `DECISION-*`, and per-task/per-plan risk items use `RISK-*`, restarting at `001` per plan like the analysis-item ids above.

**Local vs. global task ids:** the AI's task-decomposition output numbers tasks `TASK-001`, `TASK-002`, ... *local to that one response*, and `dependencies` reference those local ids — the AI has no way to predict the eventual database id. Persistence (`app/repositories/engineering_plan_repository.py::save_generated_plan`) remaps every local id to its real global `TASK-*` id, in both the task's own id and every dependency reference, before anything is returned to the API. Clients only ever see final, global ids — the local numbering is an internal detail of the AI contract (`app/schemas/task_decomposition.py`), not something either the API or its consumers deal with.

`ai_run_id` (`AI-RUN-*`) is likewise a database primary key formatted with its prefix, globally unique (not per-task). `artifact_id` (`ARTIFACT-*`) and `validation_id` (`VALIDATION-*`) follow the same convention. `EngineerDecisionResponse.ai_run_id`/`artifact_id` are `null` unless a decision is of that kind — the same `DECISION-*` id space and `EngineerDecision` model is reused across all three decision endpoints (task-plan, AI-run, artifact), distinguished by which one of `task_id`/`ai_run_id`/`artifact_id` is set on the underlying row, not by a separate type field.

## Error response shape

All error responses are:

```json
{ "detail": "<clean, non-internal message>" }
```

No stack trace, exception type, or internal detail is ever included — see [validation/PHASE-3-SECURITY-REVIEW.md](validation/PHASE-3-SECURITY-REVIEW.md), [validation/PHASE-4-SECURITY-REVIEW.md](validation/PHASE-4-SECURITY-REVIEW.md), and [validation/PHASE-5-SECURITY-REVIEW.md](validation/PHASE-5-SECURITY-REVIEW.md).
