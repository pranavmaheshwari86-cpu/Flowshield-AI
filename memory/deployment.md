# Flowshield — Deployment & Infrastructure Specification

---

## 1. Multi-Container Docker Compose Architecture

Flowshield includes a production-ready `docker-compose.yml` definition orchestrating three isolated services:

```yaml
services:
  db:
    image: postgis/postgis:16-3.4-alpine
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-flowshield}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-flowshield_secret}
      POSTGRES_DB: ${POSTGRES_DB:-flowshield_spatial}
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U flowshield -d flowshield_spatial"]
      interval: 10s
      timeout: 5s
      retries: 5

  api:
    build:
      context: .
      dockerfile: apps/api/Dockerfile
    environment:
      DATABASE_URL: postgresql://flowshield:flowshield_secret@db:5432/flowshield_spatial
      ENVIRONMENT: production
      LOG_LEVEL: INFO
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy

  web:
    build:
      context: apps/web
      dockerfile: Dockerfile
    ports:
      - "80:80"
    depends_on:
      - api
```

---

## 2. Dockerfiles & Container Builds

### 2.1 Backend API Container (`apps/api/Dockerfile`)
- **Base Image**: `python:3.10-slim`
- **System Dependencies**: `build-essential`, `libgdal-dev`, `libpq-dev`
- **Application Directory**: `/app`
- **ML Artifacts**: Mounts or copies `ml/artifacts/` into container image so `RealFloodPredictor` can load the trained XGBoost model and scaler.
- **Command**: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2`

### 2.2 Frontend Web Container (`apps/web/Dockerfile`)
- **Multi-Stage Build**:
  - *Stage 1 (Builder)*: `node:20-alpine`, runs `npm ci` and `npm run build` targeting `/app/dist`.
  - *Stage 2 (Server)*: `nginx:alpine`, copies built static assets to `/usr/share/nginx/html` and mounts `nginx.conf` for reverse-proxying `/api/` to the backend container.

---

## 3. Environment Variables Reference

| Variable Name | Default / Example | Purpose |
|---|---|---|
| `ENVIRONMENT` | `production` | Runtime mode (`development`, `staging`, `production`) |
| `DATABASE_URL` | `postgresql://...` or `sqlite:///./flowshield.db` | Connection URI for SQLAlchemy |
| `POSTGRES_USER` | `flowshield` | Database superuser |
| `POSTGRES_PASSWORD` | `flowshield_secret` | Database access credentials |
| `POSTGRES_DB` | `flowshield_spatial` | Database instance name |
| `JWT_SECRET` | `flowshield_super_secure_jwt_secret_key_2026` | Secret key for signing authority tokens |
| `JWT_ALGORITHM` | `HS256` | Cryptographic algorithm for JWT |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `720` (12 hours) | Token validity window |
| `CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | Comma-separated allowed frontend origins |
| `LOG_LEVEL` | `INFO` | Logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |

---

## 4. Production Deployment Checklist

1. [ ] Set strong, unique secrets for `POSTGRES_PASSWORD` and `JWT_SECRET` in `.env`.
2. [ ] Verify PostgreSQL health check passes: `docker compose ps`.
3. [ ] Verify ML artifacts exist: `ml/artifacts/xgboost_flood_model.json` and `ml/artifacts/feature_scaler.joblib`.
4. [ ] Run database migration and seed:
   ```bash
   docker compose exec api alembic upgrade head
   docker compose exec api python scripts/seed_db.py
   ```
5. [ ] Verify API health endpoint: `curl http://localhost:8000/api/v1/health`.
6. [ ] Verify AI model status endpoint: `curl http://localhost:8000/api/v1/ai/status`.
7. [ ] Verify web dashboard accessibility: `curl -I http://localhost/`.
8. [ ] Confirm CORS configuration restricts public write operations to approved domains.

---

## 5. Rollback & Fail-Safe Procedures

- **Database Rollback**: Migrations can be reverted step-by-step using Alembic:
  ```bash
  alembic downgrade -1
  ```
- **Container Rollback**: Previous container images are tagged with Git commit SHAs. In case of regression, point Compose image tags to the previous stable release.
- **Fail-Safe Offline Mode**: If connection to the PostGIS cluster fails, the backend logs a critical alert and can fall back to the embedded SQLite engine for local read operations.

Cross-references:
- Architecture: [`architecture.md`](./architecture.md)
- How to Run: [`how-to-run.md`](./how-to-run.md)
- Decisions: [`decisions.md`](./decisions.md)
