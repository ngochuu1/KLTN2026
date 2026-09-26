# PHASE 2D — WORKSPACE FRONTEND

## 1. MỤC TIÊU

Triển khai Frontend cho UC06–UC14 dựa trên Workspace Backend đã hoàn thành và test PASS ở Phase 2A–2C.

Phạm vi:

- Tạo Workspace
- Danh sách Workspace
- Xem Workspace
- Mời thành viên
- Tham gia / từ chối lời mời
- Cập nhật Workspace
- Quản lý thành viên
- Phân quyền
- Rời Workspace
- Xóa Workspace

Không thay đổi Backend contract.
Không làm Channel.


## 2. NGỮ CẢNH

Chỉ đọc khi cần:

1. `README.md`
2. `docs/progress/phase-2c-verification.md`
3. File này
4. Source frontend hiện tại
5. Workspace Backend routes/schemas khi cần xác nhận contract

Không đọc lại Phase 2A–2C requirements.
Không đọc toàn bộ `docs/use-cases.md`.


## 3. WORKSPACE LIST

Route:

`/workspaces`

Hiển thị các Workspace current User đang tham gia.

Có:

- loading
- empty state
- error state
- nút tạo Workspace
- chọn Workspace để mở

Nếu chưa có Workspace:

hiển thị chức năng tạo/tham gia Workspace phù hợp.


## 4. UC06 — CREATE WORKSPACE

Tạo form/modal phù hợp.

Fields:

- name
- description

Có:

- validation
- loading
- business error
- chống submit lặp
- cancel

Thành công:

điều hướng vào Workspace vừa tạo.

Không cho Client chọn role/OWNER.


## 5. WORKSPACE DETAIL

Route gợi ý:

`/workspaces/[workspaceId]`

Phase 2D chỉ cần hiển thị:

- name
- description
- current User role
- các thao tác Workspace tương ứng quyền

Không làm danh sách Channel ở stage này.


## 6. UC08–UC09 — INVITATION

### Create Invitation

OWNER / ADMIN có giao diện mời thành viên.

Hỗ trợ:

- direct invitation nếu Backend hiện tại hỗ trợ chọn User theo contract
- generic invitation link/code

Hiển thị invitation token/link trả về để Actor sao chép.

Không hiển thị token hash.


### Invitation Page

Route gợi ý:

`/invitations/[token]`

Hiển thị thông tin Workspace từ invitation preview.

Có:

- Tham gia
- Từ chối

Accept thành công:

điều hướng vào Workspace.

Decline thành công:

hiển thị trạng thái phù hợp và không thêm membership.

Xử lý rõ:

- invitation invalid
- expired
- already used
- invitation không dành cho current User
- User đã là member


## 7. UC10 — UPDATE WORKSPACE

OWNER / ADMIN:

cho phép sửa:

- name
- description

MEMBER:

không hiển thị hoặc disable chức năng chỉnh sửa.

Có:

- save
- cancel
- validation
- loading/error/success

Cancel không gọi update API.


## 8. UC11 — MANAGE MEMBERS

Route hoặc khu vực:

`/workspaces/[workspaceId]/members`

Hiển thị:

- full_name
- email
- role
- joined_at

OWNER / ADMIN:

có thể remove thành viên theo quyền Backend.

Không cho remove OWNER.

Sau remove thành công:

cập nhật danh sách ngay.


## 9. UC12 — CHANGE ROLE

Chỉ OWNER thấy chức năng đổi role.

Role được chọn:

- ADMIN
- MEMBER

Không cho chọn OWNER.

ADMIN / MEMBER không thấy hoặc không sử dụng chức năng này.

Sau update:

role mới phải cập nhật ngay trên UI.


## 10. UC13 — LEAVE WORKSPACE

ADMIN / MEMBER:

có chức năng `Rời Workspace`.

Trước khi thực hiện:

hiển thị confirmation.

Sau thành công:

- remove Workspace khỏi state/list
- điều hướng `/workspaces`

OWNER:

không cho thực hiện Leave.
Hiển thị thông tin phù hợp nếu cần.


## 11. UC14 — DELETE WORKSPACE

Chỉ OWNER thấy chức năng Delete.

Phải có confirmation rõ ràng trước khi gọi API.

Có thể yêu cầu xác nhận lại tên Workspace trên UI nếu phù hợp với thiết kế.

Sau thành công:

- Workspace không còn trong danh sách
- clear Workspace state liên quan
- điều hướng `/workspaces`

Không thực hiện hard-delete phía Frontend.


## 12. PERMISSION UI

Frontend phải phản ánh current User Workspace role.

| Action | OWNER | ADMIN | MEMBER |
|---|---|---|---|
| Update Workspace | YES | YES | NO |
| Invite Member | YES | YES | NO |
| Remove Member | YES | YES | NO |
| Change Role | YES | NO | NO |
| Leave Workspace | NO | YES | YES |
| Delete Workspace | YES | NO | NO |

Frontend permission chỉ phục vụ UX.

Backend vẫn là nguồn authorization cuối cùng.


## 13. CODE RULES

Reuse:

- Auth state Phase 1
- API client hiện tại
- Error handling hiện tại
- Tailwind/components hiện có

Tạo Workspace services/types/features theo convention frontend hiện tại.

Không:

- fetch trực tiếp rải rác trong page/component
- dùng `any`
- hard-code Backend URL
- mock API
- thêm UI library mới nếu không cần


## 14. BACKEND RULE

Backend Phase 2C đã nghiệm thu.

Không tự sửa Backend.

Nếu phát hiện Backend integration lỗi:

DỪNG và báo:

- endpoint
- lỗi
- nguyên nhân nghi ngờ
- thay đổi tối thiểu đề xuất

Không sửa contract/nghiệp vụ.


## 15. KHÔNG LÀM

Không triển khai:

- Channel
- `#general`
- Chat
- WebSocket
- Study Room
- Documents
- AI/RAG
- Workspace avatar upload
- chuyển quyền OWNER
- Admin toàn hệ thống


## 16. VERIFICATION

Kiểm tra với Backend thật:

- Create Workspace
- List/View Workspace
- Update Workspace
- Create invitation
- Accept/Decline invitation
- Member list
- Remove member
- Change role
- Leave Workspace
- Delete Workspace
- Permission UI OWNER/ADMIN/MEMBER

Sau khi hoàn thành chạy một lần:

`npm run lint`

`npm run build`

Nếu không sửa Backend:

không chạy lại Phase 2C Backend suite.


## 17. DONE KHI

- UC06–UC14 Frontend hoạt động với Backend thật
- Permission UI đúng
- invitation flow hoạt động
- member/role flow hoạt động
- leave/delete flow hoạt động
- loading/error/empty states rõ ràng
- không dùng `any`
- lint PASS
- build PASS
- không có blocker Phase 2D


## 18. HANDOFF

Sau khi PASS:

Cập nhật ngắn `README.md`:

- Phase 2D: DONE
- Next: Phase 2E — Integration & Regression
- Latest handoff:
  `docs/progress/phase-2d-verification.md`

Tạo:

`docs/progress/phase-2d-verification.md`

Chỉ ghi:

- Status
- Implemented
- Files changed
- Lint/Build
- Integration checks
- Remaining issues
- Next stage

Không lưu full log.


## 19. OUTPUT CHAT

Chỉ trả:

DONE hoặc FAILED
Lint: PASS/FAIL
Build: PASS/FAIL
Integration: PASS/FAIL
Files changed: ...
Handoff: docs/progress/phase-2d-verification.md
Remaining issue: ...

Không giải thích.
Không paste code.
Không paste full log.