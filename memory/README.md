# Flowshield Project Memory & Documentation Infrastructure

This directory (`memory/`) serves as the single source of truth for Flowshield's architecture, domain rules, API contracts, data models, decisions, operational workflows, and active status. It is designed to preserve project continuity across AI pair-programming sessions and engineering iterations.

---

## 1. Directory Structure & Responsibilities

| File | Purpose & Responsibility |
|---|---|
| [`project-overview.md`](./project-overview.md) | High-level purpose, problem statement (SIH 2026 PS ID 26192), target geography, personas, and system scope. |
| [`architecture.md`](./architecture.md) | System architecture, modular monolith design, subsystem boundaries, data flow pipelines, and GIS topology. |
| [`tech-stack.md`](./tech-stack.md) | Verified frameworks, libraries, versions, runtimes, and dependencies actually used across backend, ML, and frontend. |
| [`api.md`](./api.md) | Comprehensive REST API catalog, endpoint contracts, schemas, authentication, query parameters, and error formats. |
| [`database.md`](./database.md) | Database schemas, SQLAlchemy models, spatial relationships, SQLite/PostGIS dual-engine design, and seed datasets. |
| [`business-rules.md`](./business-rules.md) | Hydrological physical bounds, ML vs. operational risk formulas, alert thresholds, shelter capacity rules, and SOPs. |
| [`decisions.md`](./decisions.md) | Architectural Decision Records (ADRs) detailing trade-offs, evaluated alternatives, and engineering rationale. |
| [`coding-standards.md`](./coding-standards.md) | Project coding standards, naming conventions, error handling protocols, typing requirements, and UI/UX rules. |
| [`current-status.md`](./current-status.md) | Up-to-date execution status, completed deliverables, passing test suites, and verified deployment state. |
| [`how-to-run.md`](./how-to-run.md) | Step-by-step local setup, environment variables, commands, background services, and demo presentation sequence. |
| [`deployment.md`](./deployment.md) | Docker Compose multi-container setup, production configurations, Nginx routing, and containerization procedures. |
| [`module-government-ids.md`](./module-government-ids.md) | Authority credentials, role-based access, citizen ID safeguarding during evacuation, and DigiLocker/MeriPehchaan roadmap. |
| [`production-implementation-spec.md`](./production-implementation-spec.md) | Production hardening criteria, latency budgets, fail-safe fallbacks, data freshness SLAs, and accessibility rules. |
| [`bugs.md`](./bugs.md) | Known issues, resolved bugs, test-isolation resolutions, environment caveats, and operational mitigations. |
| [`changelog.md`](./changelog.md) | Chronological log of key development phases, commits, architectural refactors, and model training milestones. |
| [`todo.md`](./todo.md) | Prioritized backlog of post-hackathon enhancements, edge integrations, hardware telemetry, and feature expansions. |

---

## 2. When to Read Each File

- **Before Planning or Implementing Any Feature**: Read [`current-status.md`](./current-status.md), [`architecture.md`](./architecture.md), and [`business-rules.md`](./business-rules.md).
- **Before Modifying or Adding Backend Routes**: Read [`api.md`](./api.md), [`database.md`](./database.md), and [`coding-standards.md`](./coding-standards.md).
- **Before Modifying Machine Learning or Telemetry Code**: Read [`business-rules.md`](./business-rules.md) and [`tech-stack.md`](./tech-stack.md).
- **Before Refactoring or Making Structural Decisions**: Read [`decisions.md`](./decisions.md) and [`architecture.md`](./architecture.md).
- **When Fixing Errors or Running Tests**: Read [`bugs.md`](./bugs.md) and [`how-to-run.md`](./how-to-run.md).
- **When Preparing Demos or Evaluating System Health**: Read [`how-to-run.md`](./how-to-run.md) and [`current-status.md`](./current-status.md).

---

## 3. When and How to Update Memory Files

To prevent documentation decay, update these files during the task lifecycle:
1. **When an architectural decision is made**: Document the problem, chosen approach, alternatives considered, and consequences in [`decisions.md`](./decisions.md).
2. **When an API route is added, changed, or removed**: Update [`api.md`](./api.md) with parameters, request/response bodies, and HTTP status codes.
3. **When a database model or migration is modified**: Update [`database.md`](./database.md) with table columns, indexes, and foreign keys.
4. **When a bug is discovered or resolved**: Log the symptom, root cause, reproduction, and resolution in [`bugs.md`](./bugs.md).
5. **When completing a milestone or feature**: Update [`current-status.md`](./current-status.md), [`changelog.md`](./changelog.md), and strike out tasks in [`todo.md`](./todo.md).

---

## 4. Documentation Maintenance Rules

1. **Evidence-Based Facts Only**: Derive all documentation from actual code, config files, model metrics, and database tables. Never speculate or state assumptions as facts.
2. **Concise and Scannable**: Use tables, bulleted lists, code blocks, and mathematical formulas instead of unstructured prose.
3. **Cross-Referenced**: Use relative Markdown links between related files (e.g., linking from [`api.md`](./api.md) to [`business-rules.md`](./business-rules.md)).
4. **Integrity and Preservation**: Never overwrite existing verified entries blindly. Append or merge new verified findings.

---

## 5. Sibling Memory & Graph Infrastructure

Flowshield couples this human-readable `memory/` catalog with automated structural graph systems:
- [`../code-review-graph/`](file:///c:/Users/Pranav/Desktop/Flowshield/code-review-graph/README.md) & [`.code-review-graph/`](file:///c:/Users/Pranav/Desktop/Flowshield/.code-review-graph/README.md): Automated code knowledge graph (3,588 nodes, 27,904 edges, 10 communities, 11 wiki articles, and OWASP audit findings).
- [`../graphify-out/`](file:///c:/Users/Pranav/Desktop/Flowshield/graphify-out/README.md): Visual architecture assets including Mermaid dependency graphs, subsystem interaction matrices, and API call graphs.
- [`../walkthrough.md`](../walkthrough.md): Comprehensive production walkthrough, test evidence, and embedded browser screenshots.
- [`../data/real/DATASET_PROVENANCE.md`](file:///c:/Users/Pranav/Desktop/Flowshield/data/real/DATASET_PROVENANCE.md): Strict provenance records for verified public meteorological and hydrological datasets.

