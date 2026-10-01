# KLTN — Backend Phase 0 + Phase 1A/1B

Phạm vi: FastAPI, PostgreSQL, SQLAlchemy async, Alembic và nền tảng Account.
Phase 1A thêm models, schemas, repositories, password/JWT/refresh utilities.
Phase 1B thêm API Account và authentication flow UC01–UC05. Chưa có frontend.
Các package Python được quản lý bằng
`pip` và `backend/requirements.txt`; sử dụng Python 3.11 trở lên.

## Chạy local (Bash / WSL)

Cần có Docker Engine hoặc Docker Desktop tích hợp WSL, Docker Compose v2,
Python có `venv`/`pip` và `curl`. Chạy từ thư mục gốc repository.

### 1. Bật PostgreSQL

```bash
cp -n backend/.env.example backend/.env
docker compose --env-file backend/.env up -d --wait postgres
docker compose --env-file backend/.env ps
```

`.env.example` chỉ chứa giá trị mẫu cho local. Khi sửa user/password/database
hoặc port, cập nhật cả `POSTGRES_*` và `DATABASE_URL` tương ứng. Với ký tự đặc
biệt trong credentials, URL-encode phần credentials trong `DATABASE_URL`.
`POSTGRES_*` dùng cho Compose; ứng dụng và Alembic chỉ đọc `DATABASE_URL`.
Volume giữ dữ liệu qua các lần restart; biến khởi tạo PostgreSQL chỉ áp dụng
khi volume còn mới. Không dùng database nghiệp vụ sẵn có cho bước bootstrap.

### 2. Tạo môi trường Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

### 3. Cấu hình security và chạy Alembic

Bổ sung các biến mới từ `.env.example` vào `.env` hiện có, không ghi đè thông
tin database. `JWT_SECRET_KEY` bắt buộc, tối thiểu 32 byte. Với file mẫu có
`JWT_SECRET_KEY=` rỗng, lệnh sau tạo khóa ngẫu nhiên local mà không in ra terminal:

```bash
python -c "from pathlib import Path; import secrets; p=Path('.env'); p.write_text(p.read_text().replace('JWT_SECRET_KEY=\n', 'JWT_SECRET_KEY='+secrets.token_urlsafe(48)+'\n'))"
```

```bash
python -m alembic upgrade head
python -m alembic current
python -m alembic check
```

Revision Phase 1A: `20260924_01`, tạo `users` và `auth_sessions`.
Phase 0 không có revision. Metadata chung là `app.db.base.Base.metadata`;
models được export trong `app/models/__init__.py` để Alembic nhận metadata.

### 4. Start FastAPI

```bash
set -a
source .env
set +a
python -m uvicorn app.main:app --reload
```

`UVICORN_HOST` và `UVICORN_PORT` lấy từ môi trường shell. Ứng dụng đọc cấu hình
bằng pydantic-settings từ `backend/.env`, ưu tiên biến môi trường hiện có.
Startup thực thi `SELECT 1` bằng async engine; nếu kết nối thất bại, startup
thất bại. `get_db` tạo session riêng cho từng request và tự đóng session;
transaction commit thuộc trách nhiệm service khi có nghiệp vụ.

### 5. Gọi thử API (terminal Bash thứ hai, từ root repository)

```bash
set -a
source backend/.env
set +a
curl --fail-with-body -i "http://${UVICORN_HOST}:${UVICORN_PORT}/api/v1/health"
```

Kết quả yêu cầu: HTTP 200 và `{"status":"ok"}`. Endpoint là liveness;
kết nối DB được kiểm tra riêng khi startup. CORS chỉ cho phép origin
`FRONTEND_URL`, cho phép credentials, GET/POST/PATCH và header Authorization.
Schema phản hồi health nằm trong
`app/schemas/health.py`; không có business logic trong router.

Không triển khai Frontend trong lượt này.

## PostgreSQL cục bộ trên Windows

Khi PostgreSQL chạy trên Windows, sử dụng Python Windows để `127.0.0.1` trỏ
đúng máy đang chạy database. Không cần Docker trong cách chạy này.
Giữ `backend/.env` đã cấu hình; môi trường Windows `.venv-win` tách khỏi WSL `.venv`.

