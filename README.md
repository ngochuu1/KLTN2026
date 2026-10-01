# KLTN2026 – Nền tảng học tập cộng tác trực tuyến

Đề tài khóa luận:

**Xây dựng nền tảng học tập cộng tác trực tuyến kết hợp phòng tự học ảo và trợ lý AI giải đáp tài liệu**

Hệ thống hỗ trợ sinh viên/học viên học tập và cộng tác trực tuyến thông qua Workspace, Channel, Chat, phòng tự học trực tuyến, tài liệu học tập và trợ lý AI.

---

## 1. Công nghệ sử dụng

### Frontend
- Next.js
- React
- TypeScript
- LiveKit Client SDK

### Backend
- Python 3.11+
- FastAPI
- SQLAlchemy Async
- Alembic
- WebSocket

### Database
- PostgreSQL

### Realtime / Media
- WebSocket
- WebRTC
- LiveKit

### Object Storage
- MinIO

### AI / RAG
- pgvector
- RAG

> Phần AI/RAG sẽ được tích hợp ở các giai đoạn sau của hệ thống.

---

## 2. Các chức năng chính

Hệ thống được phát triển theo các nhóm chức năng:

- Quản lý tài khoản và xác thực
- Workspace và thành viên
- Channel
- Chat realtime
- Reaction và attachment
- Study Room
- Microphone / Camera
- Video realtime bằng WebRTC
- Chia sẻ màn hình
- Pomodoro dùng chung
- Quản lý tài liệu học tập
- Trợ lý AI sử dụng RAG
- Theo dõi tiến độ học tập
- Thống kê và báo cáo

---

## 3. Cấu trúc project

```text
KLTN2026/
│
├── backend/
│   ├── app/
│   ├── alembic/
│   ├── tests/
│   ├── scripts/
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   ├── tests/
│   ├── package.json
│   └── package-lock.json
│
├── docker-compose.yml
├── docker-compose.livekit.yml
└── README.md
```

---

# 4. Yêu cầu môi trường

Máy cần cài:

- Git
- Python 3.11 trở lên
- Node.js
- npm
- PostgreSQL
- Docker Desktop
- Docker Compose v2

Khuyến nghị trên Windows:

- Python 3.12
- Node.js 22
- PostgreSQL
- Docker Desktop

---

# 5. Clone project

```bash
git clone https://github.com/ngochuu1/KLTN2026.git
cd KLTN2026
```

---

# 6. Cấu hình Backend

Đi vào thư mục backend:

```powershell
cd backend
```

Tạo virtual environment:

```powershell
python -m venv .venv-win
```

Cài dependencies:

```powershell
.\.venv-win\Scripts\python.exe -m pip install -r requirements.txt
```

---

# 7. Cấu hình biến môi trường

Copy:

```text
backend/.env.example
```

thành:

```text
backend/.env
```

Không commit file `.env` lên Git.

Cần cấu hình các nhóm biến:

```env
# PostgreSQL
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_DB=
DATABASE_URL=

# JWT
JWT_SECRET_KEY=

# Frontend
FRONTEND_URL=http://localhost:3000

# MinIO / Object Storage
OBJECT_STORAGE_ENDPOINT=http://127.0.0.1:9000
OBJECT_STORAGE_ACCESS_KEY=
OBJECT_STORAGE_SECRET_KEY=
OBJECT_STORAGE_BUCKET=chat-attachments
OBJECT_STORAGE_SECURE=false

# LiveKit
LIVEKIT_URL=ws://localhost:7880
LIVEKIT_API_KEY=
LIVEKIT_API_SECRET=
```

Các giá trị thật của password, JWT secret, MinIO credential và LiveKit secret phải được cấu hình riêng trên từng máy.

---

# 8. PostgreSQL

Tạo database PostgreSQL phù hợp với `DATABASE_URL` trong:

```text
backend/.env
```

Ví dụ:

```text
postgresql+asyncpg://USER:PASSWORD@127.0.0.1:5432/DATABASE
```

Sau đó chạy migration:

```powershell
cd backend

.\.venv-win\Scripts\python.exe -m alembic upgrade head
```

Kiểm tra migration:

```powershell
.\.venv-win\Scripts\python.exe -m alembic current
```

---

# 9. Khởi động MinIO

Đảm bảo Docker Desktop đang chạy.

Từ thư mục root của project:

```powershell
docker compose --env-file backend\.env up -d minio minio-init
```

Kiểm tra:

```powershell
docker compose --env-file backend\.env ps -a
```

MinIO server phải ở trạng thái healthy.

MinIO API:

```text
http://127.0.0.1:9000
```

MinIO Console:

```text
http://127.0.0.1:9001
```

Bucket mặc định:

```text
chat-attachments
```

---

# 10. Khởi động LiveKit

LiveKit được sử dụng cho:

