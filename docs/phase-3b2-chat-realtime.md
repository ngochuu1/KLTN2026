# PHASE 3B2 — TEXT CHAT + REALTIME + REACTION

## 1. MỤC TIÊU

Triển khai Backend cho:

- UC18 — Gửi tin nhắn trong kênh
- UC19 — Chỉnh sửa/Xóa tin nhắn
- UC21 — Thả cảm xúc

Bao gồm:

- lịch sử tin nhắn
- tạo/chỉnh sửa/xóa tin nhắn
- reaction
- WebSocket realtime broadcast

Không làm attachment/file upload.
UC20 thuộc Phase 3B3.


## 2. NGỮ CẢNH

Chỉ đọc khi cần:

1. `README.md`
2. `docs/progress/phase-3b1-verification.md`
3. File này
4. Channel/Chat models + repositories hiện tại
5. Auth/Workspace permission hiện tại khi tích hợp

Không đọc lại Phase cũ.
Không đọc toàn bộ `docs/use-cases.md`.


## 3. NGUYÊN TẮC CHAT

Chat chỉ áp dụng cho Channel:

`type = TEXT`

Actor phải:

- authenticated
- còn là member của Workspace
- Workspace còn active
- Channel còn tồn tại

PostgreSQL là source of truth.

REST chịu trách nhiệm ghi dữ liệu.
WebSocket chịu trách nhiệm broadcast realtime.

Không dùng WebSocket làm nơi duy nhất lưu message.


## 4. MESSAGE HISTORY

Endpoint:

`GET /api/v1/channels/{channel_id}/messages`

Hỗ trợ pagination, ưu tiên:

- `limit`
- `before_message_id`

Default limit hợp lý, có giới hạn tối đa.

Trả message theo thứ tự ổn định.

Message response tối thiểu:

- id
- content
- sender public info
- created_at
- edited_at
- reaction summary

Không trả message đã `deleted_at`.

Không trả dữ liệu User nhạy cảm.


## 5. UC18 — SEND MESSAGE

Endpoint:

`POST /api/v1/channels/{channel_id}/messages`

Request:

```json
{
  "content": "Nội dung tin nhắn"
}
```

Rules:

- content không được NULL
- trim để kiểm tra blank
- chỉ whitespace → reject
- không cho gửi vào STUDY_ROOM Channel trong stage này

Flow:

1. Authenticate.
2. Check Workspace membership.
3. Check TEXT Channel.
4. Validate content.
5. Persist message.
6. Commit.
7. Broadcast `message.created`.
8. Return message.

Database commit phải hoàn thành trước khi broadcast.


## 6. UC19 — EDIT MESSAGE

Endpoint:

`PATCH /api/v1/messages/{message_id}`

Request:

```json
{
  "content": "Nội dung đã sửa"
}
```

Chỉ sender của message được sửa.

Rules:

- message chưa deleted
- content mới không blank
- update `edited_at`
- không thay sender/channel

Sau commit:

broadcast `message.updated`.


## 7. UC19 — DELETE MESSAGE

Endpoint:

`DELETE /api/v1/messages/{message_id}`

Chỉ sender được xóa message của chính mình.

Thực hiện:

`deleted_at = current UTC time`

Không hard-delete.

Sau commit:

broadcast `message.deleted`.

Các client nhận event phải có đủ `message_id` để loại message khỏi UI.


## 8. UC21 — REACTION

Dùng hai endpoint rõ trạng thái, tránh toggle request không idempotent.

### Add

`PUT /api/v1/messages/{message_id}/reactions/{emoji}`

### Remove

`DELETE /api/v1/messages/{message_id}/reactions/{emoji}`

Rules:

- Actor phải còn quyền truy cập Channel
- message phải tồn tại và chưa deleted
- emoji không được rỗng
- không tự tạo whitelist emoji nếu nghiệp vụ chưa quy định
- cùng User + message + emoji không duplicate
- User được dùng nhiều emoji khác nhau

Add reaction đã tồn tại:

không tạo duplicate.

Remove reaction chưa tồn tại:

xử lý nhất quán theo convention API hiện tại.

Sau thay đổi:

broadcast `reaction.updated` với reaction summary mới.


## 9. WEBSOCKET

Endpoint:

`WS /api/v1/ws/channels/{channel_id}`

WebSocket chỉ subscribe realtime cho một Channel.

Không dùng query-string access token nếu có thể tránh.


### Authentication

Sau khi socket connect, client phải gửi frame đầu tiên:

```json
{
  "type": "auth",
  "access_token": "..."
}
```

