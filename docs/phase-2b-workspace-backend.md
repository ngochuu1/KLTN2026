# PHASE 2B — WORKSPACE BACKEND APIs

## 1. MỤC TIÊU

Triển khai Backend API và business logic cho UC06–UC14 dựa trên foundation đã hoàn thành ở Phase 2A.

Bao gồm:

- UC06 — Tạo Workspace
- UC07 — Xem danh sách Workspace
- UC08 — Mời thành viên vào Workspace
- UC09 — Tham gia Workspace
- UC10 — Cập nhật thông tin Workspace
- UC11 — Quản lý thành viên Workspace
- UC12 — Phân quyền thành viên Workspace
- UC13 — Rời Workspace
- UC14 — Xóa Workspace

Không làm Frontend.

Không viết full test suite trong stage này.
Phase 2C sẽ phụ trách automated tests đầy đủ.


## 2. NGỮ CẢNH

Chỉ đọc khi cần:

1. `README.md`
2. `docs/progress/phase-2a-verification.md`
3. File này
4. Workspace models/repositories từ Phase 2A
5. Auth dependency hiện tại

Không đọc lại Phase 1.

Không đọc toàn bộ `docs/use-cases.md`.

Chỉ tra đúng UC06–UC14 nếu phát hiện điểm nghiệp vụ chưa rõ.


## 3. WORKSPACE APIs

Base path:

`/api/v1/workspaces`


### UC06 — CREATE WORKSPACE

Endpoint:

`POST /api/v1/workspaces`

Request:

```json
{
  "name": "Nhóm học KLTN",
  "description": "..."
}
```

Flow phải atomic:

1. Xác thực current User.
2. Validate dữ liệu.
3. Tạo Workspace.
4. Tạo membership cho current User với role `OWNER`.
5. Commit transaction.
6. Trả Workspace vừa tạo.

Không cho Client tự gửi:

- owner_id
- user_id
- role
- deleted_at

Nếu tạo OWNER membership thất bại:

rollback toàn bộ thao tác tạo Workspace.

Không tạo Channel hoặc `#general` trong Phase 2B.


### UC07 — LIST WORKSPACES

Endpoint:

`GET /api/v1/workspaces`

Chỉ trả các Workspace mà current User đang là thành viên.

Không trả:

- Workspace của User khác
- Workspace đã soft-delete


### WORKSPACE DETAIL

Endpoint:

`GET /api/v1/workspaces/{workspace_id}`

Current User phải là thành viên của Workspace.

Response cần đủ thông tin Workspace và role hiện tại của User trong Workspace.

User không thuộc Workspace:

từ chối truy cập.


### UC10 — UPDATE WORKSPACE

Endpoint:

`PATCH /api/v1/workspaces/{workspace_id}`

Được phép:

- OWNER
- ADMIN

MEMBER:

không được phép.

Phase 2B chỉ cập nhật:

- name
- description

Không triển khai upload avatar.

Workspace đã soft-delete không được update.


### UC14 — DELETE WORKSPACE

Endpoint:

`DELETE /api/v1/workspaces/{workspace_id}`

Chỉ OWNER được thực hiện.

Thực hiện soft delete:

`deleted_at = current UTC time`

Không hard-delete Workspace.

Sau khi xóa:

- Workspace không xuất hiện trong danh sách
- thành viên không còn truy cập Workspace qua API nghiệp vụ
- các thao tác quản lý Workspace phải bị từ chối

Không hard-delete memberships hoặc invitations trong Phase 2B.


## 4. INVITATION APIs

### UC08 — CREATE INVITATION

Endpoint:

`POST /api/v1/workspaces/{workspace_id}/invitations`

Được phép:

- OWNER
- ADMIN

Phải hỗ trợ hai loại lời mời.


### Direct Invitation

Request:

```json
{
  "invitee_user_id": "uuid"
}
```

Kiểm tra:

- User được mời tồn tại
- Workspace active
- User chưa là thành viên Workspace


### Link / Code Invitation

Request có thể không chứa `invitee_user_id`.

Ví dụ:

```json
{}
```

Khi đó tạo generic invitation dùng token/link.


### Invitation Token

Sinh token ngẫu nhiên an toàn.

Plaintext token được trả cho Client để tạo link/code mời.

Database chỉ lưu:

`token_hash`

Không lưu plaintext invitation token.


### Expiration

Nếu invitation có `expires_at`:

phải kiểm tra hết hạn khi sử dụng.

