# AI Engineering Workbench — Assignment Submission

## 📋 Complete Assignment Response

This repository contains a **production-grade AI-assisted engineering platform** that demonstrates how AI (Claude) can accelerate software development while maintaining full engineer ownership and rigorous quality gates.

**Start here:** Read this file first, then refer to the specific documents below based on what you need.

---

## 📁 Key Documents

| Document | Purpose | Read Time |
|----------|---------|-----------|
| **ASSIGNMENT_DELIVERABLES.md** | Complete assignment response with all requirements | 20 min |
| **DEMO_GUIDE.md** | Step-by-step walkthrough of all 3 scenarios | 15 min |
| **FIXES_IMPLEMENTED.md** | Summary of critical fixes and improvements | 10 min |
| **This file** | Navigation and quick reference | 5 min |

---

## 🎯 What This Demonstrates

### ✅ Requirement: Effective Use of AI Tools Across Development Tasks

The workbench integrates AI assistance at **7 critical stages**:

1. **Requirement Analysis** — AI analyzes raw requirement, identifies ambiguities, extracts scope
2. **Task Decomposition** — AI breaks requirement into 5-15 structured engineering tasks
3. **Task Planning** — AI suggests execution order and dependencies
4. **AI Recommendations** — AI proposes approach for each task (with approach, files, changes, tests)
5. **Artifact Generation** — AI generates actual code, tests, APIs, documentation
6. **Validation** — System validates all generated artifacts
7. **Reporting** — System compiles comprehensive audit trail

Each stage has **engineer review/approval gates** — AI assists, engineer decides.

### ✅ Requirement: Strong Engineering Ownership of All Outputs

Engineers control every decision:

| Stage | Engineer Decision |
|-------|-------------------|
| Requirement | Clarify ambiguities (or approve as-is) |
| Analysis | Review ambiguity analysis |
| Planning | Accept, modify, or reject task decomposition |
| Tasks | Approve each task individually |
| AI Runs | Accept, modify, or reject AI recommendations |
| Artifacts | Review generated code, approve or reject |
| Validation | Review validation results, assess risk |
| Report | Sign off on final output |

Result: **Complete audit trail** of every decision with rationales.

### ✅ Requirement: Rigorous Validation of AI-Generated Results

**7-stage validation pipeline:**
- **UNIT_TEST** — pytest validation
- **INTEGRATION_TEST** — Full app + DB tests
- **STATIC_ANALYSIS** — ruff code quality check
- **API_CONTRACT** — OpenAPI schema validation
- **BUILD** — Import check (app boots cleanly)
- **SECURITY** — Pattern scan for hardcoded secrets
- **PERFORMANCE** — Extensible for performance metrics

**Key principle:** `NOT_VALIDATED` ≠ `PASSED` — engineer must explicitly run/skip each

---

## 🚀 Quick Start (5 minutes)

### 1. Prerequisites
```bash
# Backend: Python 3.11+ with FastAPI
# Frontend: Node.js 18+ with React/TypeScript
# Optional: Anthropic API key for live Claude
```

### 2. Start Services
```bash
# Terminal 1: Backend (port 8000)
cd ai-engineering-workbench/backend
python -m app.cli serve

# Terminal 2: Frontend (port 5173)
cd ai-engineering-workbench/frontend
npm run dev
```

### 3. Open Browser
```
http://localhost:5173
```

### 4. Create Example Requirements
```bash
bash scripts/setup_examples.sh
```

### 5. Select Requirement & Follow Workflow
```
Requirement tab → Engineering Plan → Tasks → AI Runs → Artifacts → Final Report
```

---

## 📚 Understanding the Platform

### Data Flow

```
Engineer inputs requirement text
              ↓
AI analyzes → Requirement Analysis (FR-*, NFR-*, AMB-*, etc.)
              ↓
Engineer clarifies ambiguities (optional)
              ↓
AI decomposes → Engineering Plan with 5-15 tasks
              ↓
Engineer approves tasks
              ↓
Engineer requests AI assistance per task
              ↓
AI generates recommendation (not code yet)
              ↓
Engineer accepts/modifies recommendation
              ↓
AI generates artifacts (actual code, tests, APIs)
              ↓
System validates artifacts (pytest, ruff, security scan, etc.)
              ↓
Engineer reviews validation results, approves/rejects artifacts
              ↓
Final Report compiled with all decisions, risks, assumptions
              ↓
Export as Markdown for documentation
```

### Key Concepts

**Stable IDs:** Every item gets an ID that persists across workflow:
- Requirement analysis: `FR-001`, `FR-002`, `NFR-001`, `AMB-001`, etc.
- Engineering plan: `TASK-001`, `TASK-002`, etc.
- Artifacts: `ARTIFACT-001`, `ARTIFACT-002`, etc.
- Validations: `VALIDATION-001`, `VALIDATION-002`, etc.

This enables **traceability** — you can trace any artifact back to the original requirement.

**Engineer Decisions:** Every approval/rejection is recorded:
```json
{
  "scope": "Task TASK-006 — Write test suite",
  "decision": "ACCEPT",
  "rationale": "Covers all acceptance criteria",
  "reviewer": "bharath",
  "created_at": "2026-09-03T14:22:51Z"
}
```

