# PHASE 3A — CHANNEL / CHAT DOMAIN & DATABASE FOUNDATION

## 1. MỤC TIÊU

Chuẩn bị Domain + Database foundation cho UC15–UC21:

- Channel
- Chat Message
- Attachment metadata
- Message Reaction

Chỉ làm model, enum, constraint, repository và migration.

Không làm API.
Không làm WebSocket.
Không làm Object Storage integration.
Không làm Frontend.


## 2. NGỮ CẢNH

Chỉ đọc khi cần:

1. `README.md`
2. `docs/progress/phase-2e-verification.md`
3. File này
4. Workspace/User models hiện tại

Không đọc lại Phase 1–2.
Không đọc toàn bộ `docs/use-cases.md`.

Chỉ tra UC15–UC21 nếu gặp điểm nghiệp vụ chưa rõ.


## 3. CHANNEL

Table:

`channels`

Fields tối thiểu:

- id: UUID PK
- workspace_id: FK → workspaces.id
- name: VARCHAR(100), NOT NULL
- description: TEXT, NULLABLE
- type: ChannelType, NOT NULL
- is_default: BOOLEAN, NOT NULL, default false
- created_at
- updated_at

ChannelType:

- TEXT
- STUDY_ROOM

Constraint:

- UNIQUE(workspace_id, name)

Mỗi Workspace chỉ được có một channel `is_default = true`.

Default channel:

- name: `general`
- type: TEXT
- is_default: true

Không triển khai chức năng Study Room ở Phase 3.


## 4. DEFAULT #GENERAL

Phase 2 đã cố ý defer default channel.

Phase 3A chỉ chuẩn bị schema/domain để hỗ trợ `#general`.

Không sửa Workspace API ở stage này.

Phase 3B phải xử lý:

- Workspace mới → tạo default `#general`
- default channel không được xóa

Nếu project hiện có Workspace được tạo từ Phase 2 chưa có `#general`,
ghi nhận trong handoff để Phase 3B xử lý bootstrap/backfill phù hợp.


## 5. CHAT MESSAGE

Table:

`chat_messages`

Fields tối thiểu:

- id: UUID PK
- channel_id: FK → channels.id
- sender_user_id: FK → users.id
- content: TEXT, NULLABLE
- edited_at: TIMESTAMPTZ, NULLABLE
- deleted_at: TIMESTAMPTZ, NULLABLE
- created_at: TIMESTAMPTZ, NOT NULL
- updated_at: TIMESTAMPTZ, NOT NULL

`content` được phép NULL ở database vì UC20 cho phép message chỉ có attachment.

Business rule Phase 3B phải đảm bảo:

Message phải có ít nhất:
- text hợp lệ
hoặc
- attachment

Tin nhắn bị xóa dùng `deleted_at`, không hard-delete ngay.


## 6. CHAT ATTACHMENT

Table:

`chat_attachments`

Fields tối thiểu:

- id: UUID PK
- message_id: FK → chat_messages.id
- storage_key: VARCHAR, NOT NULL
- original_filename: VARCHAR, NOT NULL
- content_type: VARCHAR, NOT NULL
- size_bytes: BIGINT, NOT NULL
- created_at: TIMESTAMPTZ, NOT NULL

Chỉ lưu metadata Object Storage.

Không lưu binary file trong PostgreSQL.

Không cấu hình MinIO/Object Storage trong Phase 3A.

Giới hạn 25MB của UC20 sẽ được enforce ở Phase 3B.


## 7. MESSAGE REACTION

Table:

`message_reactions`

Fields:

- id: UUID PK
- message_id: FK → chat_messages.id
- user_id: FK → users.id
- emoji: VARCHAR(32), NOT NULL
- created_at: TIMESTAMPTZ, NOT NULL

Constraint:

`UNIQUE(message_id, user_id, emoji)`

Một User:

- không được thả trùng cùng emoji trên cùng message
- được phép thả nhiều emoji khác nhau

Phù hợp toggle reaction của UC21.


## 8. DELETE / RELATIONSHIP RULES

Channel mặc định:

không được phép xóa ở business layer.

