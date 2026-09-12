# Flowshield Graphify Architecture & Dependency Assets

**System Version**: 4.0.0 (Predictive Risk & Multi-Horizon Timeline)  
**Smart India Hackathon 2026** (Problem Statement ID: 26192)  
**Last Updated**: September 2026

This directory contains system architecture graphs, cross-subsystem dependency matrices, and call graphs generated for the Flowshield multi-hazard flash flood and landslide early warning and decision support system.

---

## 1. Directory Contents

| File | Type | Description |
| :--- | :---: | :--- |
| [`dependency-graph.mermaid`](file:///c:/Users/Pranav/Desktop/Flowshield/graphify-out/dependency-graph.mermaid) | Mermaid | High-level system architecture showing Client Layer, Timeline Workspace, API Gateway, Multi-Hazard Services, ML Subsystem, Persistence, and Telemetry Layers. |
| [`subsystem-dependency-matrix.md`](file:///c:/Users/Pranav/Desktop/Flowshield/graphify-out/subsystem-dependency-matrix.md) | Markdown | Interaction matrix mapping coupling strength, communication protocols, and architectural invariants across subsystems. |
| [`api-call-graph.md`](file:///c:/Users/Pranav/Desktop/Flowshield/graphify-out/api-call-graph.md) | Markdown | End-to-end trace from HTTP requests across all 17 routers to domain handlers, database queries, and ML model invocations. |
| [`architecture-graph.json`](file:///c:/Users/Pranav/Desktop/Flowshield/graphify-out/architecture-graph.json) | JSON | Machine-readable node and edge specifications, community IDs, canonical feature catalog, and endpoint inventories. |

---

## 2. Subsystems at a Glance

```text
┌─────────────────────────────────────────────────────────────┐
│                    Web Client (React / Vite)                │
│     Command Center · Predictive Timeline · Responder Console│
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTP / SSE / RBAC Auth
┌──────────────────────────────▼──────────────────────────────┐
│                  FastAPI Backend Gateway                    │
│ 17 Routers: Forecast, Hazards, Routes, Alerts, Sim, AI, etc │
└──────────────┬───────────────────────────────┬──────────────┘
               │ In-Memory Python Calls        │
┌──────────────▼──────────────┐ ┌──────────────▼──────────────┐
│    Multi-Hazard Services    │ │    ML Subsystem (ml/)       │
│ Timeline, Risk, Landslide,  │ │  Calibrated Risk Classifier │
│ Route Solver & Alert Engine │ │  Multi-Horizon +1h to +48h  │
└──────────────┬──────────────┘ └──────────────┬──────────────┘
               │                               │
┌──────────────▼──────────────┐ ┌──────────────▼──────────────┐
│  Relational DB (PostGIS)    │ │   Verified Real Data (data/)│
│ Dual Engine: SQLite/Postgres│ │   ERA5 10-Yr & CWC Telemetry│
└─────────────────────────────┘ └─────────────────────────────┘
```

---

## 3. How to Render and Use

* **Mermaid Graphs**: Can be previewed directly in VS Code / Antigravity Markdown Preview or rendered using GitHub/GitLab natively.
* **JSON Metadata**: Can be consumed by automated CI/CD dependency checkers or security scanning scripts.
* **Complementary Graph Data**: For detailed abstract syntax tree (AST) code nodes and Louvain community clusters, inspect [`code-review-graph/`](file:///c:/Users/Pranav/Desktop/Flowshield/code-review-graph/README.md).
