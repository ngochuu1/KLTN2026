# Phase 2A Verification

## Status

DONE

## Database changes

- Thêm `workspaces`, `workspace_members`, `workspace_invitations`; UUID PK, TIMESTAMPTZ và FK tới Workspace/User.
- Workspace soft-delete bằng `deleted_at`; repository mặc định chỉ lấy Workspace hoạt động.
- `WorkspaceRole`: OWNER/ADMIN/MEMBER; `InvitationStatus`: PENDING/ACCEPTED/DECLINED/REVOKED, có CHECK tại database.
- UNIQUE(workspace_id, user_id), UNIQUE(token_hash); partial unique index bảo đảm tối đa một OWNER mỗi Workspace.
- Thiết kế đúng một OWNER: Phase 2B phải tạo Workspace và membership OWNER của người tạo trong cùng transaction. Repository mặc định người tham gia là MEMBER; câu lệnh update role/remove loại trừ OWNER và không cho gán OWNER qua update role. Authorization actor OWNER cho UC12 thuộc service Phase 2B; không dùng users.system_role.
- Invitation chỉ có token_hash, không có plaintext token/code; caller truyền cryptographic hash. Hỗ trợ invitee nullable và expires_at nullable, không đặt lifetime mặc định.
- Repositories không commit; caller sở hữu transaction. ORM relationships dùng explicit eager loading cho async.

## Files changed

- `README.md`
- `backend/app/models/enums.py`
- `backend/app/models/__init__.py`
- `backend/app/models/workspace.py`
- `backend/app/models/workspace_member.py`
- `backend/app/models/workspace_invitation.py`
- `backend/app/repositories/workspace_repository.py`
- `backend/app/repositories/workspace_member_repository.py`
- `backend/app/repositories/workspace_invitation_repository.py`
- `backend/alembic/versions/20260925_01_workspace_foundation.py`
- `backend/tests/test_workspace_foundation.py`
- `docs/progress/phase-2a-verification.md`

## Migration result

PASS — revision `20260925_01`, kế thừa `20260924_01`.
Upgrade → downgrade về Phase 1A → upgrade PASS trên PostgreSQL `kltn_test`; Alembic check PASS.
Database local của dự án đã upgrade head và Alembic check PASS. Không sửa migration cũ, không drop/recreate database.

## Verification

PASS — `python -m unittest tests.test_workspace_foundation -v`: 6/6 tests trên PostgreSQL riêng, fixtures rollback.
Kiểm tra PK/FK/TIMESTAMPTZ, duplicate membership, duplicate OWNER, duplicate token hash và invalid role/status bị database từ chối bằng SQL trực tiếp; CRUD repositories, soft-delete, OWNER protection, invitation direct/link/expiry/status, ORM relationships và Backend import/lifespan startup đều PASS.
Không chạy lại Phase 1 suite; không thêm API, Frontend hoặc Channel.

## Remaining issues

Không có blocker Phase 2A. Service authorization, transaction tạo OWNER và invitation business flows thuộc Phase 2B. Channel/#general tiếp tục deferred sang Channel phase.

## Next stage

Phase 2B — Workspace Backend APIs.
