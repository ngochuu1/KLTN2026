# PHASE 1C — ACCOUNT / AUTH BACKEND TESTS

## 1. MỤC TIÊU

Kiểm thử Backend Account/Auth đã hoàn thành ở Phase 1A và Phase 1B.

Phase này chỉ tập trung vào:

- UC01 — Đăng ký tài khoản
- UC02 — Đăng nhập
- UC03 — Đăng xuất
- UC04 — Xem và cập nhật thông tin cá nhân
- UC05 — Đổi mật khẩu
- Refresh Authentication là cơ chế kỹ thuật hỗ trợ duy trì phiên đăng nhập.

Không triển khai Frontend.

Không mở rộng nghiệp vụ.


---

# 2. NGỮ CẢNH CẦN ĐỌC

Trước khi thực hiện chỉ cần đọc:

1. `README.md`
2. `docs/progress/phase-1b-verification.md` nếu file tồn tại.
3. File này: `docs/phase-1c-account-tests.md`
4. Source Backend Account/Auth liên quan trực tiếp đến test.

Không đọc lại toàn bộ các Phase trước.

Không đọc toàn bộ `docs/use-cases.md`.

Chỉ tra đúng UC01–UC05 trong `docs/use-cases.md` nếu phát hiện hành vi implementation không rõ hoặc có khả năng lệch nghiệp vụ.


---

# 3. NGUYÊN TẮC

Mục tiêu của Phase 1C là:

TEST IMPLEMENTATION HIỆN TẠI

không phải:

REDESIGN ACCOUNT/AUTH.


Nếu test phát hiện implementation sai nhưng contract hiện tại rõ ràng:

- sửa bug,
- chạy lại test liên quan.

Nếu phát hiện cần thay đổi:

- API contract,
- Database contract,
- Authentication strategy,
- nghiệp vụ UC,

thì:

DỪNG

và báo Tech Lead.

Không tự thay đổi contract để làm test pass.


---

# 4. TEST ENVIRONMENT

Automated test không được sử dụng Development Database có dữ liệu thật.

Phải sử dụng PostgreSQL test database riêng.

Ưu tiên biến môi trường:

TEST_DATABASE_URL

Không thay PostgreSQL bằng SQLite chỉ để test dễ hơn.

Test phải:

- độc lập với thứ tự chạy,
- không phụ thuộc dữ liệu test trước,
- cleanup dữ liệu sau test hoặc sử dụng transaction isolation phù hợp.


---

# 5. TEST TOOLING

Sử dụng test framework phù hợp với Backend Python/FastAPI hiện tại.

Ưu tiên reuse dependencies đã có.

Chỉ thêm dependency test nếu thực sự thiếu.

Không thêm package không cần thiết.

Test HTTP API qua FastAPI application/test client phù hợp với async stack hiện tại.

Không gọi Backend production thật.


---

# 6. UC01 — REGISTER TESTS

Endpoint hiện tại của Phase 1B phải được test theo contract đã triển khai.

Bắt buộc bao phủ:

### R1 — Register thành công

Input hợp lệ.

Kiểm tra:

- HTTP 201.
- User được tạo.
- email được lưu đúng.
- full_name được lưu đúng.
- status mặc định đúng.
- system_role mặc định đúng.
- password_hash tồn tại.
- plain password KHÔNG được lưu.
- Response không chứa password/password_hash.
- Không tạo auth session sau register.


### R2 — Thiếu required field

Ví dụ:

- full_name thiếu,
- email thiếu,
- password thiếu,
- confirm_password thiếu.

Expected:

Validation error.


### R3 — Email sai định dạng

Expected:

Validation error.


### R4 — Password không đạt policy

Policy Phase 1:

8–128 ký tự.

Expected:

Validation error.


### R5 — Confirm password không khớp

Expected:

Validation error theo contract hiện tại.


### R6 — Duplicate email

Register email đã tồn tại.

Expected:

HTTP 409
EMAIL_ALREADY_EXISTS


### R7 — Email normalization

Register:

User@Test.COM

Sau đó thử register/login bằng dạng lowercase tương ứng.

