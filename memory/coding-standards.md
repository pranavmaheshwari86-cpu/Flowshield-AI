# Flowshield — Engineering & Coding Standards

---

## 1. Python & Backend Standards (`apps/api`, `ml/`)

### 1.1 Style & Formatting
- **PEP 8 Compliance**: Follow standard Python conventions (4-space indentation, 100-character line limit where practical).
- **Type Annotations**: Mandatory type hints on all public functions, service methods, and router endpoints. Use `typing.Optional`, `typing.List`, `typing.Dict`, and `typing.Any`.

### 1.2 Pydantic Validation & Schemas
- **Strict Separation**: Route inputs and responses must be governed by Pydantic models in `apps/api/app/schemas/`. Never expose raw SQLAlchemy model instances directly.
- **ORM Mode**: Configure `model_config = ConfigDict(from_attributes=True)` for seamless SQLAlchemy serialization.
- **Physical Bounds**: Feature schemas in `ml/feature_schema.py` must validate numeric bounds and clamp/reject out-of-physical-range telemetry.

### 1.3 Database & ORM Hygiene
- **Session Management**: Always inject database sessions using FastAPI's dependency injection: `db: Session = Depends(get_db)`.
- **Transaction Boundaries**: Commit write operations explicitly; keep sessions short-lived. Avoid long-running transactions across external HTTP calls.
- **Dialect Independence**: Write SQLAlchemy queries that work seamlessly on both PostgreSQL and SQLite. Use standard ANSI SQL operators or handle dialect branching in `app/database.py`.

### 1.4 Error Handling & Status Codes
- Raise `fastapi.HTTPException` with explicit status codes (`400`, `401`, `404`, `422`).
- Never suppress exceptions silently with bare `except: pass`. Always log errors with descriptive context.

---

## 2. TypeScript & Frontend Standards (`apps/web`)

### 2.1 Typing & Contract Safety
- **Strict TypeScript**: Keep `noImplicitAny: true` enabled. Avoid unconstrained `any` types; define explicit interfaces in `apps/web/src/types/index.ts`.
- **API Client Normalization**: The API wrapper (`apps/web/src/services/api.ts`) is responsible for normalizing backend responses into frontend-safe interfaces.

### 2.2 Component Architecture
- **Functional Components**: Use React 18 functional components with typed props (`React.FC<Props>`).
- **Hook Discipline**:
  - Always clean up intervals, event listeners, and timeouts in `useEffect` return functions.
  - Wrap stable callback handlers in `useCallback` when passed as props to prevent unnecessary re-renders.
- **State Segregation**: Keep global application state (user, system health) at the `App` root level; keep view-specific interaction state (selected village, drawer open) local to page containers.

---

## 3. Styling, Accessibility & Design System

### 3.1 CSS Tokens & Styling Paradigm
- **CSS Variables**: Use the tokens defined in `src/styles/tokens.css` for all colors, radii, transitions, and shadows. Never use ad-hoc hardcoded hex values in component styles.
- **Bespoke Classes**: Place reusable classes in `components.css` or `layout.css`. Avoid deeply nested inline CSS.

### 3.2 Accessibility (WCAG 2.1 AA Compliance)
- **Minimum Interactive Target**: All buttons and clickable icons must have at least a $44 \times 44\text{px}$ touch target area for mobile usability.
- **No Color-Alone Encoding**: Risk levels and alert tiers must always present text labels (e.g., `CRITICAL`) or distinct icons alongside color coding to assist colorblind responders.
- **High Contrast**: Ensure contrast ratios $\ge 4.5:1$ between text and background surfaces, especially on alert banners.

---

## 4. Machine Learning & Hydrological Pipeline Standards

- **Zero Data Fabrication**: Training datasets must strictly derive from verified public observational records (ERA5, IndoFloods, IMD/CWC catalogs). Fabricating synthetic positive events or random labels for training is strictly prohibited.
- **Leakage-Free Validation**: Temporal splitting and event-based holdout (`FloodEventHoldoutSplitter`) are mandatory. Never perform random k-fold splits across time series or within single storm events.
- **Reproducibility**: All preprocessing and model training scripts must declare and enforce deterministic seeds (`random_state = 26192`).
- **Cost-Sensitive Optimization**: Due to extreme flash flood event scarcity, classifiers must use inverse class weighting (`scale_pos_weight`) and calibrated decision thresholds ($\tau = 0.42$) rather than standard 0.50 cutoff.
- **Explainability & Fallback**: Every model prediction exposed to the API must include confidence metrics and fallback to hydrologic heuristics if inputs are out of distribution or artifacts are unavailable.
- **Statutory Disclaimers**: Machine learning outputs must always be labeled as decision-support aids with disclaimers indicating they do not replace official statutory meteorological warnings.

Cross-references:
- Architecture: [`architecture.md`](./architecture.md)
- Technology Stack: [`tech-stack.md`](./tech-stack.md)
- ADRs: [`decisions.md`](./decisions.md)
