# PHASE 3B1 — CHANNEL BACKEND + DEFAULT CHANNEL

## 1. MỤC TIÊU

Triển khai Backend Channel cho UC15–UC17 và hoàn tất dependency `#general` đã defer từ Phase 2.

Chỉ làm:

- default `#general`
- Channel REST APIs
- Channel permissions
- create / list / detail / update / delete Channel

Không làm Chat.
Không làm WebSocket.
Không làm file upload.
Không làm Frontend.


## 2. NGỮ CẢNH

Chỉ đọc khi cần:

1. `README.md`
2. `docs/progress/phase-3a-verification.md`
3. File này
4. Channel model/repository
5. Workspace service/permission hiện tại khi cần tích hợp

Không đọc lại Phase 1–2.
Không đọc toàn bộ UC.

Chỉ tra UC15–UC17 nếu gặp điểm nghiệp vụ chưa rõ.


## 3. DEFAULT #GENERAL

Phase 3A đã xác nhận Workspace cũ chưa có default Channel.

Phase 3B1 phải xử lý cả hai trường hợp.


### Workspace mới

Khi tạo Workspace thành công:

đồng thời tạo:

- name: `general`
- type: `TEXT`
- is_default: true

Flow:

Workspace
+
OWNER membership
+
default Channel

phải atomic.

Nếu tạo default Channel thất bại:

rollback toàn bộ Create Workspace.


### Workspace đã tồn tại

Tạo migration/data migration an toàn để backfill Workspace chưa có default Channel.

Rule:

- nếu Workspace chưa có default và chưa có channel tên `general`:
  tạo `general`.
- nếu đã có `general` nhưng chưa có default:
  sử dụng channel đó làm default nếu hợp lệ.
- không tạo duplicate.
- không tạo thêm default nếu Workspace đã có default.

Migration phải idempotent về mặt dữ liệu mong đợi.

Không sửa migration Phase 3A cũ.


## 4. UC15 — CREATE CHANNEL

Endpoint:

`POST /api/v1/workspaces/{workspace_id}/channels`

Actor:

- OWNER
- ADMIN

MEMBER bị từ chối.

Request:

```json
{
  "name": "backend",
  "description": "Trao đổi backend",
  "type": "TEXT"
}
```

`type` cho phép:

- TEXT
- STUDY_ROOM

Phase này chỉ tạo metadata cho STUDY_ROOM.
Không triển khai chức năng phòng tự học.

Validate:

- Workspace active
- Actor thuộc Workspace
- Actor có quyền
- name không rỗng
- name không trùng Channel trong Workspace

Không cho Client gửi:

- workspace_id
- is_default


## 5. LIST CHANNELS

Endpoint:

`GET /api/v1/workspaces/{workspace_id}/channels`

OWNER / ADMIN / MEMBER đều xem được.

Chỉ trả Channel thuộc Workspace Actor có quyền truy cập.

Default `general` phải xuất hiện trong danh sách.


## 6. CHANNEL DETAIL

Endpoint:

`GET /api/v1/channels/{channel_id}`

Actor phải là member của Workspace chứa Channel.

Không phải member:

từ chối truy cập.


## 7. UC16 — UPDATE CHANNEL

Endpoint:

`PATCH /api/v1/channels/{channel_id}`

Actor:

- OWNER
- ADMIN

Phase 3B1 chỉ cho update:

- name
- description

Không đổi:

- workspace_id
- type
- is_default

Validate duplicate name theo rule hiện tại của hệ thống.

MEMBER bị từ chối.


## 8. UC17 — DELETE CHANNEL

Endpoint:

`DELETE /api/v1/channels/{channel_id}`

Actor:

- OWNER
- ADMIN

Default Channel:

`is_default = true`

→ tuyệt đối không được xóa.

Channel thường:

được xóa theo UC17.

Dữ liệu phụ thuộc được cleanup theo FK/cascade đã thiết kế ở Phase 3A.

MEMBER bị từ chối.

Không áp dụng soft-delete Workspace rule cho Channel.


## 9. PERMISSION

| Action | OWNER | ADMIN | MEMBER |
|---|---|---|---|
| List/View Channel | YES | YES | YES |
| Create Channel | YES | YES | NO |
| Update Channel | YES | YES | NO |
| Delete Channel thường | YES | YES | NO |
| Delete #general | NO | NO | NO |

Backend là nguồn authorization cuối cùng.


## 10. ERROR CONTRACT

Reuse Error Contract hiện tại.

Tối thiểu phân biệt được:

- CHANNEL_NOT_FOUND
- CHANNEL_PERMISSION_DENIED
- CHANNEL_NAME_ALREADY_EXISTS
- DEFAULT_CHANNEL_CANNOT_BE_DELETED
- INVALID_CHANNEL_TYPE

Reuse convention hiện có nếu naming tương đương.

Không tạo error envelope mới.


## 11. UC17 SOURCE NOTE

Description của UC17 trong tài liệu bị copy nhầm nội dung tìm kiếm.

Không sử dụng Description sai đó.

Bám theo:

- tên UC17: Xóa kênh
- Pre/Post Conditions
- Main Flow
- Alternative Flow
- Exception Flow


## 12. KHÔNG LÀM

Không làm:

- Chat Message API
- Edit/Delete Message
- Reaction
- WebSocket
- Object Storage
- Attachment
- Frontend
- Study Room implementation
- Pomodoro

Không refactor Workspace ngoài phần cần thiết để tạo default Channel.


## 13. VERIFICATION

Targeted verification:

1. Workspace mới → có đúng một default `general`.
2. Workspace cũ → backfill đúng một default.
3. Create Channel OWNER → PASS.
4. Create Channel ADMIN → PASS.
5. MEMBER create → DENY.
6. Duplicate name → DENY.
7. List/View member → PASS.
8. OWNER/ADMIN update → PASS.
9. MEMBER update → DENY.
10. Delete Channel thường OWNER/ADMIN → PASS.
11. Delete `general` → DENY.
12. MEMBER delete → DENY.
13. Backend startup → PASS.

Không chạy full Phase 1–2 suites.

Không viết full Phase 3 test suite; Phase 3C phụ trách.


## 14. DONE KHI

- default `general` hoạt động cho Workspace mới
- Workspace cũ được backfill
- UC15–UC17 Backend hoạt động
- permission đúng
- default Channel không xóa được
- migration PASS
- targeted verification PASS
- startup PASS
- không có thay đổi ngoài scope


## 15. HANDOFF

Sau khi PASS:

Cập nhật README:

- Phase 3A: DONE
- Phase 3B1: DONE
- Current: Phase 3B2 — Chat + Realtime
- Latest handoff:
  `docs/progress/phase-3b1-verification.md`

Tạo:

`docs/progress/phase-3b1-verification.md`

Chỉ ghi:

- Status
- APIs implemented
- Default-channel/backfill result
- Files changed
- Verification
- Bugs fixed
- Remaining issues
- Next stage


## 16. OUTPUT CHAT

Chỉ trả:

DONE hoặc FAILED
Migration: PASS/FAIL
Verification: PASS/FAIL
APIs: <count>
Files changed: ...
Handoff: docs/progress/phase-3b1-verification.md
Remaining issue: ...

Không giải thích.
Không paste code.
Không paste log.