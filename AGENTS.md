# AGENTS.md — Autonomous Engineering Operating Manual (v3)

> Supersedes v1 and v2. Same architecture, re-scoped: global rules are now
> genuinely global (cheap, universal), everything else is stage-conditional.
> No skill, MCP, or agent runs "just because it's on the list" — every entry
> below has an explicit trigger and an explicit skip condition. v3 adds a
> second wave of skills (token/context savers, planners, execution/quality,
> security/shipping, DevOps) plus the `sequential-thinking` MCP and the
> `caveman` family — each run through the same overlap/merge audit as v2,
> not just appended (see §0.1).

---

## 0. Audit Summary — What Changed From v1 and Why

| Item | v1 behavior | v2 behavior | Reason |
|---|---|---|---|
| `ponytail` | Always-on global | Merged into **Review Stage** as a shared quality baseline | It only applies to code; running it on non-code answers wasted tokens. Overlapped with `vibe-code-auditor` / `code-reviewer` / `bugs-are-annoying`. |
| `ruflo` (MCP) | Always-on global | Stage-conditional: **Investigation** (memory/business-rule lookup) + **Automation** (workflow execution) | "Orchestration + memory" is two different jobs already covered by Steps 1–6 and the `memory` resource. Keeping it global duplicated the protocol's own logic. |
| `agency-agents` | Always-on global, vague ("alongside every task") | Triggered only when Step 2 finds **independent, parallelizable sub-tasks** | This is literally Step 4's parallel-execution branch. Making it global meant paying for a dispatcher even on single-threaded tasks. |
| `memory` / `graphify-out` / `.code-review-graph` | View before + update after *every* task | View before **Investigation Stage**; update after any stage that **modified code or made an architectural decision** | A pure Q&A turn has nothing to log and nothing to look up. |
| `writing-plans` | Not present in v1 | New global gate, but only for **non-trivial** tasks (multi-file, architectural, or destructive) | Added per spec — planning is mandatory before implementation, not before "what does this function do?" |
| `token-saver` / `verification-before-completion` / `safety-guardrails` | Always-on | **Unchanged** — kept global | These are pure discipline checks with ~zero token cost and no code-dependency. They're the only things that earn "always-on." |

Net effect: fewer skills fire on trivial requests, no two skills do the same job in the same turn, and every capability below has a concrete "when NOT to run" clause.

### 0.1 v3 Addendum — Round 2 Additions (new skills, `sequential-thinking` MCP, `caveman` family)

Same rule as v2: nothing gets appended without being checked for overlap first. Three of these turned out to be a real gap in v2 (restored, not new); the rest are genuinely new capabilities or merges.

