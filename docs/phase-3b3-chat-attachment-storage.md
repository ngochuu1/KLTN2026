# PHASE 3B3 — CHAT ATTACHMENT + OBJECT STORAGE

## 1. MỤC TIÊU

Triển khai Backend UC20 — Gửi tệp trong kênh chat.

Bao gồm:

- Object Storage
- upload attachment
- message có file
- message có text + file
- download attachment có authorization
- realtime broadcast message chứa attachment

Không làm Frontend.
Không mở rộng Chat ngoài UC20.


## 2. NGỮ CẢNH

Chỉ đọc khi cần:

1. `README.md`
2. `docs/progress/phase-3b2-verification.md`
3. File này
4. Chat service/schema/model hiện tại
5. `docker-compose.yml` và backend config

Không đọc lại Phase cũ.
Không đọc toàn bộ `docs/use-cases.md`.


## 3. OBJECT STORAGE

Sử dụng S3-compatible Object Storage.

Local development sử dụng MinIO chạy standalone trên Windows.
Không yêu cầu Docker.

Business code phải đi qua StorageService abstraction,
không phụ thuộc trực tiếp vào cách MinIO được chạy.

Bucket phải PRIVATE.

PostgreSQL chỉ lưu attachment metadata.
Binary file được lưu trong Object Storage.


## 4. CONFIGURATION

Bổ sung:

- OBJECT_STORAGE_ENDPOINT
- OBJECT_STORAGE_ACCESS_KEY
- OBJECT_STORAGE_SECRET_KEY
- OBJECT_STORAGE_BUCKET
- OBJECT_STORAGE_SECURE
- ATTACHMENT_MAX_SIZE_BYTES

Default attachment max size:

25 MB

Cập nhật backend/.env.example.

Không commit credential thật.


## 5. LOCAL STORAGE ENVIRONMENT

Không sử dụng Docker trong Phase 3B3.

MinIO được chạy standalone trên Windows.

Code phải cho phép cấu hình endpoint bằng environment variable,
ví dụ local MinIO hoặc S3-compatible provider khác.

Không hard-code localhost/port/credential vào source.

Phase này không yêu cầu container hóa PostgreSQL, Backend hoặc Frontend.


## 6. STORAGE SERVICE

Tạo StorageService abstraction tối thiểu hỗ trợ:

- upload object
- delete object dùng cho compensation khi upload flow thất bại
- generate authorized temporary download URL hoặc cơ chế download tương đương
- kiểm tra bucket/config khi cần

Storage key phải được hệ thống sinh.

Không dùng original filename làm object key trực tiếp.


## 7. FILE POLICY

UC20 hỗ trợ tài liệu và ảnh.

Phase 3B3 hỗ trợ tối thiểu:

- PDF
- DOC
- DOCX
- TXT
- PNG
- JPG / JPEG

Không cho phép file executable/script.

Validation phải kiểm tra:

- filename
- extension/type policy
- size <= 25MB
- file không rỗng

Không chỉ tin `Content-Length`.

Server phải thực sự giới hạn số byte đọc/upload.


## 8. SEND ATTACHMENT MESSAGE

Endpoint:

`POST /api/v1/channels/{channel_id}/messages/attachments`

Content-Type:

`multipart/form-data`

Fields:

- `file`: required
- `content`: optional

Chỉ áp dụng cho TEXT Channel.

Actor phải còn là member của Workspace.


### Business rule

Message hợp lệ khi có:

- attachment

và có thể kèm:

- content text


Nếu có content:

content không được chỉ chứa whitespace.


## 9. UPLOAD FLOW

Flow:

1. Authenticate User.
2. Validate Workspace/Channel access.
3. Validate TEXT Channel.
4. Validate file type + size.
5. Generate unique storage key.
6. Upload file vào Object Storage.
7. Tạo `chat_messages`.
8. Tạo `chat_attachments`.
9. Commit database transaction.
10. Broadcast `message.created`.
11. Return message response đầy đủ.

Nếu bước 6 thất bại:

- không tạo message
- không tạo attachment metadata

Nếu Object Storage upload thành công nhưng DB transaction thất bại:

- rollback DB
- cố gắng xóa object vừa upload để tránh orphan

Không rollback DB chỉ vì WebSocket broadcast thất bại.


## 10. MESSAGE RESPONSE

Message response/history phải hỗ trợ:

`attachments`

