# PHASE 2E — WORKSPACE INTEGRATION & REGRESSION

## 1. MỤC TIÊU

Nghiệm thu cuối Phase 2.

Xác nhận toàn bộ UC06–UC14 hoạt động ổn định theo luồng:

Frontend
→ Backend
→ PostgreSQL

Không phát triển chức năng mới.
Không lặp lại toàn bộ verification đã PASS ở Phase 2D.


## 2. NGỮ CẢNH

Chỉ đọc khi cần:

1. `README.md`
2. `docs/progress/phase-2d-verification.md`
3. File này
4. Source liên quan trực tiếp nếu phát hiện lỗi

Không đọc lại Phase 2A–2D requirements.
Không đọc toàn bộ `docs/use-cases.md`.

Chỉ tra UC06–UC14 nếu cần đối chiếu nghiệp vụ.


## 3. PHẠM VI REGRESSION

Thực hiện một vòng final regression ngắn cho:

- UC06 — Create Workspace
- UC07 — List/View Workspace
- UC08 — Create Invitation
- UC09 — Accept/Decline Invitation
- UC10 — Update Workspace
- UC11 — Member Management
- UC12 — Role Management
- UC13 — Leave Workspace
- UC14 — Delete Workspace


## 4. FINAL FLOWS

Kiểm tra tối thiểu:

### Flow A — Owner lifecycle

1. User tạo Workspace.
2. User trở thành OWNER.
3. Workspace xuất hiện trong danh sách.
4. OWNER update Workspace.
5. OWNER tạo invitation.
6. Thành viên khác join.
7. OWNER xem member list.
8. OWNER đổi MEMBER → ADMIN.
9. OWNER remove member phù hợp.
10. OWNER delete Workspace.
11. Workspace không còn truy cập được.


### Flow B — Member lifecycle

1. User nhận invitation.
2. Accept → MEMBER.
3. MEMBER xem Workspace.
4. MEMBER không có quyền update/invite/change role/delete.
5. MEMBER leave Workspace.
6. Sau leave không còn truy cập Workspace.


### Flow C — Admin lifecycle

1. MEMBER được OWNER đổi thành ADMIN.
2. ADMIN update Workspace được.
3. ADMIN invite được.
4. ADMIN remove MEMBER được.
5. ADMIN không change role.
6. ADMIN không delete Workspace.
7. ADMIN leave Workspace được.


## 5. REGRESSION RULE

Không chạy lại từng test/flow đã PASS ở Phase 2D nếu không cần.

Chỉ cần:

- final end-to-end lifecycle flows
- kiểm tra permission quan trọng
- kiểm tra persistence sau reload/request mới
- kiểm tra soft-delete cuối flow

Nếu sửa Frontend:

chạy targeted check liên quan + `npm run lint` / `npm run build` khi cần.

Nếu sửa Backend:

chạy targeted Backend tests liên quan.

Không chạy toàn bộ Phase 1 regression.


## 6. BUG FIX RULE

Nếu phát hiện bug:

- sửa tối thiểu đúng nguyên nhân
- chỉ test lại flow bị ảnh hưởng
- sau đó chạy lại final flow tương ứng

Không thay đổi API/database/business contract.

Nếu cần thay đổi contract:

DỪNG và báo Tech Lead.


## 7. KHÔNG LÀM

Không triển khai:

- Channel
- Chat
- WebSocket
- Study Room
- Documents
- AI/RAG
- Admin toàn hệ thống
- feature Workspace mới ngoài UC06–UC14


## 8. DEFINITION OF DONE

Phase 2 hoàn thành khi:

- UC06–UC14 PASS
- OWNER lifecycle PASS
- MEMBER lifecycle PASS
- ADMIN lifecycle PASS
- Permission rules đúng
- Invitation flow ổn định
- Membership/role flow ổn định
- Leave/Delete flow ổn định
- PostgreSQL persistence đúng
- Soft-delete đúng
- Không còn blocker Phase 2


## 9. HANDOFF

Sau khi PASS:

Cập nhật `README.md`:

- Phase 2A: DONE
- Phase 2B: DONE
- Phase 2C: DONE
- Phase 2D: DONE
- Phase 2E: DONE
- Phase 2: COMPLETED
- Next: Phase 3
- Latest handoff:
  `docs/progress/phase-2e-verification.md`

Tạo:

`docs/progress/phase-2e-verification.md`

Chỉ ghi:

- Status
- Final flows PASS/FAIL
- Bugs fixed
- Files changed
- Remaining issues
- Phase 2 completion status
- Next stage

Không lưu full log.


## 10. OUTPUT CHAT

Chỉ trả:

DONE hoặc FAILED
Final flows: <passed>/<failed>
Regression: PASS/FAIL
Files changed: ...
Handoff: docs/progress/phase-2e-verification.md
Remaining issue: ...

Không giải thích.
Không paste code.
Không paste log.