Server:

1. Không gửi dữ liệu Channel trước khi auth thành công.
2. Validate Access Token.
3. Validate Workspace membership.
4. Validate Channel.
5. Sau đó mới register connection.

Nếu auth fail:

close socket bằng close code phù hợp.

Có timeout ngắn cho auth frame để connection vô danh không tồn tại vô hạn.


## 10. WEBSOCKET EVENTS

Event envelope thống nhất:

```json
{
  "type": "message.created",
  "data": {}
}
```

Tối thiểu:

- `message.created`
- `message.updated`
- `message.deleted`
- `reaction.updated`

Không tạo nhiều event naming cho cùng một hành vi.


## 11. CONNECTION MANAGER

Tạo connection manager theo Channel.

Phải hỗ trợ:

- connect
- disconnect
- broadcast channel
- cleanup dead connection

Phase 3B2 hiện tại cho phép in-process manager.

Không thêm Redis chỉ để pub/sub ở stage này.

Nếu hệ thống sau này chạy nhiều Backend worker/instance,
Redis pub/sub sẽ được đánh giá riêng.


## 12. REALTIME CONSISTENCY

WebSocket không phải durable message queue.

Nếu client mất WebSocket event:

sau reconnect phải có thể lấy dữ liệu mới nhất qua REST history.

Backend không giữ message chỉ trong memory.

Khi broadcast fail tới một socket:

- không rollback dữ liệu đã commit
- cleanup connection lỗi nếu cần


## 13. SECURITY

WebSocket phải kiểm tra Origin theo frontend origin/config hiện tại nếu architecture cho phép.

Không log:

- access token
- message credential data

Mọi REST mutation vẫn kiểm tra authorization độc lập.

Không tin permission chỉ vì socket trước đó đã authenticate.


## 14. ERROR CONTRACT

REST reuse Error Contract hiện tại.

Tối thiểu xử lý:

- CHANNEL_NOT_FOUND
- CHANNEL_ACCESS_DENIED
- INVALID_MESSAGE_CONTENT
- MESSAGE_NOT_FOUND
- MESSAGE_PERMISSION_DENIED
- MESSAGE_ALREADY_DELETED

Reuse naming hiện tại nếu tương đương.

Không tạo error envelope mới.


## 15. KHÔNG LÀM

Không triển khai:

- UC20 attachment
- MinIO/Object Storage
- file upload
- Frontend
- typing indicator
- read receipt
- mention
- thread/reply
- message search
- Redis
- Study Room

Không mở rộng Chat ngoài UC18/19/21.


## 16. VERIFICATION

Targeted verification tối thiểu:

1. Member lấy history → PASS.
2. Non-member history → DENY.
3. Send valid message → persist + broadcast.
4. Blank message → DENY.
5. Sender edit → PASS + `edited_at` + broadcast.
6. User khác edit → DENY.
7. Sender delete → PASS + broadcast.
8. Deleted message không còn trong history.
9. User khác delete → DENY.
10. Add reaction → PASS + broadcast.
11. Same reaction không duplicate.
12. Different emoji cùng User → PASS.
13. Remove reaction → PASS + broadcast.
14. Reaction trên deleted message → DENY.
15. WebSocket auth/member validation → PASS.
16. Disconnect cleanup → PASS.
17. Backend startup → PASS.

Không viết exhaustive suite — Phase 3C phụ trách.


## 17. DONE KHI

- UC18 hoạt động
- UC19 hoạt động
- UC21 hoạt động
- REST persistence đúng
- WebSocket broadcast đúng
- authorization đúng
- reconnect có REST source of truth
- targeted verification PASS
- startup PASS
- không có thay đổi ngoài scope


## 18. HANDOFF

Sau khi PASS:

Cập nhật README:

- Phase 3B1: DONE
- Phase 3B2: DONE
- Current: Phase 3B3 — Chat Attachment/Object Storage
- Latest handoff:
  `docs/progress/phase-3b2-verification.md`

Tạo:

`docs/progress/phase-3b2-verification.md`

Chỉ ghi:

- Status
- APIs / WebSocket implemented
- Event types
- Files changed
- Verification
- Bugs fixed
- Remaining issues
- Next stage


## 19. OUTPUT CHAT

Chỉ trả:

DONE hoặc FAILED
REST verification: PASS/FAIL
WebSocket verification: PASS/FAIL
Events: <count>
Files changed: ...
Handoff: docs/progress/phase-3b2-verification.md
Remaining issue: ...

Không giải thích.
Không paste code.
Không paste log.