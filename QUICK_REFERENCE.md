# Quick Reference Card

## 🚀 Start Here (Decide What to Read)

### "I have 5 minutes"
→ Read: **ASSIGNMENT_README.md** (this repo's navigation guide)

### "I have 15 minutes"
→ Read: **ASSIGNMENT_README.md** + start backend/frontend
→ Do: Quick workflow on Greenfield scenario

### "I have 45 minutes"
→ Read: **ASSIGNMENT_DELIVERABLES.md** (complete assignment response)
→ Do: Walkthrough all 3 scenarios using **DEMO_GUIDE.md**

### "I want to evaluate thoroughly"
→ Read: All documents in order:
  1. ASSIGNMENT_README.md (overview)
  2. ASSIGNMENT_DELIVERABLES.md (complete response)
  3. FIXES_IMPLEMENTED.md (what was fixed)
  4. DEMO_GUIDE.md (detailed walkthrough)
→ Do: Run all scenarios + explore API + review code

---

## 📋 Assignment Requirements ← → Implementation

| Assignment Requirement | Where Implemented | Evidence |
|---|---|---|
| Effective use of AI tools | 7-stage pipeline (§ DELIVERABLES 1) | Analysis, planning, recommendations, artifact generation |
| Strong engineering ownership | Decision gates (§ DEMO 1-10) | Engineer approves at every stage |
| Rigorous validation | 7-stage validator (§ DELIVERABLES 4) | pytest, ruff, API, build, security scans |
| Requirement understanding | RequirementAnalyzer (§ DELIVERABLES 1.1) | Identifies FR-*, NFR-*, AMB-*, SC-*, ENG-* |
| Task decomposition | TaskDecomposer (§ DELIVERABLES 1.2) | Generates 5-15 tasks with dependencies |
| AI-assisted development | Multiple assistance types (§ DELIVERABLES 1.3) | CODE_GENERATION, TEST_GENERATION, DOCUMENTATION, SECURITY_REVIEW, etc. |
| Engineering outputs | Artifact types (§ DELIVERABLES 7) | Code, tests, APIs, documentation, configuration |
| Validation & QA | Validation pipeline (§ DELIVERABLES 4) | All artifacts validated before approval |
| Risk awareness | Risk analysis (§ DELIVERABLES 5-6) | Functional, design, and AI-related risks documented |
| Final engineering output | FinalReportScreen (§ DEMO 9) | Approach, artifacts, risks, assumptions, validation summary |
| Greenfield scenario | REQ-001 + walkthrough (§ DELIVERABLES 2.1) | URL shortener new system development |
| Brownfield scenario | REQ-008 + walkthrough (§ DELIVERABLES 2.2) | Performance optimization of existing system |
| Ambiguous scenario | REQ-009 + walkthrough (§ DELIVERABLES 2.3) | Vague requirement with clarification flow |
| Setup instructions | (§ DELIVERABLES 3 & DEMO Quick Start) | Step-by-step backend/frontend startup |
| Testing approach | (§ DELIVERABLES 4) | Unit, integration, manual testing with known limitations |

---

## 🔄 Workflow at a Glance

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. CREATE REQUIREMENT                                            │
│    Engineer: Enter requirement text                              │
└──────────────────────────┬──────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. ANALYZE REQUIREMENT (AI)                                     │
│    System: AI identifies FR-*, NFR-*, AMB-*, SC-*               │
│    Engineer: Review, clarify ambiguities if needed              │
└──────────────────────────┬──────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. GENERATE ENGINEERING PLAN (AI)                               │
│    System: AI breaks down into 5-15 tasks with dependencies     │
│    Engineer: Review & approve plan                              │
└──────────────────────────┬──────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. APPROVE TASKS                                                │
│    Engineer: Accept/modify/reject each task                     │
└──────────────────────────┬──────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. REQUEST AI ASSISTANCE PER TASK (AI)                          │
│    Engineer: Select assistance type (CODE_GENERATION, etc.)     │
│    System: AI generates recommendation (not code yet)           │
│    Engineer: Review recommendation                              │
└──────────────────────────┬──────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ 6. ACCEPT & GENERATE ARTIFACTS (AI)                             │
│    Engineer: Accept recommendation                              │
│    System: AI generates actual code/tests/docs                  │
│    Engineer: Review artifacts                                   │
└──────────────────────────┬──────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ 7. VALIDATE ARTIFACTS                                           │
│    System: pytest, ruff, security scan, API validation, etc.    │
│    Engineer: Review validation results                          │
└──────────────────────────┬──────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ 8. GENERATE FINAL REPORT                                        │
│    System: Compile all decisions, risks, artifacts, validations │
│    Engineer: Sign off & export markdown                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Three Scenario Types

| Scenario | Type | Key Difference | Example |
|----------|------|---|---|
| **Greenfield** | New system | No constraints from existing code | "Build a URL shortener..." |
| **Brownfield** | Enhancement/optimization | Backward compatibility required | "Optimize DB performance..." |
| **Ambiguous** | Vague spec | Engineer must clarify before planning | "Add analytics..." |

---

## 📊 Key Metrics

| Metric | Value |
|--------|-------|
| Total API endpoints | 25+ |
| Validation types | 7 |
| Database tables | 12 |
| Frontend screens | 8 |
| AI integration points | 7 |
| Engineer decision points | 5 |
| Example scenarios | 3 (greenfield, brownfield, ambiguous) |

---

## ✅ Critical Fixes Applied

| Fix # | What | Status |
|---|---|---|
| 1 | Artifact generation prompt (Python tests) | ✅ FIXED |
| 2 | Final Report tab implementation | ✅ VERIFIED |
| 3 | Multiple scenario examples | ✅ CREATED |
| 4 | Architecture documentation | ✅ CREATED |
| 5 | Setup instructions | ✅ CREATED |
| 6 | Risk analysis & trade-offs | ✅ CREATED |
| 7 | Testing approach documentation | ✅ CREATED |
| 8 | Assignment evaluation matrix | ✅ CREATED |

See **FIXES_IMPLEMENTED.md** for details.

---

## 🗂️ File Structure

```
ai-engineering-workbench/
├── README.md                          # Original project README
├── ASSIGNMENT_README.md               ← START HERE (navigation guide)
├── ASSIGNMENT_DELIVERABLES.md         ← Complete assignment response (300+ lines)
├── DEMO_GUIDE.md                      ← Step-by-step walkthrough (400+ lines)
├── FIXES_IMPLEMENTED.md               ← What was fixed
├── QUICK_REFERENCE.md                 ← This file
├── backend/
│   ├── app/
│   │   ├── ai/prompts.py              ← UPDATED: test artifact generation
│   │   ├── services/
│   │   │   ├── requirement_analyzer.py
│   │   │   ├── engineering_plan_service.py
│   │   │   ├── artifact_generator.py
│   │   │   ├── artifact_service.py
│   │   │   ├── validation_runner.py
│   │   │   └── validation_service.py
│   │   └── api/routes/
│   │       ├── requirements.py
│   │       ├── engineering_plans.py
│   │       ├── tasks.py
│   │       ├── ai_runs.py
│   │       ├── artifacts.py
│   │       └── validations.py
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── screens/
│   │   │   ├── RequirementScreen.tsx
│   │   │   ├── EngineeringPlanScreen.tsx
│   │   │   ├── TasksScreen.tsx
│   │   │   ├── AIRunsScreen.tsx
│   │   │   ├── ArtifactsScreen.tsx
│   │   │   ├── ValidationScreen.tsx
│   │   │   └── FinalReportScreen.tsx
│   │   ├── api/
│   │   │   ├── requirements.ts
│   │   │   ├── tasks.ts
│   │   │   └── artifacts.ts
│   │   └── hooks/useProjectData.ts
└── scripts/
    └── setup_examples.sh              ← NEW: Populate 3 scenarios
```

---

## 🚀 Commands Cheat Sheet

```bash
# Start backend (port 8000)
cd backend && python -m app.cli serve

# Start frontend (port 5173)
cd frontend && npm run dev

# Create example requirements
bash scripts/setup_examples.sh

# Run tests
cd backend && pytest -v tests/

# View API docs
http://localhost:8000/docs

# Browse SQLite database
sqlite3 backend/app.db
  .tables
  SELECT * FROM requirement LIMIT 5;
```

---

## 📚 Reading Guide by Role

### For Hiring Manager / Evaluator
1. **ASSIGNMENT_README.md** (understand scope)
2. **ASSIGNMENT_DELIVERABLES.md** § 7 (evaluation matrix)
3. Try 2 scenarios: Greenfield + Ambiguous

### For Software Engineer
1. **ASSIGNMENT_DELIVERABLES.md** (full technical design)
2. **DEMO_GUIDE.md** (workflow walkthrough)
3. Explore backend code:
   - `/app/ai/prompts.py` (AI integration)
   - `/app/services/` (business logic)
   - `/app/api/routes/` (API design)

### For DevOps / Infrastructure
1. **ASSIGNMENT_README.md** (overview)
2. Check Docker/requirements setup
3. Review database schema
4. Understand validation sandbox (safe command execution)

### For QA / Testing
1. **ASSIGNMENT_DELIVERABLES.md** § 4 (testing approach)
2. **DEMO_GUIDE.md** (test scenarios)
3. Review `backend/tests/`
4. Try validation pipeline manually

---

## 🔑 Key Takeaways

1. **AI Assists, Engineer Decides**
   - AI generates recommendations
   - Engineer reviews and approves
   - Full decision record maintained

2. **Stable IDs Enable Traceability**
   - FR-001 → TASK-003 → ARTIFACT-001 → VALIDATION-001
   - Can trace any output back to original requirement

3. **Multiple Validation Gates**
   - Before plan generation (ambiguity resolution)
   - Before task execution (engineer approval)
   - Before artifact acceptance (validation pipeline)
   - Before final report (complete decision review)

4. **Three Requirement Types Supported**
   - Greenfield (new system) — no backward compatibility constraints
   - Brownfield (optimization) — backward compatibility + constraints
   - Ambiguous (vague) — requires clarification loop

5. **Production-Grade Quality**
   - Error handling with rollback
   - Safe command execution (no shell injection)
   - Audit trail of all decisions
   - Full transaction support

---

## ⚠️ Important Notes

- **AI Responses:** System uses Anthropic API (with fallback to mock data in demo mode)
- **Validation:** Python tests only (pytest). Adding JS/Go/Rust would require additional runners
- **Database:** SQLite for demo (PostgreSQL recommended for production)
- **Concurrency:** Single-engineer model (no conflict resolution)
- **Performance:** Suitable for 1-50 concurrent requirements (scale with database)

---

## 🎓 What You Learn From This

✅ How to structure AI-assisted workflows
✅ How to maintain engineer control with AI acceleration
✅ How to build robust validation pipelines
✅ How to track decisions and maintain audit trails
✅ How to decompose complex requirements into tasks
✅ How to handle ambiguity in specifications
✅ REST API design (OpenAPI)
✅ React + FastAPI integration patterns

---

**Next Step:** Open **ASSIGNMENT_README.md** and start exploring! 🚀