| New Capability | Type | Decision | Rationale |
|---|---|---|---|
| `opencode-token-optimization` | SK | **MERGE/REPLACE** `token-saver` | Deploys TOE v2 (Token Optimization Engine). Supersedes the basic `token-saver` with a global cognitive framework governing input, output, reasoning, and tool-call token efficiency. |
| `context-optimizer` | SK | **Restored to Global Layer** | This was in v1's original always-on table ("Context Optimizer — run before every model call") and was dropped by mistake in v2. Per-call context pruning is cheap and universal — it belongs alongside `opencode-token-optimization`. |
| `memory-history` | SK | **Restored to Global Layer**, coupled with the `memory` resource | Matches v1's "Memory/History" global row. `memory-history` is the skill that manages the cache; `memory` (§5) remains the underlying data store it reads/writes. |
| `session-persistence` | SK | **Restored to Global Layer** | Matches v1's "Session Persistence" global row. Cheap rehydration check that skips expensive re-discovery — same cost profile as the other globals. |
| `sequential-thinking` (MCP) | MCP | **Add, cross-stage** — not owned by one stage | Triggered whenever Planning, Architecture, Debugging root-cause, or Security threat-modeling work is high-complexity/ambiguous. Distinct from `writing-plans`: this is the reasoning process, `writing-plans` is the resulting artifact. They feed each other, not compete. |
| `opencode-architecture-planning` | SK | **MERGE** — becomes the Planning-stage umbrella | Overlaps `software-architecture` / `backend-architect` / `frontend-architect`. Those three become its domain-specific lenses instead of three independent structural passes that could disagree with each other. |
| `senior-architect` | SK | **Add, cross-stage advisory** (Planning *and* Review) | A second-opinion check plugged into two existing checkpoints (structure decisions in Planning, structural integrity in Review) rather than a full standalone pass that re-does the same analysis. |
| `tdd-workflow` | SK | **Add to Development** | No existing overlap — genuinely new discipline (test-first implementation). |
| `opencode-bug-detection` | SK | **Add to Review**, sequenced *before* `bugs-are-annoying` | Both hunt logic flaws, but this one is static/mechanical (pre-runtime patterns) while `bugs-are-annoying` is semantic (race conditions, business-logic edge cases). Running the mechanical pass first narrows what the deeper pass needs to look at, instead of two independent full re-reads. |
| `debugging-toolkit-smart-debug` | SK | **REPLACES** `debugging-toolkit` | Same slot in the `systematic-debugging` hierarchy, upgraded capability (structured resolution path on test failure vs. generic tool actions). Keeping both would be a pure duplicate — v2's `debugging-toolkit` entry is retired. |
| `opencode-refactoring` | SK | **MERGE** into Cleanup stage alongside `vibe-code-cleanup` | Cleanup is subtractive (dead code/imports/duplication removal); refactoring is transformative (DRY restructuring). Run as two sub-phases of *one* Cleanup pass, not two independent scans of the same code. |
| `differential-review` | SK | **Add to Security**, scoped to routine PR-level diffs | Overlaps `security-audit`/`vulnerability-scanner`, but this is the fast default gate on every PR; the full `security-audit` is reserved for higher-risk changes (new attack surface, auth changes). Prevents running the heavy audit on every trivial PR. |
| `pr-writer` | SK | **Add to Git/Deployment-prep** | Distinct job from `code-reviewer` (writes descriptions vs. reviews code) — no overlap. |
| `aws-cost-cleanup` | SK | **Add to Deployment/Background Maintenance**, manual/periodic | Distinct cost-hygiene task, no existing overlap. |
| `open-deep-research` | SK | **Add to Investigation**, scoped to unfamiliar/novel tech | Distinct from `vexor-cli` (internal code search) — this is external research for things the codebase itself can't answer (e.g. a brand-new framework version), specifically to prevent hallucinated API usage. |
| `caveman` | SK | **MERGE** — becomes the Background Maintenance compression *engine* | Same job as v2's `context-compression`. `context-window-management` keeps its monitoring role; `caveman` now does the actual compressing it triggers. |
| `caveman-compress` | SK | **MERGE** into `memory-history` as its compression engine | Directly matches `memory-history`'s stated job (avoid re-reading/re-summarizing giant docs every session). |
| `caveman-commit` | SK | **Add to Git stage** | Distinct granularity (commit message) from `pr-writer` (PR description) — no overlap. |
| `caveman-review` | SK | **Add as a large-diff output MODE for Review stage**, not a parallel skill | On large PRs, `vibe-code-auditor`/`bugs-are-annoying`/`code-reviewer` emit one-line-per-finding instead of full prose. Same review depth, cheaper output — this is a format toggle, not a fifth reviewer. |
| `caveman-stats` | SK | **Add, manual/optional only** | Per your own rating, token savings here are *estimated, not measured* — kept off auto-run so it's never reported as a verified number. |
| `cavecrew` | SK | **MERGE** — becomes `agency-agents`'s inter-stream communication protocol | Same problem (multi-agent token waste) as `agency-agents`'s parallel dispatch. Coupled to it rather than run as an independent skill that might fire without a parallel session to govern. |

Full integration of every row above (trigger/skip conditions, stage placement, roster table, auto-run rules) is in §3, §5, §6, and §7 below.

---

## 1. Design Principles

1. Every capability has exactly one owner and one clearly bounded job.
2. Nothing loads speculatively. Step 3's selection is mandatory and explicit every turn.
3. Global = cheap + universal. Anything code-dependent or session-dependent is stage-scoped, not global.
4. Overlapping skills are resolved once, here, not re-litigated per task (see §6).
5. Verification is never skipped, but its *cost* scales with task risk — a typo fix and a schema migration do not get the same QA pass.

---

## 2. Execution Protocol

### Step 1 — Task Classification (replaces blanket "capability discovery")
Classify the request along two axes before touching anything else:
- **Triviality**: trivial (single fact, single small edit, no architecture impact) vs. non-trivial (multi-file, new feature, security/data-model change, irreversible action).
- **Code-touching**: does this task read/write repository code, or is it pure conversation/analysis?

This classification gates almost everything downstream — it's the cheapest possible check and it prevents the rest of the protocol from over-firing.

### Step 2 — Task Analysis
Break the task into: primary goal → required sub-tasks → type of each sub-task (planning / investigation / implementation / debugging / review / security / QA / deployment). Flag which sub-tasks are independent (parallelizable) vs. dependent (sequential).

### Step 3 — Mandatory Capability Selection (before execution)
Match each sub-task to the **most specific** skill/MCP/agent in the Capability Roster (§5). Never load the full registry. Output the selection line before execution:

```
[STAGE(S): ...] [SKILLS SELECTED: ...] [MCPs SELECTED: ...] [AGENTS SELECTED: ... | NONE] [FALLBACK: general-assistant | N/A]
```

### Step 4 — Execution
Run independent sub-tasks in parallel (via `agency-agents` if more than one genuinely independent stream exists — see §5), dependent sub-tasks sequentially, in stage order (§4).

### Step 5 — Verification & Fallback
`verification-before-completion` runs regardless of task size — no exceptions — but its depth scales: a trivial task gets a self-check; a non-trivial task gets the full QA/Security stages before anything is called "done." On failure, report exactly what failed and fall back to a direct, unassisted approach.

### Step 6 — Code Review Graph Update (conditional, not blanket)
If the task touched code, changed architecture, or produced a reusable finding: update `.code-review-graph`, `memory`, and `graphify-out` with what changed, what was found, and what pattern to remember. If the task was pure conversation with no code/decision impact, skip this step explicitly rather than performing a no-op update.