Nếu:

`expires_at = NULL`

thì không tự coi lời mời là hết hạn.

Không tự đặt policy 7 ngày, 14 ngày hoặc 30 ngày vì UC chưa quy định.


## 5. UC09 — INVITATION PREVIEW

Endpoint:

`GET /api/v1/workspace-invitations/{token}`

Current User phải authenticated.

Flow:

1. Hash token.
2. Tìm invitation.
3. Kiểm tra invitation đang `PENDING`.
4. Kiểm tra expiration nếu có.
5. Kiểm tra Workspace active.
6. Nếu direct invitation:
   invitation phải dành cho current User.
7. Kiểm tra current User chưa là thành viên.
8. Trả thông tin cơ bản Workspace.

Không trả:

- token_hash
- dữ liệu nhạy cảm


## 6. UC09 — ACCEPT INVITATION

Endpoint:

`POST /api/v1/workspace-invitations/{token}/accept`

Flow phải atomic:

1. Authenticate current User.
2. Lookup invitation bằng token hash.
3. Validate:
   - invitation tồn tại
   - status = PENDING
   - chưa hết hạn
   - Workspace active
   - đúng invitee nếu là direct invitation
   - current User chưa là member
4. Tạo Workspace membership:
   `role = MEMBER`
5. Update invitation:
   `status = ACCEPTED`
6. Commit transaction.

Không được tạo duplicate membership.


## 7. UC09 — DECLINE INVITATION

Endpoint:

`POST /api/v1/workspace-invitations/{token}/decline`

Invitation phải hợp lệ và đang:

`PENDING`

Sau thao tác:

`PENDING → DECLINED`

Không tạo membership.


## 8. MEMBER APIs

### UC11 — LIST MEMBERS

Endpoint:

`GET /api/v1/workspaces/{workspace_id}/members`

Current User phải thuộc Workspace.

Trả tối thiểu:

- user_id
- full_name
- email
- role
- joined_at

Không trả thông tin Account nhạy cảm.


### UC11 — REMOVE MEMBER

Endpoint:

`DELETE /api/v1/workspaces/{workspace_id}/members/{user_id}`

Được phép:

- OWNER
- ADMIN

Rules:

- target phải đang thuộc Workspace
- không được remove OWNER
- không được tạo trạng thái membership không nhất quán

Nếu target không còn trong Workspace:

trả business error phù hợp.


## 9. UC12 — CHANGE MEMBER ROLE

Endpoint:

`PATCH /api/v1/workspaces/{workspace_id}/members/{user_id}/role`

Chỉ OWNER được thực hiện.

Request:

```json
{
  "role": "ADMIN"
}
```

Role được phép gán:

- ADMIN
- MEMBER

Không được gán:

- OWNER

Rules:

- target phải thuộc Workspace
- target không phải OWNER
- OWNER không tự thay đổi role của mình thông qua UC12
- ADMIN không được thay đổi role thành viên

Role mới có hiệu lực ngay sau khi update.


## 10. UC13 — LEAVE WORKSPACE

Endpoint:

`POST /api/v1/workspaces/{workspace_id}/leave`

Current User phải đang là thành viên.

Nếu role:

`OWNER`

→ từ chối.

Nếu:

- ADMIN
- MEMBER

→ remove membership của current User.

Sau khi rời:

User không còn quyền truy cập Workspace.


## 11. PERMISSION RULES

Permission logic phải tập trung tại Service/helper thích hợp.

Không duplicate kiểm tra role rải rác trong Router.

Quyền Phase 2B:

| Action | OWNER | ADMIN | MEMBER |
|---|---|---|---|
| View Workspace | YES | YES | YES |
| Update Workspace | YES | YES | NO |
| Create Invitation | YES | YES | NO |
| List Members | YES | YES | YES |
| Remove Member | YES | YES | NO |
| Change Member Role | YES | NO | NO |
| Leave Workspace | NO | YES | YES |
| Delete Workspace | YES | NO | NO |

OWNER không được bị remove.


## 12. TRANSACTION RULES

Các flow nhiều bước phải đảm bảo atomic transaction.


### Create Workspace

Workspace
+
OWNER Membership


### Accept Invitation

Validate Invitation
+
Create MEMBER Membership
+
Update Invitation Status


Nếu một bước thất bại:

rollback toàn bộ transaction.

Database constraints của Phase 2A vẫn là lớp bảo vệ cuối cùng đối với duplicate/concurrent request.