PowerShell, bắt đầu từ thư mục repository (Python 3.12 đã cài ở đường dẫn bên dưới):

```powershell
cd backend
& "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe" -m venv .venv-win
.\.venv-win\Scripts\python.exe -m pip install -r requirements.txt
.\.venv-win\Scripts\python.exe -m alembic upgrade head
.\.venv-win\Scripts\python.exe -m alembic current
.\.venv-win\Scripts\python.exe -m alembic check
$env:UVICORN_HOST = "127.0.0.1"
$env:UVICORN_PORT = "8000"
.\.venv-win\Scripts\python.exe -m uvicorn app.main:app
```

Đặt `UVICORN_HOST`/`UVICORN_PORT` tương ứng `.env`. Các biến `UVICORN_*` phải
có trong môi trường shell; Uvicorn không tự đọc chúng từ file `.env` của ứng dụng.
Terminal PowerShell khác:

```powershell
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/api/v1/health
```

### MinIO Docker trên Windows (Phase 3B3)

Backend chạy trực tiếp trên Windows; MinIO chạy trong Docker Desktop bằng
Compose tại project root. Giữ PostgreSQL hiện có. Docker Desktop quản lý named
volume `minio_data` trong data location đã cấu hình `D:\DockerData`; không tạo
thư mục dữ liệu MinIO trong project.

Trong `backend/.env` (được gitignore), cấu hình các biến `OBJECT_STORAGE_*`
theo `.env.example`, thay credential mẫu bằng credential local. Compose dùng
cùng access key/secret key để khởi tạo MinIO. Endpoint cho backend trên host là
`http://127.0.0.1:9000`, `OBJECT_STORAGE_SECURE=false`, bucket `chat-attachments`.
Nếu đổi `MINIO_API_PORT`, cập nhật port trong endpoint tương ứng.

PowerShell tại project root, sau khi Docker Engine hoạt động:

```powershell
docker compose --env-file backend/.env config --quiet
docker compose --env-file backend/.env up -d minio minio-init
docker compose --env-file backend/.env ps -a
```

