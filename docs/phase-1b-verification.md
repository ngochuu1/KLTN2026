# Phase 1B — Backend Account APIs

Ngày verification: 2026-09-24.

## STAGE COMPLETED

Phase 1B: UC01–UC05 và authentication flow phía Backend.
Đã đọc UC01–UC05 trong `docs/use-case.md` và requirements Phase 1.
Chưa chuyển sang Phase 1C hoặc Frontend.

## FILES CREATED

- `backend/app/api/dependencies.py`
- `backend/app/api/cookies.py`
- `backend/app/api/v1/auth.py`
- `backend/app/api/v1/users.py`
- `backend/app/core/exceptions.py`
- `backend/app/core/exception_handlers.py`
- `backend/app/schemas/common.py`
- `backend/app/services/auth_service.py`
- `backend/app/services/user_service.py`
- `docs/phase-1b-verification.md`

## FILES MODIFIED

- `backend/app/main.py`: error handlers, CORS credentials/methods/Authorization.
- `backend/app/api/v1/router.py`: mount Auth và User routers.
- `backend/app/core/security.py`: verify bằng dummy Argon2 hash khi email không tồn tại.
- `backend/app/repositories/user_repository.py`: hỗ trợ row lock khi tìm email,
  nhận diện riêng lỗi unique email để service map HTTP 409, kể cả đăng ký đồng thời.
- `backend/app/schemas/fields.py`, `auth.py`, `user.py`: tách password mới với
  password cần đối chiếu; không trả 422 thay cho lỗi xác thực khi nhập sai password ngắn.
- `README.md`: hướng dẫn và mô tả API/transaction/error contract.

## DEPENDENCIES ADDED

Không thêm dependency.

## DATABASE CHANGES

Không đổi schema hoặc tạo revision mới. Giữ revision `20260924_01`.
Service sở hữu transaction. Repository không tự commit.
Các mutation khóa User trước AuthSession; change password và revoke các session
khác nằm trong cùng transaction. Refresh rotation cập nhật hash có điều kiện,
không tạo session mới.

## API CHANGES

| Method | Endpoint | Success |
| --- | --- | --- |
| POST | `/api/v1/auth/register` | 201 |
| POST | `/api/v1/auth/login` | 200 |
| POST | `/api/v1/auth/refresh` | 200 |
| POST | `/api/v1/auth/logout` | 204, body rỗng |
| GET | `/api/v1/users/me` | 200 |
| PATCH | `/api/v1/users/me` | 200 |
| POST | `/api/v1/users/me/change-password` | 204, body rỗng |

JSON success có envelope `data`; error có envelope `error` với `code`, `message`,
`fields`. Không đưa input/password/token vào validation error.
Health endpoint giữ nguyên contract Phase 0.

## TESTS EXECUTED

- Chạy lại 20 kiểm tra foundation hiện có của Phase 1A: 20/20 đạt.
- Chạy verification tạm thời bằng HTTP thực tế qua Uvicorn và PostgreSQL
  `kltn_test`: 53 kiểm tra đạt. Script/log nằm trong `.venv-win` được ignore;
  đây không phải bộ automated API tests chính thức của Phase 1C.
- Dữ liệu verification được tạo qua API, không dùng mock API, không dùng SQLite.
- Kiểm tra trực tiếp database cho password Argon2id, refresh hash, session ID,
  số session và trạng thái revoke. Chỉ xóa đúng fixtures do verification tạo.

Các nhóm đã xác minh:

- Register: normalization, role/status mặc định, không tự login/tạo session,
  missing/invalid/extra fields, confirmation mismatch, duplicate email.
- Login: thành công; sai email/password trả generic error.
- Profile: yêu cầu authentication, đọc/cập nhật full_name, reject email/field lạ.
- Refresh: cookie mới/hash mới, giữ session ID/số session; token cũ bị từ chối.
- Logout: 204 body rỗng, xóa cookie đúng path, cả access và refresh bị từ chối sau revoke.
- Change password: kiểm tra current password/new password/confirmation;
  giữ current session, revoke session khác; password cũ không login được.
- Account LOCKED: login đúng password, refresh và protected API đều bị từ chối.
- Session expired/revoked: từ chối refresh và protected API.
- Concurrency: hai register cùng email → một 201, một 409;
  hai refresh cùng token → một 200, một 401.
- Cookie HttpOnly, SameSite=Lax, Path, Secure theo cấu hình, Max-Age;
  CORS preflight cho Authorization/PATCH và credentials, origin lạ không được cấp CORS.
- Error envelope cho authentication, validation, malformed JSON, 404/405.

## VERIFICATION RESULT

- Import toàn bộ application modules: đạt.
- `alembic upgrade head`: thành công; `alembic check`: không có schema drift.
- Migration round-trip trong regression 1A chỉ chạy trên `kltn_test`.
- Startup Uvicorn với PostgreSQL test: thành công.
- Đã restart server development trên `http://127.0.0.1:8000`; log xác nhận
  `Application startup complete`, OpenAPI có 7 API Account và health.
- HTTP health: 200, `{"status":"ok"}`.
- Dữ liệu fixtures trong `kltn_test` đã cleanup; không tạo account test trên `kltn`.

## ISSUES / WARNINGS

Không có lỗi còn tồn tại trong phạm vi đã verification.
Chưa triển khai hoặc nghiệm thu Phase 1C; bộ API tests chính thức và các kiểm tra
Frontend/integration browser vẫn thuộc stage tiếp theo.
Refresh thành công gia hạn session thêm lifetime cấu hình (mặc định 7 ngày).
Access token được xác minh cùng trạng thái session trong database trên protected requests.

Dừng chờ Tech Lead review.
