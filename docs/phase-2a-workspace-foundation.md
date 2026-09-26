# PHASE 2A — WORKSPACE DOMAIN & DATABASE FOUNDATION

## 1. MỤC TIÊU

Chuẩn bị Domain + Database foundation cho UC06–UC14.

Chỉ triển khai:
- Workspace ORM model
- Workspace Member ORM model
- Workspace Invitation ORM model
- enums/domain rules cần thiết
- repositories nền tảng
- Alembic migration

Không tạo Workspace API.
Không làm Frontend.


## 2. NGỮ CẢNH

Chỉ đọc khi cần:

1. `README.md`
2. `docs/progress/phase-1e-verification.md`
3. File này
4. User/Auth model hiện tại để liên kết FK

Không đọc lại toàn bộ Phase 1.
Không đọc toàn bộ `docs/use-cases.md`.

Chỉ tra UC06–UC14 nếu phát hiện điểm nghiệp vụ chưa rõ.


## 3. WORKSPACE MODEL

Table:

`workspaces`

Fields tối thiểu:

- id: UUID, PK
- name: VARCHAR(120), NOT NULL
- description: TEXT, NULLABLE
- created_at: TIMESTAMPTZ, NOT NULL
- updated_at: TIMESTAMPTZ, NOT NULL
- deleted_at: TIMESTAMPTZ, NULLABLE

Quy ước:

`deleted_at IS NULL`
→ Workspace đang hoạt động.

`deleted_at IS NOT NULL`
→ Workspace đã bị xóa mềm.

Không hard-delete Workspace trong nghiệp vụ thông thường.


## 4. WORKSPACE MEMBER MODEL

Table:

`workspace_members`

Fields:

- id: UUID, PK
- workspace_id: FK → workspaces.id, NOT NULL
- user_id: FK → users.id, NOT NULL
- role: WorkspaceRole, NOT NULL
- joined_at: TIMESTAMPTZ, NOT NULL

WorkspaceRole:

- OWNER
- ADMIN
- MEMBER

Constraints:

- UNIQUE(workspace_id, user_id)

Không được có duplicate membership.

Thiết kế phải đảm bảo mỗi Workspace chỉ có một OWNER hợp lệ.

Nguồn quyền Workspace nằm ở `workspace_members`.

Không dùng `users.system_role` cho quyền trong Workspace.


## 5. DOMAIN RULES

Các rule phải được model/schema/repository hỗ trợ để Phase 2B thực thi:

- Người tạo Workspace → OWNER.
- Người tham gia thông thường → MEMBER.
- OWNER không được bị xóa khỏi Workspace.
- OWNER không được tự rời Workspace.
- Chỉ OWNER được thay đổi role thành viên.
- Role có thể thay đổi giữa MEMBER và ADMIN.
- Không tự thay đổi OWNER thông qua chức năng phân quyền UC12.
- MEMBER không có quyền quản lý Workspace.

Không cần implement service enforcement đầy đủ ở 2A.


## 6. WORKSPACE INVITATION MODEL

Table:

`workspace_invitations`

Phải hỗ trợ:

- lời mời trực tiếp tới User
- lời mời bằng link/code
- chấp nhận
- từ chối
- lời mời hết hạn

Fields tối thiểu:

- id: UUID, PK
- workspace_id: FK → workspaces.id, NOT NULL
- created_by_user_id: FK → users.id, NOT NULL
- invitee_user_id: FK → users.id, NULLABLE
- token_hash: VARCHAR(255), UNIQUE, NOT NULL
- status: InvitationStatus, NOT NULL
- expires_at: TIMESTAMPTZ, NULLABLE
- created_at: TIMESTAMPTZ, NOT NULL
- updated_at: TIMESTAMPTZ, NOT NULL

InvitationStatus:

- PENDING
- ACCEPTED
- DECLINED
- REVOKED

Không lưu plaintext invitation token/code trong database.

Thời hạn mặc định của invitation chưa được UC quy định.

Không tự chọn số ngày hết hạn ở Phase 2A.
Schema chỉ cần hỗ trợ `expires_at`.


## 7. REPOSITORIES

Tạo/reuse repository layer phù hợp cho:

### WorkspaceRepository

Tối thiểu hỗ trợ foundation cho:
- create
- get by id
- update
- soft delete
- lấy Workspace đang hoạt động

### WorkspaceMemberRepository

Tối thiểu:
- create membership
- get membership
- list members
- check membership
- update role
- remove membership

### WorkspaceInvitationRepository

Tối thiểu:
- create invitation
- get invitation
- lookup bằng token hash
- update invitation status

Không viết business flow của UC06–UC14 trong repository.


## 8. DATABASE CONSTRAINTS

Database phải bảo vệ tối thiểu:

- Workspace PK
- Membership FK
- Invitation FK
- UNIQUE(workspace_id, user_id)
- UNIQUE invitation token hash
- role/status hợp lệ

Không chỉ dựa vào application validation cho uniqueness.


## 9. DEFAULT CHANNEL — DEFERRED DEPENDENCY

UC06 có bước khởi tạo thông tin mặc định cho Workspace và các UC Channel sau này có kênh mặc định `#general`.

Phase 2A KHÔNG tạo Channel model hoặc `#general`.

Đây là dependency của Channel phase sau.

Không kéo Channel domain vào Phase 2A chỉ để xử lý trước.


## 10. MIGRATION

Tạo Alembic migration cho:

- workspaces
- workspace_members
- workspace_invitations
- enums/indexes/constraints liên quan

Migration phải:

- upgrade PASS
- downgrade hợp lệ
- không sửa migration Phase 1 cũ
- không drop/recreate database để né migration lỗi


## 11. KHÔNG LÀM

Không triển khai:

- Workspace API
- invitation API
- permission service hoàn chỉnh
- Frontend
- Channel
- #general
- Chat
- WebSocket
- Study Room
- Document
- AI/RAG
- Admin

Không refactor Account/Auth nếu không cần cho FK/import.


## 12. VERIFICATION

Chỉ kiểm tra phạm vi 2A:

- migration upgrade
- tables/constraints được tạo đúng
- Backend import/startup không lỗi
- ORM relationships hoạt động
- duplicate membership bị database từ chối
- invalid role/status không được persist

Không chạy lại toàn bộ Phase 1 test suite nếu source Phase 1 không bị sửa.


## 13. DONE KHI

- 3 tables được tạo đúng
- WorkspaceRole đúng
- InvitationStatus đúng
- membership uniqueness hoạt động
- single OWNER constraint/design được đảm bảo
- soft-delete foundation có sẵn
- invitation token không lưu plaintext
- migration PASS
- Backend startup PASS
- không có thay đổi ngoài phạm vi


## 14. HANDOFF

Sau khi PASS:

Cập nhật ngắn `README.md`:

- Phase 2A: DONE
- Next: Phase 2B — Workspace Backend APIs
- Latest handoff:
  `docs/progress/phase-2a-verification.md`

Tạo:

`docs/progress/phase-2a-verification.md`

Chỉ ghi:

- Status
- Database changes
- Files changed
- Migration result
- Verification
- Remaining issues
- Next stage

Không lưu full logs.


## 15. OUTPUT CHAT

Chỉ trả:

DONE hoặc FAILED
Migration: PASS/FAIL
Verification: PASS/FAIL
Files changed: ...
Handoff: ...
Remaining issue: ...

Không giải thích.
Không paste code.
Không paste full log.