- microphone
- camera
- WebRTC media
- screen sharing

Từ root project:

```powershell
docker compose --env-file backend\.env -f docker-compose.livekit.yml up -d
```

Kiểm tra:

```powershell
docker compose --env-file backend\.env -f docker-compose.livekit.yml ps
```

Kiểm tra signaling server:

```powershell
Test-NetConnection 127.0.0.1 -Port 7880
```

Kết quả cần có:

```text
TcpTestSucceeded : True
```

Các port local:

```text
7880 - LiveKit signaling
7881 - RTC TCP
7882 - RTC UDP
```

---

# 11. Chạy Backend

Mở một PowerShell tại:

```text
KLTN2026/backend
```

Chạy:

```powershell
.\.venv-win\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Backend:

```text
http://127.0.0.1:8000
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

Health check:

```text
http://127.0.0.1:8000/api/v1/health
```

---

# 12. Cài và chạy Frontend

Mở PowerShell mới:

```powershell
cd frontend
npm install
```

Cấu hình Backend URL:

```powershell
$env:NEXT_PUBLIC_API_BASE_URL = "http://localhost:8000"
```

Chạy development server:

```powershell
npm run dev
```

Frontend:

```text
http://localhost:3000
```

---

# 13. Thứ tự chạy project

Mỗi lần khởi động project nên chạy theo thứ tự:

```text
1. PostgreSQL
       ↓
2. Docker Desktop
       ↓
3. MinIO
       ↓
4. LiveKit
       ↓
5. FastAPI Backend
       ↓
6. Next.js Frontend
```

---

# 14. Sau khi restart máy

### Bước 1

Mở Docker Desktop và chờ Docker Engine chạy.

Kiểm tra:

```powershell
docker version
```

Phải thấy cả:

```text
Client
Server
```

### Bước 2

Khởi động MinIO:

```powershell
docker compose --env-file backend\.env up -d minio minio-init
```

### Bước 3

Khởi động LiveKit:

```powershell
docker compose --env-file backend\.env -f docker-compose.livekit.yml up -d
```

### Bước 4

Khởi động Backend:

```powershell
cd backend

.\.venv-win\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Bước 5

Khởi động Frontend ở terminal khác:

```powershell
cd frontend

$env:NEXT_PUBLIC_API_BASE_URL = "http://localhost:8000"

npm run dev
```

---

# 15. Build Frontend

```powershell
cd frontend

$env:NEXT_PUBLIC_API_BASE_URL = "http://localhost:8000"

npm run build
```

Nếu build thành công có thể chạy:

```powershell
npm start
```

---

# 16. Kiểm tra hệ thống

Sau khi chạy đầy đủ:

Frontend:

```text
http://localhost:3000
```

Backend:

```text
http://127.0.0.1:8000
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

MinIO:

```text
http://127.0.0.1:9001
```

LiveKit:

```text
ws://localhost:7880
```

---

# 17. Một số lỗi thường gặp

## Backend không kết nối PostgreSQL

Kiểm tra:

- PostgreSQL đang chạy
- username/password/database
- `DATABASE_URL`
- port PostgreSQL

Sau đó chạy lại:

```powershell
.\.venv-win\Scripts\python.exe -m alembic upgrade head
```

---

## Docker command bị treo

Mở Docker Desktop và đợi:

```text
Engine running
```

Sau đó:

```powershell
docker version
```

---

## LiveKit không hoạt động

Kiểm tra:

```powershell
docker compose --env-file backend\.env -f docker-compose.livekit.yml ps
```

và:

```powershell
Test-NetConnection 127.0.0.1 -Port 7880
```

---

## MinIO không hoạt động

Kiểm tra:

```powershell
docker compose --env-file backend\.env ps -a
```

Container MinIO cần ở trạng thái healthy.

---

## Frontend không gọi được Backend

Kiểm tra:

```powershell
$env:NEXT_PUBLIC_API_BASE_URL
```

Giá trị local:

```text
http://localhost:8000
```

Nếu thay đổi biến môi trường, restart Next.js development server.

---

# 18. Lưu ý khi phát triển

Không commit các file chứa secret:

```text
backend/.env
```

Không hard-code:

- Database password
- JWT secret
- MinIO access/secret key
- LiveKit API key/secret

Các giá trị mẫu dùng chung được khai báo trong:

```text
backend/.env.example
```

Nếu thay đổi database schema phải tạo và chạy Alembic migration.

Nếu thay đổi dependency Backend:

```text
backend/requirements.txt
```

Nếu thay đổi dependency Frontend:

```text
frontend/package.json
frontend/package-lock.json
```

---

# KLTN2026

**Xây dựng nền tảng học tập cộng tác trực tuyến kết hợp phòng tự học ảo và trợ lý AI giải đáp tài liệu.**