---

## 🔄 Complete Workflow Examples

### Example 1: Greenfield (New System)
**Requirement:** *"Build a scalable URL shortener service..."*

**Workflow:**
1. ✅ Analyze → 8 functional requirements, 4 ambiguities
2. ✅ Clarify → Engineer resolves ambiguities
3. ✅ Plan → 10 implementation tasks generated
4. ✅ Approve → Engineer reviews & accepts all tasks
5. ✅ Assist → AI provides recommendations for CODE_GENERATION + TEST_GENERATION
6. ✅ Generate → Artifacts created (code, tests, config)
7. ✅ Validate → Tests pass, security scan passes, build passes
8. ✅ Report → Final report shows 10/10 tasks approved, 2/2 artifacts validated

### Example 2: Brownfield (Performance Optimization)
**Requirement:** *"Optimize database query performance..."*

**Workflow:**
1. ✅ Analyze → Constraints identified (backward compatibility, SLA targets)
2. ✅ Plan → 6 tasks focused on optimization (indexes, pooling, caching)
3. ✅ Assist → AI provides DEBUGGING + PERFORMANCE_REVIEW recommendations
4. ✅ Artifacts → Database migrations, performance tests
5. ✅ Validate → New performance benchmarks, regression tests pass

**Key difference:** Focused on constraints, backward compatibility, performance metrics

### Example 3: Ambiguous (Vague Specification)
**Requirement:** *"Add analytics to the shortener..."*

**Workflow:**
1. ✅ Analyze → AI identifies 5 critical ambiguities:
   - What events to track?
   - What insights matter?
   - Storage/retention?
   - Privacy constraints?
   - Scale requirements?
2. ✅ Clarify → Engineer provides specific answers:
   ```
   "Track daily clicks by country/device. GDPR: anonymize IPs. 
   50k-500k events/day. Store in same DB."
   ```
3. ✅ Re-analyze → System re-analyzes with context, preserves FR-* IDs
4. ✅ Plan → Plan generated with concrete, unambiguous tasks
5. ✅ Complete → Full workflow with clarity

**Key feature:** ID preservation during clarification — shows workbench handles ambiguity without breaking references

---

## 📊 Platform Statistics

| Metric | Value |
|--------|-------|
| **Database Tables** | 12 (requirement, analysis, plan, task, ai_run, artifact, validation, decisions, etc.) |
| **API Endpoints** | 25+ RESTful endpoints (see /docs) |
| **Validation Types** | 7 (unit, integration, static, API, build, security, performance) |
| **Frontend Screens** | 8 (Dashboard, Requirement, Plan, Tasks, AI Runs, Artifacts, Validation, Final Report) |
| **Decision Points** | 5 (clarify, approve plan, request AI, accept recommendation, approve artifact) |

---

## 🔐 Security & Safety

### Validation Strategy
- **No arbitrary shell execution** — all validation commands are hardcoded & allowlisted
- **Safe path resolution** — artifact paths validated (no `../`, no absolute paths)
- **Transaction rollback** — all failures trigger automatic rollback
- **Audit trail** — every decision recorded with timestamp and rationale

### AI Integration Boundaries
- **Content boundary** — Task context treated as untrusted data (prompt injection resistant)
- **Task scope** — AI operates within individually scoped tasks
- **Output validation** — All AI outputs validated against schema
- **Engineer approval** — No automatic deployment; all outputs require engineer approval

---

## 📈 Evaluation Against Assignment Criteria

| Criterion | Status | Evidence |
|-----------|--------|----------|
| **Effective use of AI tools** | ✅ | AI assists in 7 stages; engineer chooses type (CODE_GENERATION, TESTING, etc.) |
| **Strong engineering ownership** | ✅ | Engineer controls: clarifications, plan, tasks, AI recommendations, artifacts |
| **Rigorous validation** | ✅ | 7-stage validation; NOT_VALIDATED tracked separately; full audit trail |
| **Code quality** | ✅ | Generated artifacts validated against pytest, ruff, security scan |
| **Real-world scenarios** | ✅ | Greenfield (new), Brownfield (optimization), Ambiguous (vague specs) |
| **Completeness** | ✅ | Full workflow: Requirement → Planning → Execution → Artifacts → Validation → Report |
| **Clarity & defensibility** | ✅ | This doc + ASSIGNMENT_DELIVERABLES.md + code comments explain all decisions |

---

## 📖 How to Use This Submission

### For Quick Understanding
1. Read this file (5 min)
2. Skim ASSIGNMENT_DELIVERABLES.md (15 min)
3. Run the platform and try Scenario A (Greenfield) (10 min)

### For Complete Review
1. Read ASSIGNMENT_DELIVERABLES.md (20 min)
2. Read FIXES_IMPLEMENTED.md (10 min)
3. Review DEMO_GUIDE.md (15 min)
4. Run all 3 scenarios end-to-end (45 min)
5. Review API docs: http://localhost:8000/docs

