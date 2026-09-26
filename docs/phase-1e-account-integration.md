# PHASE 1E — ACCOUNT/AUTH INTEGRATION & REGRESSION

## 1. MỤC TIÊU

Nghiệm thu cuối Phase 1 bằng cách kiểm tra tích hợp thực tế:

Frontend
→ Backend
→ PostgreSQL

Phạm vi chỉ gồm UC01–UC05.

Không phát triển chức năng mới.


## 2. NGỮ CẢNH

Chỉ đọc khi cần:

1. `README.md`
2. `docs/progress/phase-1d-verification.md`
3. File này
4. Source liên quan trực tiếp đến lỗi nếu verification fail

Không đọc lại toàn bộ Phase 1A–1D.
Không đọc toàn bộ `docs/use-cases.md`.


## 3. LƯU Ý TRẠNG THÁI 1D

Phase 1D đã được Tech Lead nghiệm thu.

Production build đã PASS trên máy local:

- Next.js compile PASS
- TypeScript PASS
- page generation PASS

Nếu handoff cũ còn ghi FAILED do sandbox build:
cập nhật lại thành DONE.

Không điều tra lại lỗi sandbox cũ.


## 4. INTEGRATION FLOWS

Kiểm tra lần lượt:


### FLOW 1 — REGISTER

Register tài khoản mới.

Expected:

Register
→ thành công
→ chuyển `/login`

Không tự đăng nhập.


### FLOW 2 — LOGIN

Login bằng tài khoản hợp lệ.

Expected:

Login
→ `/app`
→ thông tin User đúng.


### FLOW 3 — AUTH RESTORE

Sau login:

reload browser.

Expected:

User vẫn authenticated
nhờ refresh session.


### FLOW 4 — INVALID LOGIN

Sai password.

Expected:

Hiển thị lỗi credentials phù hợp.

Không crash.


### FLOW 5 — PROFILE

`/profile`

Kiểm tra:

- xem full_name + email
- email read-only
- sửa full_name
- save
- reload
- dữ liệu mới vẫn tồn tại


### FLOW 6 — CANCEL PROFILE EDIT

Thay đổi full_name nhưng chọn hủy.

Expected:

Không lưu thay đổi.


### FLOW 7 — CHANGE PASSWORD

Đổi password thành công.

Expected:

- current session vẫn hoạt động
- password cũ không login được
- password mới login được


### FLOW 8 — LOGOUT

Logout.

Expected:

- Backend logout được gọi
- session hiện tại bị kết thúc
- chuyển `/login`
- protected routes không còn truy cập được


### FLOW 9 — PROTECTED ROUTES

Khi chưa authenticated, truy cập:

- `/app`
- `/profile`
- `/settings/security`

Expected:

Không hiển thị nội dung protected.
Điều hướng về login theo implementation hiện tại.


## 5. REGRESSION

Không chạy lại mọi thứ một cách dư thừa.

Nếu source Backend không thay đổi từ Phase 1C:
không cần chạy lại toàn bộ test suite nhiều lần.

Chạy một lần regression cần thiết để xác nhận Phase 1 vẫn ổn.

Nếu sửa Backend:
chạy targeted Backend tests liên quan.

Nếu sửa Frontend:
chạy:

npm run lint
npm run build

sau thay đổi.


## 6. BUG FIX RULE

Nếu integration phát hiện bug:

- sửa tối thiểu đúng nguyên nhân
- chỉ test lại flow bị ảnh hưởng
- sau đó chạy regression cần thiết

Không refactor ngoài phạm vi.

Không thay đổi nghiệp vụ/API contract.

Nếu cần thay đổi contract:
DỪNG và báo Tech Lead.


## 7. KHÔNG LÀM

Không triển khai:

- Workspace
- Channel
- Chat
- Study Room
- Document
- AI/RAG
- Admin
- tính năng Account mới

Không thêm framework/tool test lớn chỉ để phục vụ Phase 1E.


## 8. DEFINITION OF DONE

Phase 1 hoàn thành khi:

- UC01 Register PASS
- UC02 Login PASS
- Auth restore PASS
- UC03 Logout PASS
- UC04 Profile PASS
- UC05 Change Password PASS
- Protected routes PASS
- Frontend ↔ Backend thật PASS
- PostgreSQL persistence PASS
- Không còn blocker thuộc Phase 1


## 9. HANDOFF

Khi hoàn thành:

Cập nhật `README.md`:

- Phase 1A: DONE
- Phase 1B: DONE
- Phase 1C: DONE
- Phase 1D: DONE
- Phase 1E: DONE
- Phase 1: COMPLETED
- Next: Phase 2
- Latest handoff:
  `docs/progress/phase-1e-verification.md`

Tạo:

`docs/progress/phase-1e-verification.md`

Chỉ ghi:

- Status
- Integration flows PASS/FAIL
- Bugs fixed
- Files changed
- Remaining issues
- Phase 1 completion status
- Next stage

Không lưu full logs.


## 10. OUTPUT CHAT

Chỉ trả:

DONE hoặc FAILED
Integration: <passed>/<failed>
Regression: PASS/FAIL
Files changed: ...
Handoff: ...
Remaining issue: ...

Không giải thích.
Không paste code.
Không paste log.