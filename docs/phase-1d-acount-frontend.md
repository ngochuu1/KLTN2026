# PHASE 1D — ACCOUNT / AUTH FRONTEND

## 1. MỤC TIÊU

Triển khai Frontend cho Account/Auth dựa trên Backend đã hoàn thành và kiểm thử ở Phase 1A–1C.

Phạm vi nghiệp vụ:

- UC01 — Đăng ký tài khoản
- UC02 — Đăng nhập
- UC03 — Đăng xuất
- UC04 — Xem và cập nhật thông tin cá nhân
- UC05 — Đổi mật khẩu

Backend contract hiện tại là nguồn tích hợp.

Không thay đổi Backend nếu không thực sự cần thiết.


---

# 2. NGỮ CẢNH CẦN ĐỌC

Chỉ cần đọc:

1. `README.md`
2. `docs/progress/phase-1c-verification.md`
3. File hiện tại:
   `docs/phase-1d-account-frontend.md`
4. Source Frontend hiện có.
5. Backend API schemas/routes Account/Auth khi cần xác nhận request/response thực tế.

Không đọc lại toàn bộ Phase 1A/1B/1C.

Không đọc toàn bộ `docs/use-cases.md`.

Chỉ tra UC01–UC05 nếu phát hiện hành vi Frontend chưa rõ hoặc có khả năng lệch nghiệp vụ.


---

# 3. NGUYÊN TẮC IMPLEMENTATION

Luồng Frontend:

Page / UI
→ Feature / Hook / Auth State
→ API Service
→ Backend

Không gọi `fetch()` trực tiếp rải rác trong presentation components.

Không duplicate API client.

Không hard-code Backend URL.

Không dùng `any`.

Không mock Backend.

Không lưu Access Token hoặc Refresh Token trong localStorage/sessionStorage.


---

# 4. API BASE URL

Sử dụng biến môi trường đã có:

NEXT_PUBLIC_API_BASE_URL

Mọi API request phải đi qua API client/service chung.

Không hard-code:

http://localhost:8000

trực tiếp trong component.


---

# 5. AUTH STATE

Tạo authentication state dùng chung cho ứng dụng.

Phải quản lý tối thiểu:

- user
- accessToken
- authStatus

authStatus:

- loading
- authenticated
- unauthenticated


Access Token:

- chỉ giữ trong memory
- không localStorage
- không sessionStorage

Refresh Token:

- do Backend quản lý bằng HttpOnly Cookie
- Frontend không được đọc trực tiếp.


---

# 6. AUTH RESTORE KHI RELOAD

Khi application khởi tạo:

1. authStatus = loading.
2. Gọi `POST /api/v1/auth/refresh`.
3. Browser gửi HttpOnly Cookie bằng `credentials: include`.
4. Nếu refresh thành công:
   - lưu access token vào memory.
   - gọi `GET /api/v1/users/me`.
   - lưu user.
   - authStatus = authenticated.
5. Nếu refresh thất bại:
   - clear access token.
   - clear user.
   - authStatus = unauthenticated.

Không hiển thị nháy giao diện Guest trước khi restore auth hoàn tất.


---

# 7. API CLIENT

API client phải:

- dùng `NEXT_PUBLIC_API_BASE_URL`
- hỗ trợ JSON request/response
- hỗ trợ Authorization Bearer Token
- hỗ trợ `credentials: include`
- parse Error Contract Backend thống nhất

Với protected API:

Nếu Access Token hết hạn và request trả HTTP 401:

1. thử refresh MỘT lần.
2. nếu refresh thành công:
   retry request ban đầu MỘT lần.
3. nếu refresh thất bại:
   clear auth state.
4. không retry vô hạn.

Phải có cơ chế ngăn recursive refresh loop.


---

# 8. API SERVICES

Tạo/reuse service phù hợp cho:

## Auth

- register
- login
- refresh
- logout

## User

- get current user
- update current user
- change password

Không đưa logic HTTP trực tiếp vào Form component.


---

# 9. TYPESCRIPT TYPES

Type phải phản ánh Backend contract hiện tại.

Tối thiểu:

- User
- AccountStatus
- SystemRole
- RegisterRequest
- LoginRequest
- LoginResponse
- RefreshResponse
- UpdateProfileRequest
- ChangePasswordRequest
- ApiError

Không copy password_hash hoặc refresh_token_hash vào Frontend types.


---

# 10. UC01 — REGISTER

Route:

`/register`

Form gồm đúng:

- Họ tên
- Email
- Mật khẩu
- Xác nhận mật khẩu

Main Flow:

1. User mở `/register`.
2. Nhập thông tin.
3. Frontend validate cơ bản.
4. Submit API Register.
5. Hiển thị trạng thái đang xử lý.
6. Nếu thành công:
   điều hướng `/login`.

QUAN TRỌNG:

Đăng ký thành công KHÔNG tự login.

Điều này phải giữ đúng UC01.


---

# 11. REGISTER VALIDATION

Frontend kiểm tra tối thiểu:

