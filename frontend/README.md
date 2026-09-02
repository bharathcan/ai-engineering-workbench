# Frontend

React + TypeScript frontend for the AI Engineering Workbench, scaffolded with Vite. As of Phase 4, it displays backend connectivity, a Requirement Analyzer form, and an Engineering Plan view with per-task Accept/Modify/Reject review. Artifact management and a validation dashboard are not implemented yet. See [../ARCHITECTURE.md](../ARCHITECTURE.md) for the full intended scope.

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

Type-checks (`tsc -b`) and produces a production bundle in `dist/`.

## Lint

```bash
npm run lint
```

Uses [oxlint](https://oxc.rs) (the Vite template default) rather than ESLint, for lighter, faster tooling.

## What it does

On load, the app calls `GET /health` on the backend (`src/api/health.ts`) and displays one of three states: `Checking backend…` (loading), `Connected` (backend responded with `{"status": "ok"}`), or `Backend unavailable` (request failed or backend returned something else).

Below that, the Requirement Analyzer (`src/components/RequirementAnalyzer.tsx`) takes a requirement in a textarea and, on submit, calls `POST /api/v1/requirements` then `POST /api/v1/requirements/{id}/analyze` (`src/api/requirements.ts`), then renders the structured result: summary, functional/non-functional requirements, ambiguities, assumptions, constraints, success criteria, and engineering concerns. Ambiguities and assumptions are styled distinctly (amber vs. blue) so they aren't mistaken for each other. API errors (e.g. no AI provider configured) are shown inline rather than failing silently.

Once an analysis is shown, `EngineeringPlanPanel` (`src/components/EngineeringPlanPanel.tsx`) offers a "Generate Engineering Plan" button that calls `POST /api/v1/requirements/{id}/tasks` (`src/api/tasks.ts`). A `GENERATED` plan renders each task as a card — id, type, description, requirement traceability, dependencies, acceptance criteria, AI-assistance type — with Accept / Modify / Reject buttons that call `POST /api/v1/tasks/{task_id}/decision`; Modify and Reject open a small form requiring rationale text before submitting, matching the backend's validation. A `BLOCKED` plan (unresolved material ambiguity) renders as a distinct "PLAN BLOCKED" panel with the reason, instead of any tasks.