Mỗi attachment public metadata tối thiểu:

- id
- original_filename
- content_type
- size_bytes

Không trả:

- storage_key
- internal bucket information

Message text bình thường:

`attachments = []`


## 11. DOWNLOAD ATTACHMENT

Endpoint:

`GET /api/v1/attachments/{attachment_id}/download`

Flow:

1. Authenticate.
2. Lookup attachment + message + channel.
3. Kiểm tra message chưa bị deleted.
4. Kiểm tra User còn là member Workspace.
5. Tạo temporary authorized download URL hoặc response download an toàn.

Object Storage không public.

Không expose permanent public URL.


## 12. REALTIME

Upload message thành công phải reuse event:

`message.created`

Không tạo event riêng như `attachment.created`.

Payload message phải chứa attachment public metadata để client realtime render ngay.

Không broadcast trước DB commit.


## 13. MESSAGE DELETE + ATTACHMENT

UC19 hiện dùng soft-delete message.

Khi message có attachment bị soft-delete:

- attachment không còn được download qua API
- message không còn xuất hiện trong history

Phase 3B3 KHÔNG bắt buộc xóa object vật lý ngay.

Object lifecycle/retention có thể xử lý ở phase vận hành sau.


## 14. ERROR CONTRACT

Reuse Error Contract hiện tại.

Tối thiểu xử lý:

- ATTACHMENT_TYPE_NOT_ALLOWED
- ATTACHMENT_TOO_LARGE
- ATTACHMENT_EMPTY
- ATTACHMENT_UPLOAD_FAILED
- ATTACHMENT_NOT_FOUND
- ATTACHMENT_ACCESS_DENIED

Reuse naming tương đương nếu project đã có convention.

Không tạo error envelope mới.


## 15. SECURITY

Không:

- trust filename làm storage path
- expose storage credentials
- expose storage_key
- dùng public bucket
- log file binary
- log credentials

Filename hiển thị phải được xử lý an toàn.

Không thực thi nội dung upload.


## 16. KHÔNG LÀM

Không triển khai:

- multiple attachments / message
- upload progress realtime
- virus scanning
- thumbnail generation
- image processing
- file preview
- Frontend
- Redis
- Documents/RAG storage
- Study Room

Một message Phase 3B3 chỉ cần hỗ trợ một attachment.


## 17. VERIFICATION

Targeted verification:

1. S3-compatible Object Storage / MinIO standalone health → PASS.
2. Upload file hợp lệ → object + DB metadata + message.
3. Text + file → PASS.
4. File-only message → PASS.
5. File >25MB → DENY.
6. Unsupported type → DENY.
7. Empty file → DENY.
8. Non-member upload → DENY.
9. STUDY_ROOM upload → DENY.
10. Upload failure → không tạo DB record.
11. DB failure sau upload → compensation cleanup object.
12. History trả attachment metadata.
13. `message.created` broadcast chứa attachment metadata.
14. Authorized download → PASS.
15. Non-member download → DENY.
16. Deleted-message attachment download → DENY.
17. Backend startup → PASS.

Không viết exhaustive suite.
Phase 3C phụ trách full tests.


## 18. DONE KHI

- UC20 Backend hoạt động
- MinIO/Object Storage hoạt động
- 25MB limit được enforce
- file type validation hoạt động
- DB/Object Storage consistency đúng
- attachment download có authorization
- history/realtime chứa attachment metadata
- targeted verification PASS
- startup PASS
- không có thay đổi ngoài scope


## 19. HANDOFF

Sau khi PASS:

Cập nhật README:

- Phase 3B1: DONE
- Phase 3B2: DONE
- Phase 3B3: DONE
- Phase 3B: COMPLETED
- Next: Phase 3C — Channel/Chat Backend Tests
- Latest handoff:
  `docs/progress/phase-3b3-verification.md`

Tạo:

`docs/progress/phase-3b3-verification.md`

Chỉ ghi:

- Status
- Storage setup
- API implemented
- Files changed
- Verification
- Bugs fixed
- Remaining issues
- Next stage


## 20. OUTPUT CHAT

Chỉ trả:

DONE hoặc FAILED
Storage: PASS/FAIL
Verification: PASS/FAIL
Files changed: ...
Handoff: docs/progress/phase-3b3-verification.md
Remaining issue: ...

Không giải thích.
Không paste code.
Không paste log.