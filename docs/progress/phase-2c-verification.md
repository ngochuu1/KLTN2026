# Phase 2C Verification

## Status

DONE — Workspace tests, permission, invitation, transaction/constraint và Backend startup PASS. Không thay đổi API/database contract hoặc nghiệp vụ.

## Tests total / passed / failed

- Total: 30; passed: 30; failed: 0; skipped: 0.
- Chạy toàn bộ suite đúng một lần cuối stage: `python -m unittest tests.test_workspace_api -v` từ `backend`, dùng Python Windows `.venv-win` kết nối PostgreSQL `kltn_test` riêng.
- Trước đó chạy targeted 6 tests cho tạo Workspace, rollback Create/Accept và concurrent requests; tất cả PASS.
- Coverage UC06–UC14: create + OWNER, input validation, list/detail theo membership, invitation direct/generic/hash/expiry/accept/decline/reuse, duplicate membership, update, member list/remove, role, leave và soft-delete.
- Permission matrix OWNER/ADMIN/MEMBER PASS; system_role ADMIN không cấp quyền Workspace; role mới có hiệu lực ngay.
- Soft-delete chặn các endpoint nghiệp vụ, giữ Workspace/memberships/invitations; error envelope kiểm tra unauthorized/forbidden/not found/conflict/invalid invitation.
- Inject lỗi giữa flow Create và sau hai writes Accept: rollback nhất quán; SQL trực tiếp xác nhận UNIQUE membership và single OWNER.
- Ba concurrent tests dùng sessions/connections riêng: cùng invitation với hai User chỉ một accept thành công; hai invitation cùng User không tạo duplicate; accept/decline cạnh tranh giữ status và membership nhất quán.
- Backend lifespan startup và health PASS. Tests thường rollback outer transaction/savepoints; concurrent tests cleanup đúng UUID fixtures đã commit. Guard trước/sau suite xác nhận test database không có dữ liệu tồn dư; không fallback sang development database.
- Không chạy Phase 1 suite hoặc frontend build.

## Files changed

- `backend/tests/test_workspace_api.py`
- `README.md`
- `docs/progress/phase-2c-verification.md`

## Bugs fixed

Không phát hiện bug implementation trong phạm vi kiểm thử. Không sửa source ứng dụng.

## Remaining issues

Không có blocker trong phạm vi Workspace Backend Phase 2A–2C. Frontend chưa triển khai, thuộc Phase 2D.

## Next stage

Phase 2D — Workspace Frontend.
