# AI Engineering Workbench — Complete Demo Guide

## Quick Start (5 minutes)

### 1. Start Backend & Frontend
```bash
# Terminal 1: Backend
cd /Users/bputta/Documents/AI-PROJECT/ai-engineering-workbench/backend
source .venv/bin/activate
python -m app.cli serve
# Logs: "Application startup complete" → Ready on http://localhost:8000

# Terminal 2: Frontend  
cd /Users/bputta/Documents/AI-PROJECT/ai-engineering-workbench/frontend
npm run dev
# Open: http://localhost:5173
```

### 2. Create Example Requirements
```bash
# Terminal 3: Run setup script
cd /Users/bputta/Documents/AI-PROJECT/ai-engineering-workbench
bash scripts/setup_examples.sh
```

### 3. Try the Full Workflow

Open http://localhost:5173 in browser. You now have 3 example requirements ready:

---

## Complete Workflow Demo (15 minutes)

### Workflow: Requirement → Report

#### **Step 1: Select Greenfield Example**
1. Open dropdown "Select a project"
2. Choose: `REQ-001 — Build a scalable URL shortener service...`
3. Go to **Requirement** tab

**What you see:**
- Original text
- Status: "Unanalyzed"
- Button: "Analyze Requirement"

#### **Step 2: Analyze Requirement**
1. Click "Analyze Requirement"
2. Wait ~5 seconds for analysis (Azure OpenAI or mock response)
3. View results: Functional requirements (FR-001, FR-002, ...), Ambiguities, Constraints, etc.

**What's happening:**
- Backend calls Claude API (or mock data in demo mode)
- AI identifies scope boundaries, missing info, constraints
- System assigns stable IDs to each item (FR-*, NFR-*, AMB-*, etc.)

#### **Step 3: (Optional) Clarify Ambiguities**
If ambiguities exist (they should):
1. Go to Requirements tab, scroll to "Ambiguities"
2. Provide clarifications like:
   ```
   "Analytics: track daily clicks by country and device. 
   Retention: 1 year. Privacy: anonymize IPs after 30 days."
   ```
3. Click "Submit Clarifications"
4. View updated analysis with preserved IDs

#### **Step 4: Generate Engineering Plan**
1. Go to **Engineering Plan** tab
2. Click "Generate Plan"
3. Watch as AI decomposes into 5-15 tasks:
   - Architecture design
   - API design
   - Database schema
   - Backend implementation
   - Testing
   - Security review
   - Documentation
4. Each task has: sequence, dependencies, acceptance criteria, risk assessment

**What's happening:**
- AI reads analyzed requirement + prior decisions
- Produces structured tasks with clear execution order
- Marks up AI assistance type for each (CODE_GENERATION, TESTING, etc.)

#### **Step 5: Approve Tasks**
1. Go to **Tasks** tab
2. Click each task (left sidebar)
3. For each, click "Accept" (after reviewing)
4. Watch status change from "PENDING" → "APPROVED"

**What's happening:**
- Engineer reviews AI-suggested decomposition
- Can Modify tasks or Reject them
- Each decision is recorded

#### **Step 6: Request AI Assistance**
1. Tasks appear as cards below each task detail
2. Select "AI Assistance type" dropdown:
   - CODE_GENERATION (for main code)
   - TEST_GENERATION (for tests)
   - DOCUMENTATION
   - SECURITY_REVIEW
   - PERFORMANCE_REVIEW
3. Add optional instructions, click "Request AI Assistance"
4. See AI Run card appear with:
   - Recommendation summary
   - Approach
   - Proposed changes
   - Tests to add
   - Risks & assumptions
   - Confidence score

**What's happening:**
- Task context sent to Claude with clear scope
- AI generates structured recommendation (not code yet)
- Engineer reviews before approval

#### **Step 7: Accept & Generate Artifacts**
1. On AI Run card, click "Accept"
2. Status changes to "ACCEPT"
3. "Generate Artifacts" button appears
4. Click it
5. Wait ~5 seconds for code generation
6. Go to **Artifacts** tab to see generated files:
   - ARTIFACT-001: Integration test file (test_*.py)
   - ARTIFACT-002: Configuration file (package.json, etc.)
   - ARTIFACT-003: API contract (OpenAPI schema)