Channel thường:

UC17 yêu cầu xóa Channel khỏi hệ thống.

Database relationships phải hỗ trợ cleanup dữ liệu phụ thuộc hợp lý khi Channel bị xóa.

Message đã xóa riêng lẻ:

dùng `deleted_at`.

Attachment/Reaction thuộc Message:

không được tồn tại orphan.


## 9. ACCESS MODEL

Không tạo:

`channel_members`

UC hiện tại dùng membership của Workspace để xác định quyền truy cập Channel.

Quyền quản lý Channel Phase 3B sẽ dựa trên Workspace role:

- OWNER
- ADMIN
- MEMBER

Không duplicate role system mới cho Channel.


## 10. REPOSITORIES

Tạo/reuse:

### ChannelRepository

Foundation cho:

- create
- get by id
- list by workspace
- update
- delete
- get default channel
- duplicate-name check


### ChatMessageRepository

Foundation cho:

- create
- get by id
- list by channel
- update content
- mark deleted


### ChatAttachmentRepository

Foundation cho:

- create metadata
- list by message


### MessageReactionRepository

Foundation cho:

- create
- find exact reaction
- delete
- list/count by message

Không đưa business permission vào Repository.


## 11. INDEX / CONSTRAINT

Tối thiểu cần index phù hợp cho:

- channels.workspace_id
- chat_messages.channel_id + created_at
- chat_messages.sender_user_id
- chat_attachments.message_id
- message_reactions.message_id

Database bảo vệ:

- unique Channel name trong Workspace
- một default Channel / Workspace
- unique reaction `(message_id, user_id, emoji)`
- FK integrity


## 12. UC17 SOURCE NOTE

UC17 có lỗi copy/paste ở phần Description trong tài liệu nghiệp vụ.

Phase 3 sử dụng:

- tên UC17: Xóa kênh
- Pre/Post Conditions
- Main/Alternative/Exception Flow của UC17

Không triển khai chức năng tìm kiếm bài viết/tài khoản từ Description bị sai.


## 13. MIGRATION

Tạo Alembic migration cho:

- channels
- chat_messages
- chat_attachments
- message_reactions
- enums
- indexes
- constraints

Migration phải:

- upgrade PASS
- downgrade hợp lệ
- không sửa migration Phase 1–2
- không reset database để né lỗi


## 14. KHÔNG LÀM

Không triển khai:

- Channel API
- Chat API
- WebSocket
- file upload
- Object Storage
- realtime reaction
- Frontend
- Study Room
- Pomodoro
- Documents
- AI/RAG

Không refactor Workspace/Auth ngoài FK/import cần thiết.


## 15. VERIFICATION

Targeted verification:

- migration PASS
- Backend startup PASS
- duplicate channel name bị chặn
- chỉ một default channel / Workspace
- duplicate same reaction bị chặn
- multiple different reactions/User được phép
- message + attachment relationships hoạt động
- không có orphan FK

Không chạy lại Phase 1–2 suites.


## 16. DONE KHI

- 4 tables đúng schema
- ChannelType đúng
- default-channel foundation đúng
- message edit/delete foundation đúng
- attachment metadata foundation đúng
- reaction uniqueness đúng
- indexes/constraints đúng
- migration PASS
- startup PASS
- không thay đổi ngoài scope


## 17. HANDOFF

Sau khi PASS:

Cập nhật `README.md`:

- Phase 3A: DONE
- Next: Phase 3B — Channel/Chat Backend + Realtime
- Latest handoff:
  `docs/progress/phase-3a-verification.md`

Tạo:

`docs/progress/phase-3a-verification.md`

Chỉ ghi:

- Status
- Database changes
- Files changed
- Migration/verification
- Existing Workspace default-channel note
- Remaining issues
- Next stage

Không lưu full logs.


## 18. OUTPUT CHAT

Chỉ trả:

DONE hoặc FAILED
Migration: PASS/FAIL
Verification: PASS/FAIL
Files changed: ...
Handoff: docs/progress/phase-3a-verification.md
Remaining issue: ...

Không giải thích.
Không paste code.
Không paste full log.