### For Evaluation
Review these specific sections:
- **AI Integration:** ASSIGNMENT_DELIVERABLES.md § 1 (Architecture)
- **Engineering Ownership:** DEMO_GUIDE.md § Complete Workflow (all decision points)
- **Validation:** ASSIGNMENT_DELIVERABLES.md § 4 (Testing Approach)
- **Risk Awareness:** ASSIGNMENT_DELIVERABLES.md § 5-6 (Risks & Trade-offs)
- **Scenarios:** ASSIGNMENT_DELIVERABLES.md § 2 (Greenfield, Brownfield, Ambiguous)

---

## 🎓 What You'll Learn From This

### About AI-Assisted Engineering
- How to decompose vague requirements into actionable work
- How to integrate AI recommendations without losing engineer control
- How to validate AI-generated code systematically
- How to maintain quality gates at each stage

### About Software Engineering
- Task decomposition and dependency management
- Risk identification and mitigation
- Validation and testing strategies
- Audit trail and decision tracking

### About System Design
- RESTful API design (25+ endpoints, OpenAPI schema)
- Database schema with audit support
- Stateful workflow with multiple decision points
- Frontend state management (React hooks)

---

## 🚢 Files Overview

### Frontend
```
frontend/src/
├── screens/          # UI screens for each stage
│   ├── RequirementScreen.tsx
│   ├── EngineeringPlanScreen.tsx
│   ├── TasksScreen.tsx
│   ├── AIRunsScreen.tsx
│   ├── ArtifactsScreen.tsx
│   ├── ValidationScreen.tsx
│   └── FinalReportScreen.tsx
├── api/              # API client functions
│   ├── requirements.ts
│   ├── tasks.ts
│   └── artifacts.ts
└── hooks/            # React data hooks
    └── useProjectData.ts
```

### Backend
```
backend/app/
├── ai/               # AI integration
│   ├── base.py
│   ├── prompts.py    # Task-specific prompts
│   └── providers.py
├── services/         # Business logic
│   ├── requirement_analyzer.py
│   ├── engineering_plan_service.py
│   ├── artifact_generator.py
│   ├── validation_runner.py
│   └── ...
├── models/           # Database models
│   └── engineering_plan.py
├── schemas/          # Pydantic schemas
│   ├── requirement_analysis.py
│   ├── artifact_generation.py
│   └── ...
└── api/              # API routes
    └── routes/
```

---

## 💡 Key Design Decisions

1. **Stable IDs across workflow** — Trade: complexity; Benefit: traceability
2. **Separate artifact lifecycle** — Trade: more tables; Benefit: independent validation
3. **Engineer decision recording** — Trade: more DB writes; Benefit: full audit trail
4. **Python test generation only** — Trade: language limitation; Benefit: consistent validation
5. **Linear workflow stages** — Trade: more clicks; Benefit: prevents broken assumptions
6. **Multi-stage validation** — Trade: slower feedback; Benefit: catches issues early

All trade-offs documented in ASSIGNMENT_DELIVERABLES.md § 6.

---

## 🔗 Important Files to Review

1. **Assignment Response:** `/ASSIGNMENT_DELIVERABLES.md` (300+ lines)
2. **Demo Walkthrough:** `/DEMO_GUIDE.md` (400+ lines)
3. **Fixes Summary:** `/FIXES_IMPLEMENTED.md`
4. **This Navigation:** `/ASSIGNMENT_README.md` (this file)

---

## ✅ Verification Checklist

- [ ] Backend starts: `python -m app.cli serve`
- [ ] Frontend starts: `npm run dev`
- [ ] Browser opens: http://localhost:5173
- [ ] Can create requirement with API
- [ ] Can analyze requirement (AI integration works)
- [ ] Can clarify ambiguities
- [ ] Can generate engineering plan
- [ ] Can approve tasks
- [ ] Can request AI assistance
- [ ] Can generate artifacts
- [ ] Can validate artifacts
- [ ] Can view final report
- [ ] Can export final report as markdown
- [ ] All 3 scenarios runnable (greenfield, brownfield, ambiguous)

---

## 🎉 Summary

This workbench demonstrates **complete AI-assisted software engineering** where:

✅ AI accelerates development within structured, scoped tasks
✅ Engineers retain full control and make all critical decisions
✅ Every output is validated and tracked
✅ Complete audit trail enables full accountability
✅ Supports diverse requirement types (new, optimization, ambiguous)
✅ Production-ready: error handling, transactions, validation, security

**Core principle maintained throughout:**
> "AI assists the engineer within tasks; the engineer owns execution and quality."

---

## 📞 Questions?

Refer to:
1. **How to run?** → DEMO_GUIDE.md § Quick Start
2. **What was fixed?** → FIXES_IMPLEMENTED.md
3. **How does it work?** → ASSIGNMENT_DELIVERABLES.md § 1-2
4. **What's the risk?** → ASSIGNMENT_DELIVERABLES.md § 5-6
5. **Technical details?** → Code comments in backend/ and frontend/

---

**Thank you for reviewing this submission!** 🚀

*Generated: 2026-09-03*
*By: Bharath Putta (bharathcan)*
*For: AI-Proficient Software Engineer Interview Assignment*