**What's happening:**
- Accepted recommendation sent to Claude for code generation
- AI generates actual file content (Python test code, configs, etc.)
- System validates paths (no ../../../ etc.)
- Artifacts stored with version history

#### **Step 8: Validate Artifacts**
1. On each artifact, see validation results:
   - **BUILD**: ✅ PASSED (import check)
   - **UNIT_TEST**: ? (pytest on test files)
   - **INTEGRATION_TEST**: ? (pytest integration)
   - **STATIC_ANALYSIS**: ? (ruff check)
   - **API_CONTRACT**: ? (OpenAPI schema validation)
   - **SECURITY**: ? (secret pattern scan)

2. Failed validations show error messages
3. Click "Run new validation" to re-run specific type

**What's happening:**
- Validation runner executes hardcoded, allowlisted commands
- Results stored with timestamp, duration, output
- Engineer sees evidence (e.g., "24 tests passed in 0.45s")

#### **Step 9: Engineer Review**
1. On each artifact, click "Accept" or "Reject"
2. For artifacts with issues, click "Reject" with rationale
3. Example: "ARTIFACT-001 fails unit tests — need setup.py with dependencies"

**What's happening:**
- Engineer decision recorded
- Artifact status: AI_RECOMMENDED → ENGINEER_REVIEW → ACCEPTED/REJECTED

#### **Step 10: Generate Final Report**
1. Go to **Final Report** tab
2. See complete summary:
   - Original requirement
   - All engineer decisions (by scope: task, AI run, artifact)
   - Implementation summary
   - Generated artifacts (names, types, versions)
   - Validation summary (passed/failed/not validated)
   - Risks identified
   - Assumptions made
   - Limitations & unresolved ambiguities

3. Click "Export as Markdown" to download complete report

**What's happening:**
- System compiles all metadata into structured report
- Markdown export useful for documentation/audits
- Demonstrates full audit trail

---

## Try the Other Scenarios

### Scenario B: Brownfield (Performance Optimization)
1. Select `REQ-008 — Optimize the URL shortener's...`
2. Follow same workflow, notice:
   - Plan includes optimization-specific tasks (index design, load testing)
   - AI recommendations focus on refactoring, not new features
   - Tests validate performance metrics, not new functionality

### Scenario C: Ambiguous (Analytics)
1. Select `REQ-009 — Add analytics to the shortener...`
2. **After analysis, ambiguities appear:**
   - "What events to track?"
   - "What insights matter?"
   - "Storage/retention?"
   - "Privacy constraints?"
   - "Scale requirements?"
3. **Provide clarifications:**
   ```
   "Track daily clicks. By country and device type. 
   Retain 1 year. GDPR: anonymize IP after 30 days. 
   Expected 50k-500k events/day."
   ```
4. **Observe:**
   - IDs preserved (FR-001 stays FR-001)
   - Ambiguities marked as RESOLVED, removed from list
   - Plan regenerates with concrete tasks
   - Full workflow proceeds

---

## Key Features to Observe

### 1. **Stable ID Preservation**
- Requirement analysis: FR-001, FR-002, etc.
- After clarifications: Same FR-* IDs persist
- Plan references FR-001, TASK-003, etc.
- Full traceability across workflow

### 2. **Multi-Stage Validation**
- Tests appear only after artifact generation
- BUILD validation passes (app boots)
- TEST validations run pytest (may fail if tests incorrect)
- Engineer sees NOT_VALIDATED ≠ PASSED

### 3. **Engineer Control Points**
```
Requirement Creation
  ↓ Engineer reviews ambiguities
Clarifications (optional)
  ↓ Engineer reviews plan
Engineering Plan
  ↓ Engineer accepts/modifies tasks
Tasks
  ↓ Engineer requests AI assistance
AI Recommendations
  ↓ Engineer accepts/rejects
Artifact Generation
  ↓ Engineer reviews artifacts
Validation
  ↓ Engineer approves/rejects
Final Artifacts
  ↓
Final Report
```