- required fields
- email format
- password 8–128 ký tự
- password confirmation match

Frontend validation chỉ phục vụ UX.

Backend vẫn là nguồn validation cuối cùng.

Nếu Backend trả field validation error:

Hiển thị lỗi đúng trường tương ứng.


---

# 12. REGISTER STATES

Form phải có:

- idle
- submitting
- error

Trong lúc submitting:

- tránh submit lặp
- button có trạng thái disabled/loading

Duplicate email:

Hiển thị lỗi phù hợp từ:

EMAIL_ALREADY_EXISTS


---

# 13. UC02 — LOGIN

Route:

`/login`

Fields:

- Email
- Mật khẩu

Login thành công:

1. Nhận Access Token.
2. Lưu Access Token trong memory.
3. Lưu User vào auth state.
4. authStatus = authenticated.
5. Điều hướng `/app`.

Backend tự set Refresh Cookie.


---

# 14. LOGIN ERROR

INVALID_CREDENTIALS:

Hiển thị:

"Email hoặc mật khẩu không chính xác"

Không phân biệt:

- email không tồn tại
- password sai


ACCOUNT_LOCKED:

Hiển thị thông báo tài khoản đang bị khóa.


Không log:

- password
- access token
- refresh information


---

# 15. AUTHENTICATED LANDING PAGE

Route:

`/app`

Đây là trang chính tối thiểu của Phase 1.

Chỉ cần:

- xác nhận user đã authenticated
- hiển thị tên người dùng
- link đến Profile
- link đến Security/Change Password
- Logout

Không triển khai Workspace tại Phase 1D.


---

# 16. PROTECTED ROUTES

Các route cần authentication:

- `/app`
- `/profile`
- `/settings/security`

Khi authStatus = loading:

Hiển thị loading state phù hợp.

Khi authStatus = unauthenticated:

Điều hướng `/login`.

Không redirect trước khi auth restore hoàn tất.


---

# 17. GUEST ROUTES

Các route:

- `/login`
- `/register`

Nếu User đã authenticated và truy cập các route trên:

Điều hướng về `/app`.

Không bắt buộc nếu implementation hiện tại có lý do kỹ thuật rõ ràng khác,
nhưng không được tạo vòng lặp redirect.


---

# 18. UC03 — LOGOUT

Logout phải gọi:

POST /api/v1/auth/logout

Nếu thành công:

1. clear access token.
2. clear user.
3. authStatus = unauthenticated.
4. điều hướng `/login`.

Không được chỉ clear Frontend state mà bỏ qua Backend logout.


Nếu request logout gặp lỗi mạng:

Không được làm UI treo vô hạn.

Xử lý theo error contract hiện có và đảm bảo trạng thái UI rõ ràng.


---

# 19. UC04 — PROFILE

Route:

`/profile`

Hiển thị:

- Họ tên
- Email

Theo quyết định Phase 1:

`full_name`:
editable

`email`:
read-only


Không thêm:

- avatar
- phone
- birthday
- address
- bio
- gender


---

# 20. PROFILE FLOW

Main Flow:

1. Load current User.
2. Hiển thị thông tin.
3. User chọn chỉnh sửa.
4. Cho phép sửa `full_name`.
5. User chọn lưu.
6. Gọi PATCH profile API.
7. Update auth user state bằng response mới.
8. Hiển thị thông báo thành công.


Alternative — chỉ xem:

Không gọi update API.


Alternative — Hủy:

- bỏ dữ liệu edit chưa lưu
- khôi phục giá trị trước chỉnh sửa
- không gọi update API


Validation error:

Hiển thị đúng field.


---

# 21. UC05 — CHANGE PASSWORD

Route:

`/settings/security`

Form:

- Mật khẩu hiện tại
- Mật khẩu mới
- Xác nhận mật khẩu mới

Frontend validation:

- required
- new password 8–128 ký tự
- confirmation match

Không hiển thị password hiện tại từ server.

Không log password.


---

# 22. CHANGE PASSWORD FLOW

1. User nhập ba field.
2. Submit.
3. Gọi Change Password API.
4. Nếu thành công:
   - clear toàn bộ password fields.
   - hiển thị success message.
   - giữ current session.
5. Không tự logout User.


Errors cần hiển thị phù hợp:

- CURRENT_PASSWORD_INCORRECT
- NEW_PASSWORD_SAME_AS_CURRENT
- PASSWORD_CONFIRMATION_MISMATCH
- VALIDATION_ERROR


---

# 23. FORM UX

Tất cả form phải:

- có label rõ ràng
- disabled submit khi đang request
- hiển thị loading
- hiển thị field error
- hiển thị business error
- tránh duplicate submit
- không mất toàn bộ input không cần thiết khi API lỗi

Không cần animation phức tạp.


---

# 24. UI SCOPE

Phase này ưu tiên:

- đúng nghiệp vụ
- dễ dùng
- responsive cơ bản
- cấu trúc component sạch
- nhất quán giao diện

Không dành thời gian xây design system lớn.

