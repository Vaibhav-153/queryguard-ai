# Final Portfolio Review

This review scores the **V2 codebase as packaged**, not the older live deployment. Scores are intentionally conservative where a dependency/provider could not be executed in the artifact-build environment.

| Area | Score / 10 | Evidence |
|---|---:|---|
| Problem clarity | 9 | Clear split between governed structured analytics, cited document Q&A, and invoice analysis |
| Role relevance | 9 | Python backend, GenAI, SQL, RAG, evaluation, security, deployment |
| Technical depth | 9 | Retrieval, AST governance, read-only boundary, workspaces, hybrid invoice flow |
| Code quality | 8 | Modular monolith, typed models, small explicit provider/loader modules, no unnecessary framework |
| Data quality | 8 | Reproducible Chinook demo, provenance/checksums, synthetic component sets clearly labeled |
| Evaluation | 8 | Independent schema/document/invoice component measurements; real-model execution benchmark remains to run |
| Testing | 7 | 43 deterministic tests pass in artifact runtime; 13 SQLGlot-dependent cases are skipped because SQLGlot cannot be installed in this container |
| Deployment readiness | 7 | Docker/Compose/Render/Streamlit files and health smoke exist; final V2 Docker/cloud deploy was not executed in this build environment |
| Documentation | 10 | Architecture, codebase, theory, setup, data, features, security, testing, deployment, interview and build guides |
| GitHub presentation | 9 | Recruiter README, sample files, CI, changelog, license, security policy, measured results |
| Interview readiness | 9 | Explicit design trade-offs, DSA/CS concepts, debugging/failure discussion, hiring/demo package |
| Target-role alignment | 9 | Strong GenAI Engineer / AI Engineer / Python Developer / Data Analyst overlap |
| Uniqueness | 9 | More than a PDF chatbot or basic Text-to-SQL demo; governed multi-source workflow is central |
| Feasibility for one graduate student | 8 | Uses understandable Python/open-source tools; scope remains a modular monolith |
| Honesty / claim discipline | 10 | Measured, synthetic, skipped and untested results are separated explicitly |

## Required improvements for scores below 8

### Testing — 7/10

**Weakness:** final SQLGlot AST and QueryService tests could not execute inside the artifact container because that dependency cannot be fetched from its blocked package index.

**Why it matters:** SQL governance is a core project claim.

**Affected files:**

- `tests/security/test_validator.py`
- `tests/integration/test_service.py`
- `tests/api/test_api.py`
- `src/queryguard/governance/validator.py`

**Required acceptance test after pushing to GitHub/Codespaces:**

```bash
pip install -e ".[ui,dev]"
ruff check app src tests scripts
pytest -v
```

Expected requirement: SQLGlot installs normally and **no SQLGlot test is skipped**. Any failure must be fixed before calling GitHub CI fully green.

### Deployment readiness — 7/10

**Weakness:** the final V2 Docker image, Render backend, and Streamlit UI were not deployed from this artifact environment.

**Why it matters:** configuration files can be structurally correct while a hosted runtime still exposes memory/cold-start/provider issues.

**Affected files:**

- `Dockerfile`
- `Dockerfile.ui`
- `docker-compose.yml`
- `render.yaml`
- `.streamlit/config.toml`
- `app/streamlit_app.py`

**Required acceptance tests:**

1. `docker compose up --build` on a Docker-enabled machine; `/health` returns V2 metadata.
2. Push to GitHub and confirm GitHub Actions is green.
3. Render Blueprint deploy succeeds with Gemini key + shared QueryGuard key.
4. Streamlit secrets point to the new Render URL and matching shared key.
5. Upload the bundled examples and verify Database/Spreadsheet/Documents/Invoices UI flows.

## Reviewer perspectives

### Recruiter

The repository communicates the value quickly and has an immediate Chinook demo plus synthetic upload examples. The README should remain concise while detailed learning material stays in `/docs`.

### Hiring manager

The strongest signal is that the LLM is surrounded by deterministic controls/evaluation rather than being the entire application. Be prepared to explain why multiple modes share infrastructure without sharing the wrong reasoning pipeline.

### Senior engineer

Expect questions about filesystem workspace limits, failure modes, SQLite concurrency, parser trust, provider abstractions, and why no queue/vector DB/microservices were added.

### Data/AI specialist

Do not present lexical Hit@K or synthetic invoice extraction as end-user answer accuracy. Discuss retrieval, execution match, semantic correctness, and the need for a real held-out domain evaluation.

### Security reviewer

Good demonstration controls exist, but this is not tenant-grade. The project correctly documents missing malware scanning, identity/RBAC, durable audit logs, encryption/KMS, per-user quotas, and production retention controls.

### End user

The UI should make mode choice, active provider, workspace state, evidence/governance, downloads, and manual-review flags visible. The user should never need to understand repository paths.

### Graduate candidate explaining the project

Lead with the problem and baseline, then explain the three depth features:

1. governed Text-to-SQL;
2. evidence-grounded document retrieval;
3. hybrid invoice analytics.

Do not start the interview explanation with a long list of libraries.