### 4. **Decision Tracking**
Every decision recorded in Final Report:
- Which ambiguities engineer clarified
- Which tasks approved
- Which AI recommendations accepted/rejected
- Which artifacts approved/rejected
- All with rationales

---

## Understanding the Database Model

```
Requirement
  ├─ RequirementAnalysis (analysis result)
  └─ EngineeringPlan
     ├─ EngineeringTask (10+ tasks per plan)
     │  ├─ EngineerDecision (task approve/modify/reject)
     │  └─ AIRun (one or more per task)
     │     ├─ EngineerDecision (accept/modify/reject recommendation)
     │     └─ Artifact (code, tests, docs, etc.)
     │        ├─ EngineerDecision (approve/reject artifact)
     │        └─ Validation (unit test, integration, build, security, etc.)
     └─ EngineerDecision (approve/reject plan)
```

Each entity has:
- **Public ID** (REQ-001, TASK-003, ARTIFACT-001, VALIDATION-002)
- **Status** (PENDING, APPROVED, REJECTED, NEEDS_REVISION, etc.)
- **Timestamp** (created_at)
- **Audit trail** (who, when, rationale)

---

## Troubleshooting

### "No tests ran" in validation
**Cause:** Generated test file is malformed or not Python
**Fix:** Check artifact ARTIFACT-001 content
- Should be Python (pytest) format
- Must have functions prefixed with `test_`
- Should be in `tests/` directory
**Solution:** Regenerate artifact or manually edit test file

### API returns 404 on task operations
**Cause:** Task not approved yet
**Fix:** Go to Tasks tab, approve task with "Accept" button first

### Final Report is empty
**Cause:** No tasks completed yet
**Fix:** Complete the workflow: Approve task → Request assistance → Accept recommendation → Generate artifacts

### Backend won't start
**Cause:** Port 8000 in use, or database locked
**Fix:**
```bash
# Kill process on port 8000
lsof -i :8000 | grep LISTEN | awk '{print $2}' | xargs kill -9

# Or reset database
rm backend/app.db
```

---

## Files to Know

| File | Purpose |
|------|---------|
| `ASSIGNMENT_DELIVERABLES.md` | Complete assignment response |
| `DEMO_GUIDE.md` | This file — step-by-step walkthrough |
| `backend/app/main.py` | FastAPI entry point |
| `backend/app/ai/prompts.py` | AI prompts (requirement analysis, planning, assistance, artifacts) |
| `frontend/src/screens/` | React components (Requirement, Plan, Tasks, Artifacts, Report) |
| `backend/app/services/` | Business logic (analyzers, decomposers, generators, validators) |
| `scripts/setup_examples.sh` | Populate example requirements |

---

## What's Demonstrated

✅ **Effective AI Use**
- AI analyzes complex requirements
- AI decomposes into structured plans
- AI generates code + tests + documentation
- AI provides reasoning + confidence scores

✅ **Engineer Ownership**
- Engineer clarifies ambiguities
- Engineer reviews & approves plans
- Engineer accepts/rejects AI recommendations
- Engineer validates all outputs

✅ **Rigorous Validation**
- 7-stage validation pipeline (unit, integration, static, security, API, build, performance)
- Failed validations block approval
- Full validation history recorded

✅ **Production Ready**
- Stable schema with migrations
- Error handling + rollback on failure
- API contracts (OpenAPI)
- Audit trail of all decisions

---

## Next Steps

1. **Try different workflows:**
   - Create your own requirement
   - Walk through full cycle
   - Modify AI recommendations
   - Reject artifacts and regenerate

2. **Explore the API:**
   - Open http://localhost:8000/docs
   - Try endpoints directly
   - See request/response schemas

3. **Examine the Database:**
   ```bash
   sqlite3 backend/app.db
   .tables
   .schema requirement
   SELECT * FROM requirement LIMIT 5;
   ```

4. **Extend the System:**
   - Add new validation types (Jest for JavaScript, etc.)
   - Add new artifact types
   - Add team collaboration features
   - Integrate with Git for artifacts

---

**Enjoy exploring AI-assisted engineering!** 🚀