### Output Format (every response)
```
[PRIMARY MODE: ] [STAGE(S): ] [MCPs USED: ] [SKILLS USED: ] [AGENTS USED: ]
```

---

## 3. Global Always-On Layer (the only unconditional entries)

These global capabilities fire on every task. All share the same qualifying property: cheap per-turn cost, zero code-dependency required to fire, and massive token savings.

### `opencode-token-optimization`
- **Purpose**: Global Token Optimization Engine (TOE v2). Eliminates waste across input, output, context, tool calls, reasoning, and formatting while preserving correctness.
- **Trigger**: every task, no exception.
- **Skip condition**: none.
- **Token cost**: negligible (response-shaping constraint that saves tokens).
- **Automation**: fully automatic.

### `ponytail`
- **Purpose**: Lazy Senior Engineer Discipline. Enforces YAGNI, stdlib over custom code, native platform features before dependencies, smallest working diffs, zero unrequested fluff/boilerplate.
- **Trigger**: every task, no exception.
- **Skip condition**: none. (Default level: `full`).
- **Token cost**: negligible (architectural & code-shaping constraint that saves tokens).
- **Automation**: fully automatic.

### `ruflo` (MCP)
- **Purpose**: Universal Orchestration & Memory Persistence Substrate. Manages cross-task memory persistence, workflow execution graphs, state tracking, and sub-task coordination.
- **Trigger**: every task, no exception.
- **Skip condition**: none.
- **Token cost**: low–medium.
- **Automation**: fully automatic.

### `verification-before-completion`
- **Purpose**: block any "fixed / done / solved / production-ready" claim until the claim has been checked against actual output (test run, build result, re-read diff — not assumption).
- **Trigger**: immediately before any completion-style statement, every task.
- **Skip condition**: none. Depth scales with task risk (§2 Step 5) but the check itself never skips.
- **Dependencies**: consumes output of whichever stage just ran (Development, Debugging, QA, etc.).
- **Token cost**: low–medium, proportional to what's being verified.

### `safety-guardrails`
- **Purpose**: detect destructive/irreversible operations (force-push, drop table, mass delete, prod deploy without rollback) and require an explicit reversible-alternative check before proceeding.
- **Trigger**: any action classified as destructive/irreversible in Step 1 or Step 2.
- **Skip condition**: task has no destructive/irreversible operation.
- **Token cost**: low (a gate check, not a full review).

### `writing-plans`
- **Purpose**: produce a short implementation plan — requirements, ambiguities to clarify, phases, risks, dependencies, acceptance criteria — before implementation starts.
- **Trigger**: task classified **non-trivial** in Step 1 (new feature, multi-file change, architecture-affecting, or irreversible).
- **Skip condition**: task is trivial (single fact, one-line fix, no architectural surface). Running a full plan on a one-line typo fix is exactly the waste this manual is meant to eliminate.
- **Output feeds**: Planning Stage (§4) directly; nothing downstream starts before this exists, when triggered.

### `context-optimizer`
- **Purpose**: prune irrelevant/stale context before each model call, preventing token bloat from accumulating across a session.
- **Trigger**: every model call, no exception.
- **Skip condition**: none — this runs even on trivial turns, since it's a pre-call step rather than a task-shaped one.
- **Token cost**: negligible per call; the savings compound over a session.
- **Note**: distinct from `context-window-management`/`caveman` (§5) — this is per-*call* micro-pruning; those are session-*level* macro-compression triggered at growth thresholds.

### `memory-history`
- **Purpose**: cache business logic/context so giant docs and prior summaries aren't re-read and re-summarized every session.
- **Trigger**: every task that would otherwise re-read project documentation or business rules already cached.
- **Skip condition**: task needs no project-specific context (e.g. a pure general-knowledge question).
- **Token cost**: low (cache lookup) — its whole point is avoiding the *high*-cost operation (full re-read).
- **Dependencies**: reads/writes the `memory` resource (§5, Investigation Stage); uses `caveman-compress` (§5) as its compression engine for large source documents.

### `session-persistence`
- **Purpose**: instantly rehydrate workspace context at session start without running expensive discovery commands again.
- **Trigger**: start of every session/turn where prior workspace state exists.
- **Skip condition**: genuinely fresh workspace with no prior state to rehydrate.
- **Token cost**: low — replaces what would otherwise be a fresh Investigation-stage discovery pass.

---

## 4. Stage Pipeline

Each stage has a one-line **I/O contract** so individual skills below don't need to repeat inputs/outputs — this is defined once per stage instead of per skill (a direct token-usage optimization).

