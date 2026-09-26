# Phase 2B Verification

## Status

DONE

## APIs implemented

13 endpoints, prefix `/api/v1`:

- POST `/workspaces` — tạo Workspace + OWNER atomic, 201.
- GET `/workspaces` — chỉ Workspace active của current User, có role.
- GET `/workspaces/{workspace_id}` — chi tiết và role current User.
- PATCH `/workspaces/{workspace_id}` — OWNER/ADMIN cập nhật name/description.
- DELETE `/workspaces/{workspace_id}` — OWNER soft-delete, 204.
- POST `/workspaces/{workspace_id}/invitations` — OWNER/ADMIN tạo direct/generic invitation, 201; trả token ngẫu nhiên một lần, chỉ lưu SHA-256 hash. expires_at tùy chọn, không đặt lifetime mặc định.
- GET `/workspace-invitations/{token}` — authenticated preview, kiểm tra trạng thái/hạn/invitee/membership/Workspace active.
- POST `/workspace-invitations/{token}/accept` — tạo MEMBER + ACCEPTED atomic; generic invitation dùng một lần.
- POST `/workspace-invitations/{token}/decline` — DECLINED, không tạo membership.
- GET `/workspaces/{workspace_id}/members` — thông tin công khai của thành viên.
- DELETE `/workspaces/{workspace_id}/members/{user_id}` — OWNER/ADMIN remove, cấm remove OWNER, 204.
- PATCH `/workspaces/{workspace_id}/members/{user_id}/role` — chỉ OWNER đổi ADMIN/MEMBER, cấm đổi OWNER.
- POST `/workspaces/{workspace_id}/leave` — ADMIN/MEMBER rời, cấm OWNER, 204.

Responses reuse data/error envelope. Permission logic tập trung tại Service, không dùng system_role.
Mỗi service transaction xác thực lại principal; khóa Workspace trước khi đọc quyền/thực hiện nghiệp vụ, khóa Invitation sau Workspace. Database uniqueness giữ lớp bảo vệ cuối cùng; conflict membership trả 409.
PATCH phân biệt field bỏ qua và description=null; request cấm field ngoài contract.

## Files changed

- `README.md`
- `backend/app/api/v1/router.py`
- `backend/app/api/v1/workspaces.py`
- `backend/app/api/v1/workspace_invitations.py`
- `backend/app/schemas/workspace.py`
- `backend/app/services/workspace_service.py`
- `backend/app/repositories/workspace_repository.py`
- `backend/app/repositories/workspace_member_repository.py`
- `backend/scripts/verify_workspace_api.py`
- `backend/tests/test_workspace_foundation.py`
- `docs/progress/phase-2b-verification.md`

## Verification

PASS — `python -m scripts.verify_workspace_api`, PostgreSQL kltn_test, 55 targeted HTTP requests qua ASGI app thật và auth dependency thật; fixtures và API writes rollback sau kiểm tra.

- Create → OWNER; list chỉ Workspace current User; non-member không truy cập.
- MEMBER không update/mời; OWNER/ADMIN mời được; accept → MEMBER; duplicate invitation/member bị từ chối.
- OWNER đổi MEMBER ↔ ADMIN; quyền mới hiệu lực ngay; ADMIN không đổi role; cấm gán/đổi OWNER.
- Cấm remove/leave OWNER; ADMIN/MEMBER leave được; remove thành viên và target đã bị remove có business error đúng.
- Chỉ OWNER soft-delete; list/detail/update/invite/member management/leave/accept bị chặn sau delete; memberships/invitations được giữ nguyên.
- Direct invitation đúng invitee; generic accept/decline; hết hạn bị chặn, expires_at null hợp lệ; DB lưu hash đúng, response không lộ token_hash.
- Inject lỗi tại create membership và update invitation status: rollback toàn bộ Create/Accept; lời mời sau rollback vẫn dùng được.
- Backend import/lifespan startup và OpenAPI 13 endpoints PASS.
- Sửa assertion Phase 2A vốn cấm Workspace API để phù hợp stage mới; giữ kiểm tra startup/OpenAPI.
- Không chạy lại Phase 1 suite; không sửa Account/Auth. Không thêm migration hoặc full test suite.

## Bugs fixed

Không phát hiện lỗi trong lượt targeted verification. Bỏ assertion lỗi thời “chưa có Workspace API” của kiểm tra foundation Phase 2A.

## Remaining issues

Không có blocker Phase 2B. Exhaustive automated tests và concurrency tests thuộc Phase 2C. Channel/#general tiếp tục deferred sang Channel phase.

## Next stage

Phase 2C — Workspace Backend Tests.