Database không được tạo hai tài khoản khác nhau chỉ vì khác uppercase/lowercase.


---

# 7. UC02 — LOGIN TESTS

Bắt buộc:


### L1 — Login thành công

Kiểm tra:

- HTTP 200.
- Access Token được trả về.
- token_type đúng.
- expires_in đúng contract.
- User data đúng.
- Refresh Cookie được set.
- Auth Session được tạo trong database.


### L2 — Email không tồn tại

Expected:

HTTP 401
INVALID_CREDENTIALS


### L3 — Sai password

Expected:

HTTP 401
INVALID_CREDENTIALS


L2 và L3 không được trả message cho phép phân biệt email có tồn tại hay không.


### L4 — Account LOCKED

Password đúng nhưng status = LOCKED.

Expected:

HTTP 403
ACCOUNT_LOCKED

Không tạo auth session.


### L5 — Password hash verification

Password đúng login thành công.

Password sai login thất bại.

Không kiểm tra bằng cách so sánh plaintext.


---

# 8. REFRESH AUTHENTICATION TESTS

Bắt buộc:


### F1 — Refresh thành công

Với refresh cookie/session hợp lệ:

- HTTP 200.
- Access Token mới được trả.
- Refresh Cookie mới được set.


### F2 — Refresh token rotation

Sau refresh thành công:

Refresh token cũ phải mất hiệu lực.


### F3 — Reuse refresh token cũ

Thử dùng token trước rotation.

Expected:

request bị từ chối.


### F4 — Session revoked

Session có `revoked_at`.

Expected:

refresh thất bại.


### F5 — Session expired

Session hết hạn.

Expected:

refresh thất bại.


### F6 — Account LOCKED

Session còn hiệu lực nhưng User đã bị LOCKED.

Expected:

HTTP 403
ACCOUNT_LOCKED


### F7 — Refresh token không hợp lệ

Token không tồn tại/không match hash.

Expected:

authentication error theo contract.


---

# 9. UC03 — LOGOUT TESTS

Bắt buộc:


### O1 — Logout thành công

User đang authenticated.

Expected:

- HTTP 204.
- Current Auth Session bị revoke.
- Refresh Cookie được clear.


### O2 — Refresh sau Logout

Sau khi logout:

refresh bằng session cũ phải thất bại.


### O3 — Session khác

Nếu User có nhiều auth session:

logout current session không được tự động revoke session khác.

Việc revoke các session khác chỉ xảy ra ở nghiệp vụ được quy định khác.


---

# 10. UC04 — PROFILE TESTS

Bắt buộc:


### P1 — Get Current User

Authenticated User gọi profile.

Expected:

HTTP 200.

Response có:

- id
- full_name
- email
- status
- system_role
- timestamps theo contract.

Không có:

- password
- password_hash
- refresh token/hash


### P2 — Unauthenticated

Không có Access Token.

Expected:

HTTP 401.


### P3 — Update full_name

Authenticated User update full_name hợp lệ.

Expected:

- HTTP 200.
- database được update.
- GET lại profile thấy giá trị mới.


### P4 — Invalid full_name

Expected:

Validation error.


### P5 — Update Email

Phase 1 không cho phép đổi email.

Client gửi email trong update request phải bị reject.

Không silently ignore.


### P6 — Cancel Profile

Không cần Backend automated test riêng.

Đây là hành vi Frontend của Phase 1D.


---

# 11. UC05 — CHANGE PASSWORD TESTS

Bắt buộc:


### C1 — Change password thành công

Input:

- current_password đúng,
- new_password hợp lệ,
- confirmation match.

Expected:

HTTP 204.

Sau đó:

- password cũ login thất bại.
- password mới login thành công.


### C2 — Current password sai

Expected:

CURRENT_PASSWORD_INCORRECT

Password database không thay đổi.


### C3 — New password không hợp lệ

Ví dụ dưới 8 ký tự.

Expected:

Validation error.


### C4 — Confirmation mismatch

Expected:

PASSWORD_CONFIRMATION_MISMATCH hoặc error code đúng contract Phase 1B.