Nếu project đã có Tailwind/components dùng chung:

reuse.

Không thêm UI library mới nếu không cần.


---

# 25. SERVER / CLIENT COMPONENTS

Sử dụng Next.js App Router đúng cách.

Không biến toàn bộ application thành Client Component nếu không cần.

Các component cần:

- form state
- browser APIs
- Auth Context/state
- event handlers

mới sử dụng `"use client"`.

Không ép Server Component nếu nghiệp vụ cần client state.


---

# 26. ERROR HANDLING

Frontend phải sử dụng Error Contract Backend hiện tại.

Không tự suy luận lỗi bằng string parsing nếu Backend đã trả error code.

Ưu tiên xử lý theo:

error.code

Field validation:

error.fields


Unknown/network error:

Hiển thị thông báo chung phù hợp.

Không show raw stack trace cho User.


---

# 27. LOADING STATES

Phải có loading state ít nhất cho:

- Auth restore
- Register
- Login
- Logout
- Load Profile
- Update Profile
- Change Password

Không để người dùng tưởng request chưa chạy.


---

# 28. KHÔNG ĐƯỢC SỬA BACKEND TÙY Ý

Backend Phase 1B + 1C đã nghiệm thu.

Frontend phải tích hợp theo Backend hiện tại.

Nếu phát hiện Frontend không thể tích hợp vì:

- API contract thực tế khác requirements
- cookie/CORS lỗi
- Backend response sai
- Backend bug

thì:

DỪNG thay đổi Backend.

Ghi rõ:

- endpoint
- lỗi
- file Backend có khả năng liên quan
- thay đổi tối thiểu đề xuất

Chờ Tech Lead nếu thay đổi làm ảnh hưởng contract/nghiệp vụ.

Nếu chỉ là bug implementation rõ ràng, không thay đổi contract và việc sửa là cần thiết để integration hoạt động, được phép sửa tối thiểu và phải ghi vào handoff.


---

# 29. KHÔNG LÀM TRONG PHASE 1D

Không:

- Workspace UI
- Channel UI
- Chat
- WebSocket
- Study Room
- Document
- AI/RAG
- Admin
- Forgot Password
- Reset Password
- Email Verification
- OAuth
- Google Login
- Remember Me
- avatar upload
- Redis
- MinIO
- frontend test suite lớn nếu project chưa có infrastructure
- full Backend regression lại từ đầu


---

# 30. VERIFICATION

Trong quá trình code:

Chỉ kiểm tra targeted phần đang triển khai.

Sau khi hoàn thành toàn bộ Phase 1D:

Chạy MỘT lần:

npm run lint

npm run build


Ngoài ra xác nhận manual/dev integration:

- Register gọi Backend thật.
- Login gọi Backend thật.
- Auth restore sau reload.
- Protected route hoạt động.
- Logout hoạt động.
- Profile load/update hoạt động.
- Change Password hoạt động.

Không chạy lại toàn bộ Backend test suite của Phase 1C nếu không sửa Backend.


---

# 31. DEFINITION OF DONE

Phase 1D DONE khi:

- `/register` hoạt động.
- Register không tự login.
- `/login` hoạt động.
- Login giữ Access Token trong memory.
- Refresh Cookie hoạt động qua Backend.
- Reload khôi phục authentication.
- `/app` được bảo vệ.
- `/profile` được bảo vệ.
- Profile xem được.
- Profile update full_name được.
- Email read-only.
- Cancel edit không gọi API.
- Logout gọi Backend.
- `/settings/security` hoạt động.
- Change Password hoạt động.
- Loading/Error states đầy đủ.
- Không có token trong localStorage/sessionStorage.
- Không dùng `any`.
- Không mock Backend.
- `npm run lint` PASS.
- `npm run build` PASS.


---

# 32. HANDOFF

Sau khi hoàn thành và verification PASS:

## README.md

Chỉ cập nhật trạng thái:

- Phase 1A: DONE
- Phase 1B: DONE
- Phase 1C: DONE
- Phase 1D: DONE
- Current next stage: Phase 1E — Integration & Regression
- Latest handoff:
  `docs/progress/phase-1d-verification.md`

Không ghi log dài.


## Tạo:

`docs/progress/phase-1d-verification.md`

Nội dung ngắn gọn:

# Phase 1D Verification

Status:
DONE / FAILED

Implemented:
- ...

Files changed:
- ...

Verification:
- lint
- build
- frontend/backend checks

Backend changes:
- None
hoặc thay đổi tối thiểu nếu có

Remaining issues:
- ...

Next:
Phase 1E — Integration & Regression


Không lưu full terminal log.


---

# 33. OUTPUT CHAT

Chỉ trả:

DONE hoặc FAILED

Lint: PASS/FAIL
Build: PASS/FAIL

Files changed:
- ...

Handoff:
docs/progress/phase-1d-verification.md

Remaining issue:
<none hoặc mô tả ngắn>

Không chào hỏi.
Không giải thích lý thuyết.
Không paste code.
Không paste terminal log.