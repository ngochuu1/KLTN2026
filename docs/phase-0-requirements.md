# ROLE

Bạn là Senior Full-stack Engineer đang làm việc dưới sự điều phối của Tech Lead.

Đây là một dự án Khóa luận tốt nghiệp mới hoàn toàn.
Hiện tại CHƯA có source code.

Không tự ý mở rộng phạm vi hoặc thêm nghiệp vụ ngoài yêu cầu.


# PROJECT

Tên đề tài:

“Xây dựng nền tảng học tập cộng tác trực tuyến kết hợp phòng tự học ảo
và trợ lý AI giải đáp tài liệu”.


# TECH STACK ĐÃ CHỐT

Frontend:
- Next.js
- React
- TypeScript
- App Router
- Tailwind CSS

Backend:
- Python
- FastAPI
- Pydantic

Database:
- PostgreSQL

Persistence:
- SQLAlchemy 2.x
- Alembic

API:
- REST API

Kiến trúc hiện tại:
- Modular Monolith

KHÔNG triển khai Microservices ở giai đoạn này.


# BUSINESS SCOPE

Hệ thống có 45 Use Case đã được phân tích và chốt.

Các nhóm chức năng gồm:

UC01–UC05:
Account

UC06–UC14:
Workspace

UC15–UC21:
Channel / Chat

UC22–UC28:
Study Room

UC29–UC32:
Documents

UC33–UC36:
AI / RAG

UC37–UC40:
Learning Tracking / Statistics

UC41–UC45:
Administration / Reports


QUAN TRỌNG:

Trong task hiện tại KHÔNG triển khai bất kỳ Use Case nào.

Task hiện tại chỉ xây dựng nền móng kỹ thuật.


# ARCHITECTURE

Project root:

kltn2026/

Frontend:

frontend/
  src/
    app/
    components/
    features/
    hooks/
    lib/
    services/
    types/

Backend:

backend/
  app/
    api/
      v1/
    core/
    db/
    models/
    schemas/
    repositories/
    services/
    main.py
  alembic/
  tests/


Backend phải tuân thủ dependency flow:

Router
→ Service
→ Repository
→ SQLAlchemy
→ PostgreSQL

Pydantic schema được sử dụng cho request/response contracts.

Không đặt business logic trực tiếp trong Router.

Frontend phải tuân thủ:

Page/Component
→ Feature/Hook
→ API Service
→ Backend API

Không gọi fetch trực tiếp rải rác trong presentation components.


# TASK — PHASE 0 PROJECT BOOTSTRAP

Khởi tạo project để đạt trạng thái tối thiểu:

Frontend chạy được.

Backend chạy được.

PostgreSQL chạy được.

Backend kết nối được PostgreSQL.

Alembic migration hoạt động.

Frontend gọi thử được Backend.

Chưa triển khai business feature.


# BACKEND

Tạo FastAPI application.

Cần có:

GET /api/v1/health

Response:

{
  "status": "ok"
}


Tạo cấu hình environment.

Ví dụ biến môi trường:

APP_NAME
APP_ENV
DATABASE_URL
FRONTEND_URL


Sử dụng pydantic-settings để quản lý config.

Không hard-code:

- database credentials
- host
- port
- secret


# DATABASE

Sử dụng PostgreSQL.

Sử dụng SQLAlchemy 2.x.

Chuẩn bị:

- Base model
- Async database session
- Engine
- Dependency get_db

Cấu hình Alembic để nhận metadata từ SQLAlchemy.

Tạo initial migration chỉ khi thực sự có model cần migration.

KHÔNG tạo bảng users hoặc bảng nghiệp vụ ở task này.

Database hiện tại phải là database sạch.


# FRONTEND

Khởi tạo Next.js với:

- TypeScript
- App Router
- src directory
- Tailwind CSS

Tạo trang Home tối thiểu.

Trang phải gọi:

GET /api/v1/health

và hiển thị:

Backend connected

khi Backend phản hồi thành công.

Nếu backend không khả dụng:

Hiển thị trạng thái lỗi rõ ràng.

Không mock response.


# CORS

FastAPI chỉ cho phép frontend origin lấy từ biến:

FRONTEND_URL

Không sử dụng:

allow_origins=["*"]

cho cấu hình mặc định.


# DOCKER

Tạo docker-compose.yml CHỈ cho PostgreSQL ở Phase 0.

Không Dockerize frontend/backend ở task này.

Không thêm Redis.

Không thêm MinIO.

Không thêm Vector Database.

Các hạ tầng trên chỉ được thêm khi nghiệp vụ thực sự cần.


# ENVIRONMENT FILES

Tạo:

backend/.env.example

frontend/.env.local.example

Không commit secret thật.


# GITIGNORE

Phải ignore tối thiểu:

.env
.env.local
__pycache__
.venv
node_modules
.next
IDE generated files


# README

Viết hướng dẫn chạy local theo đúng thứ tự:

1. Start PostgreSQL
2. Setup backend environment
3. Run Alembic
4. Start FastAPI
5. Setup frontend
6. Start Next.js

Các command phải copy-paste chạy được.


# CONSTRAINTS

Không được:

- triển khai Account
- tạo User model
- triển khai JWT
- triển khai Workspace
- triển khai Chat
- triển khai WebSocket
- triển khai AI
- triển khai RAG
- thêm Redis
- thêm MinIO
- thêm Celery
- thêm Kafka
- thêm package không cần cho Phase 0
- tạo mock data
- tạo TODO placeholder
- xây kiến trúc Microservice
- tự ý thay đổi folder structure


# QUALITY REQUIREMENTS

Backend:

- type hints đầy đủ
- async nhất quán
- không dùng global database session
- không duplicate config
- import rõ ràng

Frontend:

- TypeScript strict
- không dùng any
- không hard-code Backend URL
- backend URL đọc từ environment variable


# VERIFICATION

Sau khi hoàn thành phải tự chạy và kiểm tra:

PostgreSQL container running

FastAPI startup success

GET /api/v1/health → HTTP 200

Alembic command hoạt động

Next.js startup success

Frontend gọi được FastAPI health endpoint


# OUTPUT SAU KHI HOÀN THÀNH

Không giải thích dài dòng.

Trả về:

PROJECT TREE

FILES CREATED

DEPENDENCIES ADDED

ENV VARIABLES

RUN COMMANDS

VERIFICATION RESULT

ISSUES / WARNINGS

Không triển khai task tiếp theo.
Chờ Tech Lead review.