# Phase 3B3 Verification

## Status

FAILED — implementation and targeted PostgreSQL verification pass; MinIO standalone runtime health is not verified.

## Storage setup

- Local development uses MinIO standalone on Windows through `OBJECT_STORAGE_*` environment variables.
- Docker Compose contains no MinIO service, bucket initializer, or MinIO volume.
- S3-compatible upload, compensation delete, bucket check, and temporary authorized download URL abstraction remain unchanged.
- Source code does not hard-code a storage endpoint, port, access key, secret key, or bucket.

## API implemented

- `POST /api/v1/channels/{channel_id}/messages/attachments`
- `GET /api/v1/attachments/{attachment_id}/download`

## Files changed

- `docker-compose.yml`
- `README.md`
- `backend/.env.example`
- `backend/requirements.txt`
- `backend/app/api/v1/chat.py`
- `backend/app/core/config.py`
- `backend/app/repositories/chat_attachment_repository.py`
- `backend/app/repositories/chat_message_repository.py`
- `backend/app/schemas/chat.py`
- `backend/app/services/chat_service.py`
- `backend/app/services/storage_service.py`
- `backend/tests/test_chat_attachments.py`
- `docs/progress/phase-3b3-verification.md`

## Verification

- Targeted PostgreSQL attachment and Phase 3B2 regression tests: PASS (9 tests).
- Upload policy, 25 MB byte limit, authorization, TEXT-only rule, history, realtime, download, rollback, and compensation: PASS.
- Backend startup and OpenAPI contract: PASS.
- Missing storage environment configuration is rejected before creating an S3 client: PASS.
- MinIO standalone health and live object round-trip: FAIL (MinIO standalone is not installed/running on the local machine).

## Bugs fixed

- No pre-existing Phase 3B2 bug was found.

## Remaining issues

- Install/start MinIO standalone on Windows, configure the private bucket and `OBJECT_STORAGE_*`, then verify a live upload/download round-trip.

## Next stage

Complete Phase 3B3 MinIO standalone runtime verification before Phase 3C.
