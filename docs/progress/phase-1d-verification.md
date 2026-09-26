# Phase 1D Verification

Status: DONE

Implemented:
- Next.js App Router: `/register`, `/login`, `/app`, `/profile`, `/settings/security`; chỉ UC01–UC05.
- Auth state dùng chung: user, access token trong memory, loading/authenticated/unauthenticated; restore qua refresh cookie và `/users/me`, bảo vệ route và guest redirect.
- API client chung sử dụng `NEXT_PUBLIC_API_BASE_URL`, credentials, Bearer token, error contract/field errors; refresh single-flight, protected 401 refresh/retry tối đa một lần, timeout request 15 giây.
- Register không tự login; profile chỉ sửa full_name, email read-only, hủy không gọi API; đổi mật khẩu xóa input và giữ phiên; logout gọi Backend, báo lỗi mạng và cho thử lại.
- Form loading/disabled, validation và giao diện responsive tiếng Việt; không thêm UI library, không mock Backend, không lưu token vào browser storage.

Files changed:
- `frontend/.env.example`, `frontend/.gitignore`
- `frontend/package.json`, `frontend/package-lock.json`
- `frontend/tsconfig.json`, `frontend/next.config.ts`, `frontend/eslint.config.mjs`
- `frontend/src/lib/types.ts`, `frontend/src/lib/api.ts`, `frontend/src/lib/services.ts`
- `frontend/src/features/auth/store.ts`, `frontend/src/features/auth/provider.tsx`, `frontend/src/features/auth/account-forms.tsx`
- `frontend/src/components/forms.tsx`
- `frontend/src/app/layout.tsx`, `frontend/src/app/page.tsx`, `frontend/src/app/globals.css`
- `frontend/src/app/(guest)/layout.tsx`, `frontend/src/app/(guest)/login/page.tsx`, `frontend/src/app/(guest)/register/page.tsx`
- `frontend/src/app/(protected)/layout.tsx`, `frontend/src/app/(protected)/app/page.tsx`, `frontend/src/app/(protected)/profile/page.tsx`, `frontend/src/app/(protected)/settings/security/page.tsx`
- `docs/progress/phase-1d-verification.md`
- `README.md` — cập nhật trạng thái Phase 1D và latest handoff.

Verification:
- `npm run lint`: PASS, chạy một lần trong `frontend`.
- Build: PASS — verified locally. Tech Lead xác nhận production build bằng `npm run build` trên máy local.
- Targeted `tsc --noEmit`: PASS từ lượt trước.
- Lỗi đọc output TypeScript trong sandbox trước đây là giới hạn môi trường; không sửa source/config để né lỗi. Lượt cập nhật này chỉ sửa tài liệu theo xác nhận của Tech Lead, không chạy lại test/build.
- Dev integration bằng Chromium/Playwright tạm ngoài repository, gọi FastAPI/PostgreSQL thật: PASS đăng ký và chuyển login không có refresh cookie, login sai/đúng, HttpOnly cookie, reload restore, ba protected routes, guest redirect.
- PASS profile load/update và đồng bộ tên ở `/app`, email read-only, hủy edit không PATCH; change password xóa ba input, reload vẫn giữ phiên; logout xóa cookie, reload vẫn guest.
- PASS logout khi browser offline: hiển thị lỗi, nút hoạt động trở lại; shared API client gọi Backend thật với Bearer không hợp lệ: refresh/retry một lần thành công; refresh thất bại clear auth, không recursion.
- Viewport mobile 390×844, không runtime page error; localStorage/sessionStorage rỗng. Source chỉ có fetch trong API client, không dùng `any`.
- Không chạy lại Backend test suite. Đã xóa đúng hai tài khoản/session tạm do kiểm tra tạo ra; không thêm test infrastructure vào project.

Local development:
- Node.js 22; trong `frontend`: `npm ci`, copy `.env.example` thành `.env.local`, đặt `NEXT_PUBLIC_API_BASE_URL` là origin Backend (không thêm `/api/v1`), chạy `npm run dev`.
- Backend chạy theo README; dùng frontend `http://localhost:3000` và Backend `http://localhost:8000` với cấu hình local hiện có. Kiểm tra trong WSL đã dùng TCP forward tạm đến Backend Windows để giữ localhost/cookie/CORS; không thay đổi Backend.

Backend changes:
- None.

Remaining issues:
- None.

Next:
Phase 1E — Integration & Regression.
