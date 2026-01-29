# Backend Refinement Log

This log tracks backend changes aimed at production hosting (Ubuntu server), remote LLM usage, and distributed-systems readiness.

## 2026-01-29
- Added centralized settings in `app/core/settings.py` for env parsing, host/port, CORS, cache, LLM, DB, and storage config.
- Wired FastAPI startup to settings and added request ID middleware + structured logging.
- Hardened DB initialization with pool and timeout settings.
- Refactored LLM service for lazy init with configurable timeouts and optional healthcheck.
- Added readiness endpoint at `/api/system/ready` with DB + LLM checks.
- Made knowledge-graph cache path/TTL configurable.
- Added single-flight guard and richer status metadata for background graph generation.
- Added S3/MinIO storage client abstraction and optional note mirroring.
- Added storage metadata columns to `FileSystem` model and schema fields.
- Added cleanup utilities for cache and orphaned storage objects.
- Added system status + metrics endpoints under `/api/system`.
- Added circuit-breaker behavior and configurable retries/timeouts for LLM and storage.
- Added environment-based CORS tightening and `NEPTUNE_MODE` support.
- Added `app/server.py` uvicorn entrypoint with env-driven settings.
- Added pytest coverage for settings parsing and LLM cooldown.
- Added pytest `conftest.py` to ensure backend imports resolve in tests.
- Updated backend deployment guide for Ubuntu + systemd + Tailscale.