Service `minio` phải healthy và `minio-init` phải exit 0. Initializer chờ healthcheck,
tạo bucket idempotent và tắt anonymous access. Console: `http://127.0.0.1:9001`.
Các port chỉ bind loopback. Image sử dụng registry Quay chính thức của MinIO:
[server documentation](https://github.com/minio/minio/blob/master/docs/docker/README.md),
[client publishing script](https://github.com/minio/mc/blob/master/docker-buildx.sh).

Sau restart máy, bật Docker Desktop và chạy lại lệnh `up` ở trên; named volume
được giữ lại. Không chạy `down -v` nếu cần giữ dữ liệu. Khởi động backend theo
phần Windows ở trên sau khi kiểm tra Python/venv và PostgreSQL hoạt động.
StorageService dùng boto3/S3v4, region `us-east-1`, URL download ký trong 300 giây;
không cần thêm biến region hoặc thay storage abstraction.

Cấu hình Compose chưa đồng nghĩa live verification PASS. Xem trạng thái thực tế
ở [Phase 3B3 verification](docs/progress/phase-3b3-verification.md).

## Quy ước Phase 1A

- User UUID; email trim/lowercase, unique và CHECK chuẩn hóa ở database.
  `status`/`system_role` là string enum có CHECK constraint, mặc định `ACTIVE`/`USER`.
- Timestamps dùng `TIMESTAMP WITH TIME ZONE`; utilities tạo datetime UTC.
  `updated_at` cập nhật khi ghi qua SQLAlchemy; không có database trigger.
- Argon2id hash/verify chạy trong worker thread để không chặn event loop.
  JWT HS256 chỉ mang `sub`, `sid`, `type`, `iat`, `exp`, mặc định 15 phút.
  Refresh token dùng 32 byte ngẫu nhiên; database chỉ lưu SHA-256 hex 64 ký tự.
- `JWT_SECRET_KEY` đọc từ môi trường; `.env` được ignore. Các biến lifetime,
  cookie name và cookie secure nằm trong `.env.example`. Production yêu cầu
  `COOKIE_SECURE=true`.
- Repositories chỉ query/flush, không commit. Service ở Phase 1B sở hữu
  transaction và xử lý lỗi uniqueness. Rotation dùng compare-and-swap hash cũ,
  đồng thời kiểm tra session chưa revoke/hết hạn trong câu UPDATE.
- Schemas cấm field request ngoài contract, che password bằng `SecretStr`.
  Response schemas mô tả phần `data`; envelope và error handlers được tích hợp ở Phase 1B.
- Kiểm tra User ACTIVE, password mới khác password hiện tại, transaction thay
  password + revoke sessions, cookie HttpOnly/SameSite/Path và CORS credentials
  đã được tích hợp ở Phase 1B.

Tham khảo thư viện: [argon2-cffi](https://argon2-cffi.readthedocs.io/en/stable/howto.html),
[PyJWT](https://pyjwt.readthedocs.io/en/latest/usage.html).

## Kiểm tra nền tảng Phase 1A

Dùng `unittest` có sẵn trong Python, không thêm test framework.
Đây là kiểm tra foundation, chưa phải bộ kiểm thử API UC01–UC05 của Phase 1C.

Chuẩn bị database riêng bằng tài khoản quản trị PostgreSQL:

```sql
CREATE DATABASE kltn_test OWNER kltn;
```

`TEST_DATABASE_URL` phải trỏ đến `kltn_test`, dùng driver `postgresql+asyncpg`.
Tests từ chối chạy trên development database, database có bảng ngoài phạm vi
hoặc có dữ liệu account. Migration round-trip chỉ chạy trên database test.
Mỗi repository test dùng transaction ngoài và savepoint; teardown rollback,
giữ schema nhưng không giữ dữ liệu fixture.

Từ `backend`, PowerShell:

```powershell
.\.venv-win\Scripts\python.exe -m unittest tests.test_foundation tests.test_foundation_database -v
```

Với Python/venv Linux và PostgreSQL truy cập được từ Linux:

```bash
python -m unittest tests.test_foundation tests.test_foundation_database -v
```

## API Account — Phase 1B

| Method | Path | Thành công |
| --- | --- | --- |
| POST | `/api/v1/auth/register` | 201, user; không tự login |
| POST | `/api/v1/auth/login` | 200, access token + user; set refresh cookie |
| POST | `/api/v1/auth/refresh` | 200, access token mới; rotate refresh cookie |
| POST | `/api/v1/auth/logout` | 204, revoke current session; xóa cookie |
| GET | `/api/v1/users/me` | 200, profile |
| PATCH | `/api/v1/users/me` | 200, profile sau cập nhật full_name |
| POST | `/api/v1/users/me/change-password` | 204, đổi mật khẩu và revoke các session khác |

Request/response theo `docs/phase-1-account-requirements.md`. Có thể xem schemas
và gọi API bằng Swagger tại `/docs`; protected endpoints dùng HTTP Bearer.
Success JSON bọc trong `data`; response 204 không có body. Health giữ nguyên
`{"status":"ok"}`.

Lỗi ứng dụng, validation, 404/405 dùng envelope:

```json
{"error":{"code":"ERROR_CODE","message":"Human readable message","fields":null}}
```

Validation trả dictionary field errors, không trả lại input/password hoặc
Pydantic context. Register confirmation mismatch là `422 VALIDATION_ERROR`;
change-password confirmation mismatch là `422 PASSWORD_CONFIRMATION_MISMATCH`.
Protected API dùng `401 AUTHENTICATION_REQUIRED`, `ACCESS_TOKEN_INVALID`,
`ACCESS_TOKEN_EXPIRED`, `SESSION_INVALID`, `SESSION_EXPIRED`; tài khoản bị khóa
trả `403 ACCOUNT_LOCKED`. Login sai email/password luôn là `401 INVALID_CREDENTIALS`.

Password mới vẫn có giới hạn 8–128 ký tự, không thêm complexity. Password dùng
để đối chiếu khi login/current_password nhận chuỗi không rỗng tối đa 128 ký tự;
nhập password sai nhưng ngắn vẫn trả lỗi xác thực theo contract.

Refresh cookie là HttpOnly, SameSite=Lax, Path=`/api/v1/auth`, Secure theo
`COOKIE_SECURE`; mặc định sống 7 ngày. Refresh thành công giữ nguyên session ID
và đặt hạn mới từ thời điểm rotate. Access token chỉ có trong response; không
có access cookie. Login/refresh response dùng `Cache-Control: no-store`.

Service kiểm tra JWT và User/Session trong database. Trước mutation, trạng thái
được đọc lại dưới row lock theo thứ tự User → AuthSession. Login cũng khóa User
để đồng bộ với đổi mật khẩu. Refresh dùng compare-and-swap hash cũ; chỉ một
request đồng thời có thể rotate thành công. Logout revoke session nên cả access
token chưa hết hạn của session đó cũng mất hiệu lực. Đổi mật khẩu + revoke các
session khác nằm trong một transaction; current session tiếp tục hoạt động.

Không thay đổi migration Phase 1A. Kết quả verification 1B nằm tại
[`docs/phase-1b-verification.md`](docs/phase-1b-verification.md).

## Trạng thái hiện tại

### LiveKit local — Phase 4C

Trong `backend/.env`, thêm `LIVEKIT_URL=ws://localhost:7880`,
`LIVEKIT_API_KEY` (chuỗi ngẫu nhiên) và `LIVEKIT_API_SECRET` (ngẫu nhiên tối thiểu
32 ký tự); giữ các giá trị thật ngoài Git. Backend và LiveKit dùng cùng key/secret.
Khởi động Docker Desktop rồi chạy từ root:

```powershell
docker compose --env-file backend/.env -f docker-compose.livekit.yml config --quiet
docker compose --env-file backend/.env -f docker-compose.livekit.yml up -d livekit
```

Compose này chỉ phục vụ browser trên cùng máy: signaling 7880, RTC TCP 7881,
UDP 7882 đều bind loopback. Khởi động lại backend sau khi cấu hình; chạy
`npm install` ở frontend và build với `NEXT_PUBLIC_API_BASE_URL` như trước.
Browser cần localhost hoặc HTTPS để cấp quyền thiết bị; môi trường ngoài local
cần cấu hình WSS/TLS, địa chỉ ICE và TURN phù hợp.
Tham khảo [LiveKit tokens](https://docs.livekit.io/home/server/generating-tokens)
và [SDK media](https://docs.livekit.io/reference/client-sdk-js/index.html).

Kiểm tra thật bằng hai tài khoản thành viên trong hai browser contexts: cùng join,
A bật mic/camera → B nhận audio/video, A tắt → B thấy OFF, rời/chuyển Channel →
track dừng. Mỗi user có một media identity trong room; tab mới có thể thay kết nối cũ.
Trạng thái kiểm tra hiện tại: [Phase 4C handoff](docs/progress/phase-4c-verification.md).

### Tiến độ

- Phase 1A: DONE
- Phase 1B: DONE
- Phase 1C: DONE
- Phase 1D: DONE
- Phase 1E: DONE
- Phase 1: COMPLETED
- Phase 2A: DONE
- Phase 2B: DONE
- Phase 2C: DONE
- Phase 2D: DONE
- Phase 2E: DONE
- Phase 2: COMPLETED
- Phase 3A: DONE
- Phase 3B1: DONE
- Phase 3B2: DONE
- Phase 3B3: DONE
- Phase 3C: DONE
- Phase 3D: DONE
- Phase 3E: DONE
- Channel & Chat UC15–UC21: COMPLETE
- Phase 4A: DONE — Study Room foundation (join/leave/presence)
- Study Room presence chạy với **một backend worker**, lưu trong bộ nhớ; restart xóa presence.
- Phase 4B: DONE — microphone/camera state và controls (chưa truyền media)
- Phase 4C: DONE — LiveKit/WebRTC media; live smoke 5/5 PASS (Chrome synthetic capture).
- Next: Phase 4D — chưa bắt đầu.
- Latest handoff: [docs/progress/phase-4c-verification.md](docs/progress/phase-4c-verification.md)

Tham khảo cơ chế framework: [FastAPI exception handlers](https://fastapi.tiangolo.com/tutorial/handling-errors/),
[Starlette cookie responses](https://starlette.dev/responses/).
