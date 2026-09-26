# PHASE 2C — WORKSPACE BACKEND TESTS

## 1. MỤC TIÊU

Viết automated tests cho Backend Workspace đã hoàn thành ở Phase 2B.

Phạm vi:

- UC06–UC14
- Workspace CRUD
- Invitation
- Membership
- Permission
- Role management
- Leave Workspace
- Soft delete
- Transaction/duplicate protection

Không làm Frontend.
Không thay đổi API contract/nghiệp vụ.


## 2. NGỮ CẢNH

Chỉ đọc khi cần:

1. `README.md`
2. `docs/progress/phase-2b-verification.md`
3. File này
4. Source Workspace Backend liên quan trực tiếp đến test

Không đọc lại Phase 2A/2B requirements.

Không đọc toàn bộ `docs/use-cases.md`.

Chỉ tra UC06–UC14 nếu phát hiện hành vi chưa rõ.


## 3. TEST ENVIRONMENT

Reuse test setup hiện có từ Phase 1/2A.

- Dùng PostgreSQL test database riêng.
- Không dùng development database.
- Không đổi sang SQLite.
- Test độc lập, cleanup rõ ràng.
- Không phụ thuộc thứ tự chạy.


## 4. TEST CASES BẮT BUỘC

### UC06 — Create Workspace

- Create thành công.
- Creator trở thành OWNER.
- Workspace + OWNER membership được tạo atomic.
- Invalid input bị reject.


### UC07 — List / View Workspace

- Chỉ trả Workspace current User tham gia.
- User khác không nhìn thấy Workspace không thuộc mình.
- Workspace đã soft-delete không xuất hiện.
- Non-member không truy cập detail được.


### UC08 — Invitation

- OWNER tạo invitation được.
- ADMIN tạo invitation được.
- MEMBER bị từ chối.
- Direct invitation tới User hợp lệ.
- Generic link/code invitation hợp lệ.
- User đã là member không được mời lại.
- Database không lưu plaintext invitation token.


### UC09 — Join Workspace

- Accept invitation → MEMBER.
- Decline invitation → không tạo membership.
- Invalid token bị từ chối.
- Expired invitation bị từ chối nếu có `expires_at`.
- Invitation đã dùng không dùng lại được.
- Direct invitation không đúng User bị từ chối.
- Duplicate membership bị từ chối.


### UC10 — Update Workspace

- OWNER update được.
- ADMIN update được.
- MEMBER bị từ chối.
- Workspace deleted không update được.


### UC11 — Manage Members

- Member list đúng.
- OWNER remove MEMBER/ADMIN được.
- ADMIN remove MEMBER được.
- OWNER không bị remove.
- Target không còn tồn tại → business error phù hợp.


### UC12 — Change Role

- OWNER đổi MEMBER → ADMIN.
- OWNER đổi ADMIN → MEMBER.
- ADMIN không đổi role.
- MEMBER không đổi role.
- Không được gán OWNER.
- OWNER không tự đổi role của mình.


### UC13 — Leave Workspace

- MEMBER leave thành công.
- ADMIN leave thành công.
- OWNER không được leave.
- Sau leave không còn quyền truy cập Workspace.


### UC14 — Delete Workspace

- OWNER soft-delete được.
- ADMIN không delete được.
- MEMBER không delete được.
- Không hard-delete Workspace.
- Workspace deleted không còn truy cập qua API nghiệp vụ.
- Membership/invitation không bị hard-delete ngoài yêu cầu.


## 5. PERMISSION REGRESSION

Xác nhận ít nhất permission matrix sau:

| Action | OWNER | ADMIN | MEMBER |
|---|---|---|---|
| View | PASS | PASS | PASS |
| Update Workspace | PASS | PASS | DENY |
| Create Invitation | PASS | PASS | DENY |
| Remove Member | PASS | PASS | DENY |
| Change Role | PASS | DENY | DENY |
| Leave | DENY | PASS | PASS |
| Delete Workspace | PASS | DENY | DENY |


## 6. TRANSACTION / CONSTRAINT TESTS

Kiểm tra tối thiểu:

- Create Workspace lỗi giữa chừng không để lại Workspace thiếu OWNER.
- Accept Invitation không tạo duplicate membership.
- Invitation status + membership update nhất quán.
- UNIQUE(workspace_id, user_id) hoạt động.
- Concurrent/duplicate request không làm dữ liệu sai nếu test setup hiện tại hỗ trợ kiểm tra hợp lý.

Không xây concurrency framework phức tạp chỉ cho stage này.


## 7. ERROR CONTRACT

Chỉ cần đủ coverage để xác nhận Workspace APIs vẫn dùng Error Contract chung.

Kiểm tra ít nhất:

- unauthorized
- forbidden
- not found
- business conflict
- invalid invitation

Không lặp cùng một format test trên mọi endpoint.


## 8. BUG FIX RULE

Nếu test phát hiện bug implementation:

- sửa tối thiểu source Workspace liên quan,
- chạy lại targeted test bị ảnh hưởng.

Nếu cần thay đổi:

- API contract
- database contract
- permission rule
- nghiệp vụ UC06–UC14

thì DỪNG và báo Tech Lead.

Không tự đổi contract để làm test pass.


## 9. KHÔNG LÀM

Không:

- làm Frontend
- thêm API mới ngoài Phase 2B
- refactor Account/Auth
- chạy lại toàn bộ Phase 1 tests
- thêm Channel/Chat
- thêm Redis/WebSocket
- thêm feature mới


## 10. VERIFICATION

Trong quá trình sửa:

chỉ chạy targeted tests.

Cuối stage:

chạy toàn bộ Workspace Phase 2C test suite MỘT lần.

Backend startup phải PASS.

Không chạy frontend build.


## 11. DONE KHI

- Test UC06–UC14 đầy đủ theo file này.
- Workspace tests PASS.
- Permission tests PASS.
- Invitation tests PASS.
- Transaction/constraint tests PASS.
- Không skip test để làm suite xanh.
- Không thay đổi contract/nghiệp vụ.
- Backend startup PASS.
- Không còn blocker Phase 2.


## 12. HANDOFF

Sau khi PASS:

Cập nhật ngắn `README.md`:

- Phase 2A: DONE
- Phase 2B: DONE
- Phase 2C: DONE
- Next: Phase 2D — Workspace Frontend
- Latest handoff:
  `docs/progress/phase-2c-verification.md`

Tạo:

`docs/progress/phase-2c-verification.md`

Chỉ ghi:

- Status
- Tests total / passed / failed
- Files changed
- Bugs fixed
- Remaining issues
- Next stage

Không lưu full test log.


## 13. OUTPUT CHAT

Chỉ trả:

DONE hoặc FAILED
Tests: <passed>/<failed>
Verification: PASS/FAIL
Files changed: ...
Handoff: docs/progress/phase-2c-verification.md
Remaining issue: ...

Không giải thích.
Không paste code.
Không paste full log.