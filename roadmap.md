# Neptune Roadmap

This roadmap is organized into phases with clear goals, deliverables, and decision points. It assumes two deployment modes:
1) **Desktop (DMG)**: offline-first for users.
2) **Server (Kubernetes)**: hosted services for your own use or optional online mode.

---

## Phase 0 — Decisions & Constraints (Short, High-Impact)
**Goals**
- Decide what runs locally vs. on your server.
- Define offline requirements for the DMG.

**Decisions**
- **Offline-first DMG** (recommended): local SQLite + local Ollama model.
- **Optional hosted mode**: remote Ollama + Postgres via server.
- **Two download SKUs**:
  - **Lite**: smaller DMG, uses hosted Ollama.
  - **Full**: larger DMG with local Ollama model.

**Outcome**
- Clear definition of “local-only” vs “hosted-assisted” capabilities.

---

## Phase 1 — Service Boundaries (Distributed Systems Design)
**Goal**
Split the backend into real services with clean boundaries.

**Services**
1) **neptune-backend**  
   - API gateway + orchestration  
   - Notes CRUD, search, graph retrieval
2) **neptune-llm**  
   - Embeddings + topic extraction (Ollama)
3) **neptune-indexer**  
   - Background workers for embeddings, graph generation, and indexing

**Deliverables**
- Service contracts (HTTP APIs) between backend and LLM/indexer.
- Clear failure/timeout strategies and retries.

**Notes**
- This phase can be done without Kubernetes.

---

## Phase 2 — Data Layer Upgrade (SQLite → Postgres)
**Goal**
Enable multi-service and multi-pod reliability.

**Decision**
- **Desktop mode** stays on SQLite.
- **Server mode** uses Postgres.

**Deliverables**
- Postgres migration scripts.
- Environment-based DB selection: SQLite for desktop, Postgres for server.

---

## Phase 3 — Kubernetes (Infrastructure Practice)
**Goal**
Run production-like stack on your **Ubuntu MacBook server**.

**Where to run K8s**
- **Primary**: Ubuntu MacBook server (k3s).
- **Optional**: local dev on your Mac with kind/minikube.

**Server Steps**
- Install k3s with `scripts/k8s_bootstrap.sh`
- Apply manifests with `scripts/k8s_deploy.sh`
- Create TLS secret with `scripts/k8s_tls.sh`
- Run migrations via `k8s/migrate-job.yaml`

**K8s Services**
- neptune-backend (Deployment + Service)
- neptune-llm (Deployment + Service)
- neptune-indexer (Deployment + Service)
- Postgres (StatefulSet + PVC)
- MinIO (StatefulSet + PVC)
- Ingress (optional)

**Deliverables**
- `k8s/` manifests or Helm chart.
- Liveness/readiness probes, resource limits, PVCs.

---

## Phase 4 — CI/CD
**Goal**
Automate builds, tests, and deployments.

**Pipeline**
- Backend: pytest + lint
- Frontend: typecheck + lint
- Build Docker images
- Deploy to k3s (GitHub Actions or scripts)

**Deliverables**
- GitHub Actions workflows
- Deployment scripts (`kubectl apply` / Helm)

---

## Phase 5 — MLOps & Inference Ops
**Goal**
Make LLM/embedding quality and reliability production-grade.

**Minimum MLOps**
- Model version pinning
- Embedding latency metrics
- Basic error rate monitoring

**Optional Advanced**
- A/B test models
- Shadow traffic for new models

---

## Phase 6 — Desktop Packaging (DMG)
**Goal**
Deliver a clean offline-first desktop app.

**Deliverables**
- DMG build pipeline
- Optional bundled local model
- Local Ollama setup for “Full” build

**Decision**
- If “Full” build is too large, keep “Lite” as the default.

---

## Recommended Order
1) Phase 1: service boundaries  
2) Phase 2: Postgres for server mode  
3) Phase 3: Kubernetes on Ubuntu server  
4) Phase 4: CI/CD  
5) Phase 5: MLOps  
6) Phase 6: DMG distribution

---

## Open Questions (to answer before Phase 3)
- Do you want **Ingress + TLS**, or port-forward for now?
- Is your server always on and reachable (for Lite build users)?
- What’s your max acceptable DMG size (Full build)?