## 13. SOFT DELETE RULES

Mọi query Workspace phục vụ nghiệp vụ phải mặc định loại Workspace có:

`deleted_at IS NOT NULL`

Workspace đã deleted không được:

- xem
- update
- mời thành viên
- tham gia
- quản lý thành viên
- đổi role
- thao tác nghiệp vụ thông thường

Không hard-delete dữ liệu liên quan trong Phase 2B.


## 14. ERROR CONTRACT

Reuse Error Contract đã có từ Phase 1.

Không tạo response error format mới.

Các business error nên có code rõ nghĩa, ví dụ:

- `WORKSPACE_NOT_FOUND`
- `WORKSPACE_ACCESS_DENIED`
- `WORKSPACE_PERMISSION_DENIED`
- `WORKSPACE_ALREADY_MEMBER`
- `WORKSPACE_MEMBER_NOT_FOUND`
- `WORKSPACE_OWNER_CANNOT_BE_REMOVED`
- `WORKSPACE_OWNER_CANNOT_LEAVE`
- `INVALID_WORKSPACE_ROLE`
- `INVITATION_INVALID`
- `INVITATION_EXPIRED`
- `INVITATION_ALREADY_USED`
- `INVITATION_NOT_FOR_USER`

Nếu project hiện tại đã có convention tương đương thì reuse convention đó.

Không đổi naming chỉ vì ví dụ trong file này khác.

Không trả HTTP 200 cho business error.


## 15. SERVICE / REPOSITORY RULE

Router:

- nhận request
- resolve authentication
- gọi Service
- trả response

Service:

- business rules
- permissions
- transaction coordination

Repository:

- database access

Không đưa business rule vào Repository.

Không query SQLAlchemy trực tiếp rải rác trong Router.


## 16. KHÔNG LÀM

Không triển khai:

- Frontend
- Channel
- default `#general`
- Chat
- WebSocket
- Study Room
- Documents
- AI/RAG
- Workspace avatar upload
- chuyển quyền OWNER
- Admin quản lý Workspace toàn hệ thống
- chức năng ngoài UC06–UC14

Không refactor Account/Auth nếu không cần thiết.


## 17. VERIFICATION

Phase 2B chỉ thực hiện targeted verification.

Kiểm tra tối thiểu:

1. Create Workspace → creator trở thành OWNER.
2. List Workspace chỉ trả Workspace của current User.
3. MEMBER không update Workspace.
4. MEMBER không tạo invitation.
5. OWNER/ADMIN tạo invitation được.
6. Accept invitation → User trở thành MEMBER.
7. Duplicate membership bị từ chối.
8. OWNER đổi MEMBER ↔ ADMIN được.
9. ADMIN không đổi role.
10. OWNER không bị remove.
11. OWNER không leave Workspace.
12. ADMIN/MEMBER leave được.
13. Chỉ OWNER soft-delete Workspace.
14. Workspace đã deleted không truy cập lại được.
15. Backend startup PASS.

Không viết exhaustive automated test suite trong Phase 2B.

Phase 2C sẽ phụ trách tests đầy đủ.

Không chạy lại Phase 1 tests nếu không sửa source Phase 1.


## 18. DONE KHI

Phase 2B DONE khi:

- UC06–UC14 Backend APIs đã triển khai
- permission rules đúng
- invitation flow hoạt động
- membership flow hoạt động
- role management hoạt động
- leave Workspace hoạt động
- soft delete hoạt động
- multi-step operations atomic
- Error Contract nhất quán
- targeted verification PASS
- Backend startup PASS
- không có thay đổi ngoài phạm vi


## 19. HANDOFF

Sau khi PASS:

Cập nhật ngắn `README.md`:

- Phase 2A: DONE
- Phase 2B: DONE
- Next: Phase 2C — Workspace Backend Tests
- Latest handoff:
  `docs/progress/phase-2b-verification.md`

Tạo:

`docs/progress/phase-2b-verification.md`

Chỉ ghi:

- Status
- APIs implemented
- Files changed
- Verification
- Bugs fixed
- Remaining issues
- Next stage

Không lưu full terminal logs.


## 20. OUTPUT CHAT

Chỉ trả:

DONE hoặc FAILED

Verification: PASS/FAIL
APIs: <số endpoint>
Files changed: ...
Handoff: docs/progress/phase-2b-verification.md
Remaining issue: ...

Không giải thích.
Không paste code.
Không paste full log.