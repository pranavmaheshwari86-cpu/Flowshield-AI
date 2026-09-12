# Flowshield — Code Review Knowledge Graph (.code-review-graph)

**Last Updated**: September 2026 (v4.1.0 — Direct Command Center Routing & Multi-Region Machine Learning Architecture)  
**Graph Database**: [`graph.db`](file:///c:/Users/Pranav/Desktop/Flowshield/.code-review-graph/graph.db) (28.4 MB SQLite knowledge graph)  
**Graph Engine**: OpenCode Code-Review-Graph MCP (`tree-sitter`, AST parsing, Louvain/Leiden community detection)  

---

## 1. Graph Statistics Summary

- **Files Parsed**: 385 source files
- **Total Graph Nodes**: 1,612 nodes (functions, classes, modules, interfaces, routes, components)
- **Total Graph Edges**: 22,176 edges (`CALLS`, `IMPORTS`, `DEFINES`, `EXTENDS`, `REFERENCES`)
- **Full-Text Search (FTS) Entries**: 1,581 indexed code symbols
- **Execution Flows Detected**: 136 distinct end-to-end execution paths
- **Architectural Communities**: 18 modular subsystem clusters

---

## 2. Detected Architectural Communities

| Community ID | Subsystem Name | Size (Nodes) | Cohesion Score | Dominant Language | Primary Concern |
|---|---|---|---|---|---|
| `community-44` | `services-risk` | 600 | 0.1404 | Python | Backend services, timeline engine, multi-horizon forecasts, risk engine, hazard routing, alert engine, 17 FastAPI routers |
| `community-45` | `types-props` | 240 | 0.2161 | TypeScript / TSX | React UI (Command Center / Dashboard, TimelineView, ResponderPage, CitizenWarning), modular timeline components, hooks, Leaflet GIS overlays, direct Command Center entry |
| `community-47` | `09-dashboard-risk` | 85 | 0.0827 | Python | Regional experiments, calibration runs, and model selection studies |
| `community-55` | `models-model` | 54 | 0.0469 | Python | ML core library (`ml/src/data`, `ml/src/evaluation`, `ml/src/models`) |
| `community-52` | `registry-load` | 42 | 0.2639 | Python | Multi-Region Model Registry, schema hashing, and FeatureContract guards |
| `community-61` | `tests-db` | 37 | 0.0000 | Python | Comprehensive integration, adversarial telemetry, and chaos test suites |
| `community-50` | `pipeline-region` | 32 | 0.0402 | Python | IndoFloods ingestion, regional event filtering, and calibration pipelines |
| `community-59` | `scripts-compute` | 24 | 0.0182 | Python | Operational scripts, real ERA5/Open-Meteo data collection, and historical inventory |
| `community-48` | `inference-compute` | 20 | 0.0856 | Python | Real ML inference pipeline, artifact loading, TreeSHAP explainability |
| `community-56` | `tests-feature` | 20 | 0.0054 | Python | ML feature testing, schema bounds, and coordinate validation |
| `community-58` | `scratch-region` | 19 | 0.0588 | Python | Regional data acquisition utilities and audit engines |
| `community-57` | `training-compute` | 14 | 0.0199 | Python | Automated calibration, tournament evaluation, and threshold optimization |
| `community-54` | `scripts-parse` | 9 | 0.0444 | Python | Model promotion, rollback, and pipeline automation CLIs |
| `community-49` | `legacy-v1-evaluate` | 5 | 0.0162 | Python | Archived legacy baseline training pipelines |
| `community-60` | `migrations-migrate` | 5 | 0.0000 | Python | Database migration scripts (`migrate_v2_4_*.py`) |
| `community-51` | `preprocessing-load` | 4 | 0.0968 | Python | Leak-free data loading, event holdout splitting, standard scaling |
| `community-46` | `evaluation-evaluate` | 2 | 0.0125 | Python | Threshold sweep and false-negative rate safety evaluation |
| `community-53` | `retraining-retrain-pipeline` | 2 | 0.0132 | Python | Automated retraining pipeline with data drift detection |

---

## 3. Subsystem Wiki Documentation (`wiki/`)

Detailed architectural markdown pages generated for detected communities:
- [`wiki/index.md`](file:///c:/Users/Pranav/Desktop/Flowshield/.code-review-graph/wiki/index.md): Subsystem index and navigation hub.
- [`wiki/services-risk.md`](file:///c:/Users/Pranav/Desktop/Flowshield/.code-review-graph/wiki/services-risk.md): Backend routing, timeline engine, risk engine, alert engine, and simulation machine.
- [`wiki/types-props.md`](file:///c:/Users/Pranav/Desktop/Flowshield/.code-review-graph/wiki/types-props.md): Frontend component tree, command center direct entry point, timeline workspace, responder console, and TypeScript contracts.
- [`wiki/registry-load.md`](file:///c:/Users/Pranav/Desktop/Flowshield/.code-review-graph/wiki/registry-load.md): Multi-Region Model Registry and feature contracts.
- [`wiki/inference-compute.md`](file:///c:/Users/Pranav/Desktop/Flowshield/.code-review-graph/wiki/inference-compute.md): Real ML model loading and inference logic.
- [`wiki/training-compute.md`](file:///c:/Users/Pranav/Desktop/Flowshield/.code-review-graph/wiki/training-compute.md): ML model training routines and calibration.
- [`wiki/preprocessing-load.md`](file:///c:/Users/Pranav/Desktop/Flowshield/.code-review-graph/wiki/preprocessing-load.md): Data scaling, imputation, and event holdout splits.
- [`wiki/retraining-retrain-pipeline.md`](file:///c:/Users/Pranav/Desktop/Flowshield/.code-review-graph/wiki/retraining-retrain-pipeline.md): Model retraining and drift evaluation.