### C5 — New password giống current password

Expected:

NEW_PASSWORD_SAME_AS_CURRENT


### C6 — Other Sessions Revoked

User có:

Session A = current session
Session B = session khác

Sau Change Password:

- Session A vẫn hoạt động.
- Session B bị revoke.


---

# 12. ERROR CONTRACT TESTS

Không cần test mọi error response lặp lại ở mọi endpoint.

Chỉ cần đủ để chứng minh format lỗi thống nhất:

{
  "error": {
    "code": "...",
    "message": "...",
    "fields": ...
  }
}

Tối thiểu kiểm tra:

- một Validation Error,
- một Business Error,
- một Authentication Error,
- một Account Locked Error.


---

# 13. SECURITY ASSERTIONS

Không cần penetration test trong Phase 1C.

Chỉ cần automated assertions cho các điểm liên quan trực tiếp implementation:

- Password không lưu plaintext.
- password_hash không trả qua API.
- Refresh token plaintext không lưu DB.
- Invalid credentials không tiết lộ email tồn tại hay không.
- LOCKED account không login.
- LOCKED account không refresh.
- Revoked session không refresh.
- Expired session không refresh.


---

# 14. PHẠM VI SỬA BUG

Nếu test phát hiện lỗi:

Được phép sửa trực tiếp các file Backend Account/Auth liên quan.

Ví dụ:

- auth service,
- user service,
- repository,
- schema validation,
- security utilities,
- auth dependency,
- exception handler.

Không refactor code không liên quan.

Không sửa API path/request/response contract chỉ để làm test pass.


---

# 15. KHÔNG LÀM TRONG PHASE 1C

Không:

- làm Frontend,
- thêm Workspace,
- thêm Forgot Password,
- thêm Email Verification,
- thêm OAuth,
- thêm Redis,
- thêm MinIO,
- thêm rate limit,
- đổi Auth architecture,
- chạy full frontend build,
- chạy full-project regression,
- test các module chưa tồn tại.


---

# 16. VERIFICATION

Chạy test Backend Account/Auth của Phase 1.

Ưu tiên:

targeted tests

thay vì toàn bộ project.

Nếu có test fail:

- xác định nguyên nhân,
- sửa bug nếu nằm trong phạm vi,
- chỉ chạy lại test bị ảnh hưởng trước,
- cuối cùng chạy toàn bộ test suite của Phase 1C một lần.


---

# 17. DEFINITION OF DONE

Phase 1C đạt khi:

- Test environment sử dụng database riêng.
- Các test bắt buộc của file này được triển khai.
- Tất cả Phase 1C tests PASS.
- Không thay đổi contract/nghiệp vụ.
- Không có test skip chỉ để đạt trạng thái xanh.
- Không có test giả/mocking làm mất ý nghĩa integration với PostgreSQL.
- Backend vẫn start bình thường.


---

# 18. HANDOFF

Sau khi hoàn thành và tests PASS:

## Cập nhật README.md

Chỉ cập nhật mục trạng thái hiện tại:

- Phase 1A: DONE
- Phase 1B: DONE
- Phase 1C: DONE
- Current next stage: Phase 1D — Frontend
- Latest handoff: docs/progress/phase-1c-verification.md

Không ghi test log dài vào README.


## Tạo:

docs/progress/phase-1c-verification.md

Nội dung ngắn gọn:

# Phase 1C Verification

Status:
DONE / FAILED

Tests:
- total
- passed
- failed

Files changed:
- ...

Bugs fixed:
- ...

Remaining issues:
- ...

Next:
Phase 1D — Account/Auth Frontend


Không lưu full terminal output.


---

# 19. OUTPUT CHAT

Output chat tối đa ngắn gọn:

DONE hoặc FAILED

Tests: <passed>/<failed>

Files changed:
- ...

Handoff:
docs/progress/phase-1c-verification.md

Remaining issue:
<none hoặc mô tả ngắn>

Không chào hỏi.

Không giải thích lý thuyết.

Không paste code.

Không paste full terminal log.