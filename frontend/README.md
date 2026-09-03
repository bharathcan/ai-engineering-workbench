# Frontend

React + TypeScript frontend for the AI Engineering Workbench, built with Vite. Implements the full workflow UI: landing/dashboard, requirement analysis, engineering plan review, task execution with AI assistance, artifact review, validation, a scenarios showcase, and a final report — all backed by the real backend API. See [../README.md](../README.md) and [../ARCHITECTURE.md](../ARCHITECTURE.md) for the full system picture; this file covers frontend-specific setup and structure.

## Setup

```bash
cd frontend
npm install
```

## Run

```bash
npm run dev
```

Opens at [http://localhost:5173](http://localhost:5173). The backend is expected at `http://localhost:8000` by default — override with `VITE_API_BASE_URL` (see [../.env.example](../.env.example)).

## Build

```bash
npm run build
```

Type-checks (`tsc -b`) and produces a production bundle in `dist/`. This is what Render's `workbench-frontend` static site deploys.

## Test

```bash
npm run test
```

Vitest + React Testing Library. A few `AppShell`/`ScenariosScreen` assertions currently fail after an earlier UI redesign changed how the empty-project state renders — a test-maintenance gap, not a functional regression (see README.md §12).

## Lint

```bash
npm run lint
```

Uses [oxlint](https://oxc.rs) rather than ESLint, for lighter, faster tooling.

## What it does

`AppShell` (`src/components/AppShell.tsx`) hosts the project selector and navigation across 9 screens:

| Screen | Purpose |
|---|---|
| Dashboard | Landing page (`TalpLanding`) when no project is selected; project overview once one is |
| Requirement | Create a requirement, run analysis, resolve ambiguities, see the structured result |
| Engineering Plan | Trigger task decomposition; view the generated plan or the ambiguity-gate block reason |
| Tasks | Per-task detail — Accept/Modify/Reject, request AI assistance, review AI runs, generate artifacts |
| AI Runs | Full history of AI requests/responses across all tasks, with confidence and decisions |
| Artifacts | Generated files — content, diffs against prior versions, Accept/Modify/Reject |
| Validation | Run and review allowlisted validation checks against approved artifacts |
| Scenarios | Live walkthroughs of the greenfield/brownfield/ambiguous demonstration scenarios |
| Final Report | Aggregated, exportable summary of a project's full pipeline |

`src/hooks/useProjectData.ts` assembles one consistent data snapshot per selected requirement (requirement + analysis, plan + tasks + AI runs, each task's artifacts, each artifact's validations) so every screen reads from the same state instead of re-fetching independently. Task-artifact and artifact-validation fetches run concurrently (`Promise.all`), not sequentially — an earlier sequential version made 40+ round trips on a single reload once a project accumulated enough tasks and artifacts.

`src/api/` holds one typed fetch client per backend resource (requirements, tasks, artifacts, validations, urls) — no screen calls `fetch` directly.
