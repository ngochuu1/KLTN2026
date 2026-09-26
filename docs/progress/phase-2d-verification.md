# Phase 2D Verification

## Status

DONE — UC06–UC14 Frontend tích hợp Backend thật PASS. Đã bổ sung DELETE vào CORS allow_methods theo phạm vi được phê duyệt; giữ nguyên origin policy và API contract/nghiệp vụ.

## Implemented

- List/create/detail/update Workspace; validation, loading/error/empty, cancel và chống submit lặp.
- Direct invitation bằng User UUID và generic link; sao chép, preview, accept/decline; giữ invitation URL qua đăng nhập.
- Danh sách thành viên trong detail; đổi ADMIN/MEMBER, remove; permission UI OWNER/ADMIN/MEMBER.
- Leave/delete có confirmation, bỏ state detail và chuyển về danh sách tải mới.

## Files changed

- `backend/app/main.py`
- `README.md`
- `frontend/src/lib/workspace-types.ts`
- `frontend/src/lib/workspace-services.ts`
- `frontend/src/features/workspaces/views.tsx`
- `frontend/src/features/auth/store.ts`
- `frontend/src/features/auth/provider.tsx`
- `frontend/src/features/auth/account-forms.tsx`
- `frontend/src/app/(protected)/workspaces/page.tsx`
- `frontend/src/app/(protected)/workspaces/[workspaceId]/page.tsx`
- `frontend/src/app/(protected)/invitations/[token]/page.tsx`
- `frontend/src/app/globals.css`
- `docs/progress/phase-2d-verification.md`

## Lint/Build

- `npm run lint`: PASS, chạy một lần bằng Node Windows.
- `npm run build`: PASS, chạy một lần bằng Node Windows.
- Giữ kết quả Lint/Build PASS của lượt triển khai; lượt gỡ blocker chỉ đổi CORS Backend và tài liệu, không chạy lại frontend checks.
- Không chạy lại Phase 2C Backend suite hoặc các flow đã PASS.

## Integration checks

- Edge headless, frontend localhost:3000 và Backend thật localhost:8000, PostgreSQL theo cấu hình hiện có.
- PASS: create/list/detail/update; cancel update; direct/generic invitation; preview/accept/decline; thông báo invitation đã dùng; danh sách thành viên; OWNER đổi MEMBER thành ADMIN và UI cập nhật ngay; permission UI cả ba role; MEMBER leave và danh sách rỗng sau leave; rejoin.
- Targeted verification bổ sung: 8 PASS / 0 FAIL.
  - OPTIONS preflight DELETE member: HTTP 200, cho phép DELETE, origin vẫn localhost:3000.
  - ADMIN DELETE member thật qua UI: HTTP 204; thành viên biến mất ngay khỏi danh sách.
  - OPTIONS preflight DELETE Workspace: HTTP 200, cho phép DELETE, origin vẫn localhost:3000.
  - OWNER DELETE Workspace thật qua UI: HTTP 204; về danh sách rỗng; GET detail trả 404. Hủy confirmation không xóa Workspace.
  - Invalid invitation: thông báo không hợp lệ, không hiện nút Tham gia.
  - Expired invitation: thông báo hết hạn, không hiện nút Tham gia.
  - Wrong-user direct invitation: thông báo lời mời không dành cho bạn, không hiện nút Tham gia.
  - Already-member invitation: thông báo đã là thành viên, không hiện nút Tham gia.
- Dùng lại đúng ba tài khoản verification cũ; không chạy lại các flow đã PASS. Login và tạo invitation chỉ là setup cho checks còn thiếu.
- Cleanup PASS trong transaction có guard UUID/email/tên và kiểm tra không liên quan dữ liệu ngoài fixture: 3 users, 12 auth sessions, 1 Workspace đã soft-delete, 2 memberships còn lại và 7 invitations. Không còn user tiền tố `phase2d-`; số bản ghi ngoài fixture được giữ nguyên.
- Công cụ và script verification tạm thời đã gỡ; không thêm dependency dự án.

## Remaining issues

Không có blocker Phase 2D.

## Next stage

Phase 2E — Integration & Regression.