```
Request
  │
  ▼
[Step 1: Classify] ──trivial──► skip Planning, go straight to Development/Direct-Answer
  │ non-trivial
  ▼
Planning Stage ───────────────► plan (scope, phases, risks, acceptance criteria)
  │
  ▼
Investigation Stage ──────────► impact radius, affected files, relevant history/business rules
  │
  ▼
Architecture/Design Stage ────► technology + structure decisions (only if new surface area)
  │
  ▼
Development Stage ────────────► implementation / refactor / docs update
  │
  ├──(bug present)──► Debugging Stage ──► root cause + minimal fix
  │
  ▼
Cleanup Stage ─────────────────► dead code / duplication removed, behavior preserved
  │
  ▼
Review Stage ──────────────────► architecture, quality, edge-case findings
  │
  ▼
Security Stage (if applicable) ► authn/authz/secrets/OWASP findings
  │
  ▼
verification-before-completion ► claim gate
  │
  ▼
QA Stage (non-trivial only) ──► build/route/API/DB/prod-readiness checks
  │
  ▼
Deployment Stage (if requested)► safe rollout + rollback plan
  │
  ▼
Background Maintenance ───────► context compression/monitoring (long sessions only)
  │
  ▼
Step 6: conditional Code Review Graph update
```

### Stage I/O Contracts

| Stage | Input | Output |
|---|---|---|
| Planning | raw request + classification | plan doc (scope/phases/risks/acceptance criteria) |
| Investigation | plan (or trivial request directly) | affected files, dependency map, relevant memory/history |
| Architecture/Design | investigation output | chosen structure/tech, milestone breakdown |
| Development | design + investigation output | code/doc changes |
| Debugging | failing behavior + dev output | root cause + minimal patch |
| Cleanup | current code state | reduced dead code/duplication, same behavior |
| Review | cleaned code | findings list (architecture, complexity, edge cases) |
| Security | code + review findings | vuln/authn/authz/secrets findings |
| QA | reviewed + secured code | build/route/API/DB/prod-readiness pass/fail |
| Deployment | QA-passed build | deployed artifact + rollback plan |
| Background Maintenance | running session | compressed context, preserved key facts |

---

## 5. Full Capability Roster

**Type key**: SK = Skill, MCP = tool/integration, AG = Agent, RES = Resource.
Sub-topics from the original routing tree (React, Tailwind, Docker, Playwright, README, etc.) are **competency tags nested under their parent skill**, not separately loaded capabilities — loading forty granular tags individually would recreate the exact bloat this audit is meant to remove.

