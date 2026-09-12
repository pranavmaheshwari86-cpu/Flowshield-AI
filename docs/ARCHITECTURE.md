# Flowshield — Architecture Documentation

## 1. System Topology

```mermaid
graph TD
    subgraph Client ["Client Presentation Layer (React + TS + Vite)"]
        UI_Dash["Authority Command Center (/dashboard)"]
        UI_Citizen["Citizen Warning App (/citizen)"]
        UI_GIS["Interactive GIS Map (Leaflet)"]
        UI_Sim["Simulation Controller"]
    end

    subgraph API ["FastAPI Modular Monolith (Port 8000)"]
        Router_Villages["/api/v1/villages"]
        Router_Map["/api/v1/map/geojson"]
        Router_Pred["/api/v1/predictions"]
        Router_Risk["/api/v1/risk"]
        Router_Alerts["/api/v1/alerts"]
        Router_Shelters["/api/v1/shelters"]
        Router_Sim["/api/v1/simulation"]
        
        Svc_Pred["PredictionService (XGBoost + SHAP)"]
        Svc_Risk["RiskEngine (Operational Formula)"]
        Svc_Alert["AlertEngine (Deduplication Lifecycle)"]
        Svc_Action["ActionEngine (Human-in-the-Loop Rules)"]
        Svc_Shelter["ShelterService (PostGIS ST_Distance)"]
        Svc_Route["RouteService (Flood Hazard Assessment)"]
        Svc_Sim["SimulationEngine (20 Substep State Machine)"]
    end

    subgraph Storage ["Persistent & Artifact Storage"]
        DB[(PostgreSQL 16 + PostGIS 3.4)]
        ModelArtifacts["ML Artifacts: xgb_flood_model.joblib & model_metadata.json"]
    end

    UI_Dash -->|REST JSON| API
    UI_Citizen -->|REST JSON| API
    
    Router_Pred --> Svc_Pred
    Router_Risk --> Svc_Risk
    Router_Alerts --> Svc_Alert
    Router_Shelters --> Svc_Shelter
    Router_Sim --> Svc_Sim
    
    Svc_Sim --> Svc_Pred
    Svc_Sim --> Svc_Risk
    Svc_Sim --> Svc_Alert
    Svc_Sim --> Svc_Action
    Svc_Sim --> Svc_Shelter
    Svc_Sim --> Svc_Route
    
    Svc_Pred --> ModelArtifacts
    API --> DB
```

## 2. End-to-End Data Pipeline Execution Sequence

1. **Environmental Observation**: Synthetic sensor reading or simulation step generates meteorological-hydrological vector for a settlement.
2. **Schema & Bounds Validation**: Vector verified against `FEATURE_SCHEMA` and `FEATURE_BOUNDS`.
3. **ML Inference**: `model.predict_proba()` calculates raw flood probability.
4. **Local Feature Attribution**: `shap.TreeExplainer` generates local attribution scores for all features, sorted into top positive/negative contributors.
5. **Operational Risk Assessment**: `RiskEngine` calculates 0–100 risk score incorporating ML probability, temporal trend multiplier, demographic vulnerability, and sensor quality/freshness caps.
6. **GIS Zone Update**: Voronoi catchment polygons for the settlement are styled with the new risk level color.
7. **Alert Evaluation**: If risk exceeds 50 (HIGH) or 75 (CRITICAL), the `AlertEngine` creates an active alert unless a deduplication key matches an existing active alert.
8. **Action Synthesis**: `ActionEngine` binds recommended decision-support guidelines with mandatory human-in-the-loop disclaimers.
9. **Shelter Nearest Evaluation**: `ShelterService` runs `ST_Distance` to return nearest relief facilities and adjust occupancy based on simulated evacuation intake.
10. **Route Risk Assessment**: `RouteService` evaluates designated evacuation corridors; segments crossing high river floodways are marked blocked.
11. **Citizen Broadcast**: `/citizen` displays plain-language warning status, safety checklist, and direct nearest-shelter directions.