| Capability | Type | Stage | Purpose | Trigger (run when) | Skip when | Token cost | Priority |
|---|---|---|---|---|---|---|---|
| `writing-plans` | SK | Planning | Scope, phase, and risk the work | non-trivial task | trivial task | med | high |
| `sequential-thinking` (MCP) | MCP | Cross-stage (Planning/Architecture/Debugging/Security) | Force step-by-step logical decomposition of ambiguous/complex problems before acting | task is high-complexity or ambiguous, regardless of stage | problem is simple/well-defined | med | high |
| `opencode-architecture-planning` | SK | Planning | Umbrella architecture pass; prevents technical debt before code is written | new surface area / cross-module change | pure bugfix, no new structure | med | high |
| `software-architecture` | SK | Planning/Design | System-level structure decisions (domain lens under `opencode-architecture-planning`) | new surface area / cross-module change | pure bugfix, no new structure | med | high |
| `backend-architect` | SK | Planning/Design | Backend structure & tech choice (domain lens under `opencode-architecture-planning`) | backend surface added/changed | frontend-only task | med | med |
| `frontend-architect` | SK | Planning/Design | Frontend structure & tech choice (domain lens under `opencode-architecture-planning`) | UI surface added/changed | backend-only task | med | med |
| `senior-architect` | SK | Planning + Review (advisory) | Senior-level second opinion on structural decisions and structural integrity | plugged into Planning's architecture check and Review's audit — not a standalone pass | trivial task with no structural decision | low–med | med |
| `vexor-cli` | SK | Investigation | Codebase search/exploration | need to locate code/usages | location already known | low | high |
| `dependency-analysis` | SK | Investigation | Trace what a change will affect | any code-touching change | pure conversation | low | high |
| `graphify-out` | RES | Investigation | Map code dependencies/architecture | code-touching task | non-code task | low | high |
| `.code-review-graph` | RES | Investigation/Review | Prior findings, impact radius, avoid repeat mistakes | code-touching task, before + after | non-code task | low | high |
| `memory` | RES | Investigation | Business rules & high-level project context | task needs project-specific context | context already in-hand | low | med |
| `ruflo` (MCP) | MCP | Investigation/Automation | Orchestration + memory persistence substrate | multi-step workflow or memory lookup needed | single-turn trivial task | low–med | med |
| `open-deep-research` | SK | Investigation | External deep research for novel/unfamiliar tech (e.g. brand-new framework version) to prevent hallucinated code | codebase/internal search can't answer it — genuinely novel problem | answer is available via `vexor-cli`/internal context | med–high | med |
| `error-detective` | SK | Debugging | Diagnose from logs/errors | reproducible error/log available | no error signal yet | med | high |
| `debugging-toolkit-smart-debug` | SK | Debugging | Structured resolution path when tests fail (supersedes generic `debugging-toolkit`, §0.1) | active debugging session, test failure present | issue not yet reproduced | med | med |
| `filesystem` (MCP) | MCP | Debugging/Investigation | Direct file inspection | need raw file state | already have file content | low | med |
| `systematic-debugging` | SK | Debugging | Umbrella method: reproduce → root-cause → minimal fix → regression check; invokes `error-detective` then `debugging-toolkit-smart-debug` | bug reported/confirmed | no bug present | med | high |
| `vibe-code-cleanup` | SK | Cleanup | Remove dead code/unused imports/duplication, preserve behavior — subtractive pass | after Development, before Review | prototype/throwaway code explicitly requested messy | low–med | med |
| `opencode-refactoring` | SK | Cleanup | DRY restructuring of messy code post-implementation — transformative pass, runs alongside `vibe-code-cleanup` in the same Cleanup stage | after Development, before Review | prototype/throwaway code explicitly requested messy | low–med | med |
| `tdd-workflow` | SK | Development | Enforce test-first, modular implementation to cut regression bugs | new feature/logic implementation | trivial one-line fix | med | high |
| `opencode-bug-detection` | SK | Review | Static-analysis pass for logical flaws before runtime; runs *before* `bugs-are-annoying` | non-trivial code change | trivial one-liner | med | high |
| `vibe-code-auditor` | SK | Review | Architecture/maintainability/complexity review of AI-generated code | non-trivial code change | trivial one-liner | med | high |
| `bugs-are-annoying` | SK | Review | Deeper semantic pass: edge cases, race conditions, null refs, missing validation — runs after `opencode-bug-detection` | non-trivial code change | trivial one-liner | med | high |
| `caveman-review` | SK | Review (output mode) | One-line-per-finding format for `vibe-code-auditor`/`bugs-are-annoying`/`code-reviewer` on large PRs | diff size crosses a "large PR" threshold | small/normal-size diff — use full prose | low | med |
| `code-reviewer` | SK | Review/Git | PR-level review, applies quality baseline (see `ponytail` merge, §6) | PR/commit-level change | no VCS action involved | med | med |
| `pr-writer` | SK | Git/Deployment-prep | Auto-format professional PR descriptions from the diff | PR being opened | no PR involved | low | med |
| `caveman-commit` | SK | Git | Conventional, sub-50-char commit messages | any commit action | no commit involved | low | low |
| `github` (MCP) | MCP | Review/Git/Automation | Repo/PR/issue operations | any git/repo action needed | no repo interaction | low | med |
| `security-audit` | SK | Security | Umbrella: authn/authz/secrets/OWASP for higher-risk changes; invokes `vulnerability-scanner` as its automated sub-scan | auth, data, or externally-facing change / new attack surface | routine PR with no new attack surface — use `differential-review` instead | med–high | high |
| `differential-review` | SK | Security | Fast default diff-level gate: OWASP + leaked-secret check on every PR | every PR, as the routine default | task explicitly needs the full `security-audit` (auth/data-model change) | low–med | high |
| `vulnerability-scanner` | SK | Security | Automated dependency/secret scan (sub-tool of `security-audit`) | invoked by `security-audit` | run standalone only if audit explicitly skipped | low | med |
| `api-security-best-practices` | SK | Security | API-specific input validation/auth checks | task adds/changes an API endpoint | no API surface touched | low–med | med |
| `performance-engineer` | SK | Review/QA | Profiling, rendering, DB, caching review | perf-sensitive path changed | no perf-sensitive path | med | med |
| `web-performance-optimization` | SK | Review/QA | Bundle size/rendering optimization | frontend perf concern raised | no frontend perf concern | med | low |
| `frontend-developer` | SK | Development | UI implementation (React/Next.js/Tailwind/Accessibility) | frontend implementation task | backend-only task | med | high |
| `ui-ux-designer` | SK | Development/Review | UX-level review of frontend work | frontend task with UX implications | pure backend/API task | low–med | low |
| `backend-developer` | SK | Development | Backend implementation (API/DB/Auth/Caching) | backend implementation task | frontend-only task | med | high |
| `nodejs-backend-patterns` | SK | Development | Node-specific backend pattern guidance | Node backend implementation | non-Node stack | low | low |
| `ml-engineer` | SK | Development | ML system implementation | ML/AI implementation task | non-ML task | med | med |
| `data-scientist` | SK | Development/Investigation | Data analysis, model evaluation | data/ML analysis task | non-data task | med | med |
| `workflow-automation` | SK | Automation | Design automation logic (distinct from `ruflo`'s execution substrate) | task requires new automated workflow | one-off manual task | med | low |
| `vibecode-production-qa-validator` | SK | QA | Build/route/API/auth/DB/SEO/prod-readiness validation | non-trivial task nearing completion | trivial task | med–high | high |
| `k6-load-testing` | SK | QA (manual) | Load/perf testing | explicitly requested | not requested | med | manual-only |
| `vercel-deployment` (or platform equivalent) | SK | Deployment | Safe deploy, env validation, rollback plan | deployment explicitly requested | no deploy requested | med | high |
| `vercel-optimize` | SK | Deployment | Deploy-time performance tuning | deployment stage active + perf concern | no deploy or no perf concern | low | low |
| `aws-cost-cleanup` | SK | Deployment/Background Maintenance (manual/periodic) | Clean up unused cloud resources | explicitly requested or scheduled cost audit | not requested, no scheduled audit due | low–med | manual/periodic |
| `caveman` | SK | Background Maintenance | Session-wide compression engine (executes what `context-window-management` triggers, supersedes v2's generic `context-compression`, §0.1) | long session, context growing large | short session | low | manual-trigger in short sessions |
| `context-window-management` | SK | Background Maintenance | Monitor context growth, decide when to trigger `caveman` | every long session, passively | short session | negligible | med |
| `caveman-compress` | SK | Background Maintenance / Investigation | Compress long docs/PRDs/notes/audits (the engine `memory-history` uses internally, §3) | large document needs caching/re-use | short document, no re-read cost to avoid | low | high |
| `caveman-stats` | SK | Background Maintenance (manual/optional only) | Report estimated token-savings metrics for motivation | explicitly requested | not requested — never auto-reported as a verified figure since savings are estimated, not measured | negligible | manual-only |
| `cavecrew` | Protocol (coupled to `agency-agents`, §8) | Automation | Token-efficient inter-agent communication for parallel streams | `agency-agents` is actively running multiple streams | single-stream/no parallel execution | low | med |
| `using-git-worktrees` | SK | Development (manual) | Parallel branch workspaces | explicitly requested multi-branch work | not requested | low | manual-only |
| `skill-creator` | SK | Meta (manual) | Create/modify/optimize skills | explicitly requested | not requested | med | manual-only |
| `general-assistant` | SK | Fallback | Direct, unassisted handling | no other skill matches | any specific skill matches | low | fallback-only |

---

## 6. Overlap Resolution

| Overlap | Decision | Rationale |
|---|---|---|
| `token-saver` vs. `opencode-token-optimization` | **REPLACE** — `opencode-token-optimization` (TOE v2) completely supersedes the basic `token-saver`. | `token-saver` was a simple prompt to be concise; TOE v2 is a comprehensive cognitive framework governing all forms of token efficiency (input, output, reasoning, tools). Keeping both is redundant. |
| `ponytail` vs. `vibe-code-auditor` vs. `code-reviewer` vs. `bugs-are-annoying` | **MERGE** — `ponytail`'s rules become the shared baseline standard the three Review-stage skills reference; `ponytail` no longer runs as its own standalone step. | Four skills doing "code quality" independently means the same code gets the same checks repeated. One baseline, three lenses (architecture, VCS/PR, edge cases) — no duplicate passes. |
| `ruflo` (MCP) vs. `workflow-automation` vs. `agency-agents` | **KEEP all three, boundaries clarified**: `ruflo` = execution/memory substrate, `workflow-automation` = the automation-design skill, `agency-agents` = the parallel-dispatch mechanism for independent sub-tasks. | They were overlapping only because v1 called all three "orchestration." Each now owns a distinct layer: knowledge → tool → dispatcher. |
| `security-audit` vs. `vulnerability-scanner` | **MERGE** — scanner becomes a sub-tool invoked by the audit, not a parallel top-level skill. | Running both independently duplicated the automated-scan portion of the audit. |
| `caveman` vs. `context-window-management` | **KEEP both, coupled** — management monitors and triggers, `caveman` executes the compression. | Not true duplication: one decides, one acts. This replaces v2's `context-compression` placeholder with the actual named engine. |
| `systematic-debugging` vs. `error-detective` vs. `debugging-toolkit-smart-debug` | **KEEP all three, hierarchy clarified**: `systematic-debugging` is the umbrella method that invokes `error-detective` (diagnosis) then `debugging-toolkit-smart-debug` (structured fail-driven resolution). | v1 listed these as siblings, risking all three firing independently on the same bug. Now there's one entry point. |
| `vibe-code-cleanup` vs. `vibe-code-auditor` | **KEEP both, different stages** — cleanup removes dead code (Cleanup stage), auditor reviews architecture/complexity (Review stage). | No real overlap once stage-scoped; v1's flat list made them look redundant. |
| `frontend-developer`/`backend-developer` vs. `frontend-architect`/`backend-architect` | **KEEP both, different stages** — architects decide structure in Planning/Design, developers implement in Development. | Same domain, different lifecycle phase — not duplicate work if properly sequenced. |
| `github` (MCP) vs. `code-reviewer` vs. release/changelog sub-tasks | **KEEP** — `github` is the tool substrate; `code-reviewer` and release-management tasks are skills that use it. | Substrate vs. skill distinction avoids treating a tool integration as if it were a competing skill. |
| `opencode-architecture-planning` vs. `software-architecture`/`backend-architect`/`frontend-architect` | **MERGE** — `opencode-architecture-planning` is the Planning-stage umbrella; the other three become its domain-specific lenses. | Three independent architecture passes risk producing conflicting structural decisions on the same task. One umbrella, three lenses. |
| `senior-architect` vs. `software-architecture` + `vibe-code-auditor` | **KEEP, but as an advisory checkpoint, not a standalone pass** — plugs into Planning's structure decision and Review's audit. | A full independent senior-architect pass would re-run the same analysis twice; a plugged-in second opinion at the two existing checkpoints gets the value without the duplicate work. |
| `opencode-bug-detection` vs. `bugs-are-annoying` | **KEEP both, sequenced** — static/mechanical pass first, semantic/logic pass second. | Same problem space (logic flaws), different method (static analysis vs. semantic review). Sequencing lets the deeper pass focus on what the mechanical pass didn't already catch, instead of two full independent re-reads. |
| `opencode-refactoring` vs. `vibe-code-cleanup` | **KEEP both, same Cleanup stage, sequential sub-phases** — subtractive removal, then DRY restructuring. | Genuinely different transformations on the same code; running them as one Cleanup pass with two sub-phases avoids re-scanning the codebase twice. |
| `differential-review` vs. `security-audit`/`vulnerability-scanner` | **KEEP both, risk-scoped** — `differential-review` is the fast default on every PR; `security-audit` (with `vulnerability-scanner`) is reserved for higher-risk changes. | Running the full audit on every routine PR is the exact waste this manual exists to prevent; scoping by risk keeps both useful without double-running the OWASP/secrets check. |
| `caveman-compress` vs. `memory-history` | **MERGE** — `caveman-compress` is the compression engine `memory-history` uses internally. | Both target the same problem (avoid re-reading/re-summarizing giant docs) — one skill owns the cache, the other does the compressing for it. |
| `caveman` vs. `caveman-compress` | **KEEP separate, different scope** — `caveman` compresses live session/conversation context; `caveman-compress` compresses static reference documents (PRDs, notes, audits) being cached into `memory`. | Session state and reference documents have different lifecycles and different consumers — collapsing them would blur what's ephemeral vs. what's persisted. |
| `caveman-review` vs. `code-reviewer`/`vibe-code-auditor`/`bugs-are-annoying`/`differential-review` | **MERGE as an output mode, not a fifth skill** — on large PRs, the existing Review-stage skills emit one-line-per-finding instead of full prose. | Same review depth, same skills doing the work — just a cheaper output format when the diff is large enough that full prose would be wasteful. |
| `cavecrew` vs. `agency-agents` | **MERGE** — `cavecrew` becomes `agency-agents`'s inter-stream communication protocol, not an independently-triggered skill. | Same problem (multi-agent token waste). A standalone `cavecrew` could theoretically fire without a parallel session to govern; coupling it to `agency-agents` ties its trigger to the actual condition that creates the waste. |

---

## 7. Auto-Run Rules

### Always Auto-Run (every task, no exception)
- `opencode-token-optimization`
- `ponytail`
- `ruflo` (MCP)
- `context-optimizer` (per model call)
- `verification-before-completion`
- `safety-guardrails` (gate check — only *acts* if a destructive operation is detected)
- `writing-plans` (gate check — only *acts* if the task is non-trivial)
- `memory-history` / `session-persistence` (gate checks — only *act* if cached context/prior session state actually exists)

### Stage Auto-Run (fires only when its stage is active)
- Planning → `writing-plans`, `opencode-architecture-planning` (→ `software-architecture`, `backend-architect`/`frontend-architect`), `senior-architect` (advisory), `sequential-thinking` (if high-complexity/ambiguous)
- Investigation → `vexor-cli`, `dependency-analysis`, `graphify-out`, `.code-review-graph`, `memory`, `ruflo`, `open-deep-research` (novel/unfamiliar tech only)
- Debugging → `systematic-debugging` (→ `error-detective` → `debugging-toolkit-smart-debug`), `sequential-thinking` (if root cause is non-obvious)
- Development → `tdd-workflow` (new feature/logic)
- Cleanup → `vibe-code-cleanup` + `opencode-refactoring` (sequential sub-phases of one pass)
- Review → `opencode-bug-detection` → `bugs-are-annoying` → `vibe-code-auditor`, `code-reviewer` (baseline: merged `ponytail` rules), `caveman-review` (large-diff output mode only)
- Security → `differential-review` (default, every PR) or `security-audit` (→ `vulnerability-scanner`) for higher-risk changes, `api-security-best-practices`
- QA → `vibecode-production-qa-validator`
- Git → `pr-writer`, `caveman-commit`
- Deployment → `vercel-deployment`, `vercel-optimize`
- Background Maintenance → `context-window-management` (monitor, passive) → `caveman` (compress, on trigger), `caveman-compress` (large reference docs, via `memory-history`)
- Automation (parallel execution only) → `cavecrew` (coupled to `agency-agents`)

### Manual-Only (never auto-run; explicit request required)
- `k6-load-testing`
- `skill-creator`
- `using-git-worktrees`
- `aws-cost-cleanup` (unless a periodic cost audit is explicitly scheduled)
- `caveman-stats` (savings are estimated, not measured — never surfaced as a verified number)
- `caveman` (in short sessions — auto in long ones via `context-window-management`)

---

## 8. Agent Definitions

### Primary Agent (the acting model)
- **Mission**: own end-to-end task execution and the Step 1–6 protocol.
- **Scope**: full request lifecycle — classification through completion claim.
- **Decision authority**: selects stages and capabilities per §3–§5; cannot skip `verification-before-completion` or `safety-guardrails`.
- **Escalation**: on repeated stage failure, fall back to `general-assistant` mode and report explicitly what failed.
- **Allowed skills**: entire roster, subject to trigger conditions.
- **Forbidden skills**: none categorically — everything is trigger-gated, not identity-gated.
- **Success criteria**: task complete, verified, no destructive action taken without an explicit guardrail check.
- **Failure criteria**: a completion claim made without verification, or a destructive action taken without a guardrail check — both are protocol violations regardless of outcome.

### `agency-agents` (Parallel Sub-Agent Dispatcher)
- **Mission**: execute genuinely independent sub-tasks concurrently.
- **Scope**: triggered only when Step 2 identifies two or more sub-tasks with no shared dependency.
- **Communication protocol**: uses `cavecrew` for inter-stream communication whenever more than one stream is active, so parallel agents don't burn tokens narrating to each other — `cavecrew` is not invoked independently of this agent (§6).
- **Decision authority**: can assign sub-tasks to parallel execution streams; cannot merge dependent sub-tasks into parallel streams.
- **Escalation**: if sub-tasks turn out to have a hidden dependency once running, halt parallel execution and re-sequence.
- **Allowed skills**: any Development/Investigation/Review skill needed by its assigned sub-task.
- **Forbidden skills**: cannot itself invoke Deployment-stage actions without the Primary Agent's Step 5 verification gate.
- **Input requirement**: a task graph with explicit independence already established in Step 2 — it does not perform its own dependency analysis.
- **Output requirement**: per-stream results, tagged by sub-task, ready for the Primary Agent to reassemble.
- **Success criteria**: all streams complete with no cross-stream state corruption.
- **Failure criteria**: any stream silently modifying state another stream depends on — this is treated as a protocol violation, not a normal error.

### `general-assistant` (Fallback Mode)
- **Mission**: handle the request directly when no specific skill/MCP/agent matches.
- **Scope**: whatever remains after Step 3 finds no match.
- **Decision authority**: none beyond direct, unassisted response.
- **Escalation**: none — this is already the floor of the fallback chain.
- **Success/failure criteria**: same as Primary Agent's general completion/verification rules, just without specialist tooling.

---

## 9. Token Optimization Strategy

1. **Global set shrunk from 8 blanket items to 4 true globals** — the other four now fire only under a concrete condition (§0 table), so trivial requests no longer pay for memory lookups, orchestration, or code-review-graph writes they don't need.
2. **Per-stage I/O contracts defined once** (§4) instead of repeated per skill, removing ~35 redundant Input/Output blocks from the roster.
3. **Sub-tool consolidation**: `vulnerability-scanner` under `security-audit`, `error-detective`/`debugging-toolkit` under `systematic-debugging` — one invocation instead of three independent ones covering the same ground.
4. **Verification depth scales with task risk** (§2 Step 5) rather than running the full QA/Security stage on every one-line change.
5. **Routing-tree sub-topics** (React, Tailwind, Docker, Playwright, README, etc.) are competency tags under their parent skill, not 40 separately-loaded entries.
6. **`context-optimizer` prunes every call**, and `session-persistence` skips re-discovery at session start — both restored from v1 after being mistakenly dropped in v2 (§0.1).
7. **`caveman-review` swaps full-prose findings for one-line-per-finding on large PRs** — same review depth, a fraction of the output tokens.
8. **`differential-review` replaces `security-audit` as the default PR gate**, reserving the heavier full audit for genuinely higher-risk changes instead of running it on every routine diff.
9. **Sequenced pairs instead of parallel duplicates**: `opencode-bug-detection` → `bugs-are-annoying`, and `vibe-code-cleanup` → `opencode-refactoring` — each pair does one combined pass over the code instead of two independent full re-reads.

---

## 10. Strict System Rules

- Never load skills, MCPs, or agents globally "by default" outside §3's Global Always-On Layer — Step 3 selection is mandatory every task.
- Never skip `opencode-token-optimization`, `verification-before-completion`, or `safety-guardrails` — they are unconditional.
- `writing-plans` is unconditional in trigger-check but conditional in action — always evaluate triviality, only produce a plan when non-trivial.
- Never update `.code-review-graph`/`memory`/`graphify-out` on a turn that touched no code and made no architectural decision — log that the update was intentionally skipped rather than performing a no-op write.
- Never hallucinate a skill, MCP, or agent not in §5's roster.
- Always select the most specific matching skill for each sub-task; fall back to `general-assistant` only when nothing matches.
- Never claim `ruflo`, `agency-agents`, or `.code-review-graph` were used unless actually invoked.
- Prefer `.code-review-graph` and `ruflo` when a task is code-touching or multi-step; do not invoke either for pure conversational turns.
- Fall back gracefully and report explicitly when a capability is unavailable.
- `debugging-toolkit` (v2 name) is retired — use `debugging-toolkit-smart-debug` (§0.1); do not reference the old name in new output.
- Never report `caveman-stats` token-savings figures as verified/measured — they are estimates by design (§0.1), and must be labeled as such if surfaced at all.
- Never invoke `cavecrew` outside an active `agency-agents` multi-stream run — it has no standalone trigger (§6, §8).