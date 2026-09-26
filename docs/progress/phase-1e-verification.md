# Phase 1E Verification

Status: DONE

Integration flows PASS/FAIL:
- Flow 1 — Register: PASS; tạo tài khoản mới, chuyển `/login`, không tự đăng nhập và không có refresh cookie.
- Flow 2 — Login: PASS; credentials hợp lệ chuyển `/app`, hiển thị đúng user.
- Flow 3 — Auth restore: PASS; reload vẫn authenticated qua refresh session.
- Flow 4 — Invalid login: PASS; sai password hiển thị lỗi credentials, không crash.
- Flow 5 — Profile: PASS; full_name/email đúng, email read-only; lưu tên mới và reload vẫn giữ dữ liệu.
- Flow 6 — Cancel profile edit: PASS; hủy khôi phục tên đã lưu, không gửi PATCH.
- Flow 7 — Change password: PASS; current session vẫn hoạt động sau reload; browser context riêng không login được bằng password cũ, login được bằng password mới.
- Flow 8 — Logout: PASS; Backend POST logout trả 204, xóa cookie, chuyển `/login`; PostgreSQL xác nhận session bị revoke.
- Flow 9 — Protected routes: PASS; sau logout, `/app`, `/profile`, `/settings/security` chuyển `/login`, không có nội dung protected sau khi guard hoàn tất.
- Frontend ↔ Backend thật: PASS; Chromium gọi Next.js local → FastAPI Windows qua TCP forward local → PostgreSQL thật, không mock.
- PostgreSQL persistence: PASS; truy vấn DB độc lập xác nhận full_name mới, hash xác thực password mới và từ chối password cũ, session logout đã revoke. Đã xóa đúng tài khoản và hai session tạm của lượt kiểm tra.
- Regression: PASS; chạy một lần `python -m unittest tests.test_account_api -v`, 26/26 tests trên PostgreSQL `kltn_test` riêng. Không thay đổi source; giữ kết quả lint/build Phase 1D đã được nghiệm thu, không chạy lại dư thừa.

Bugs fixed:
- Không phát hiện bug source. Lượt browser đầu thiếu `NEXT_PUBLIC_API_BASE_URL`; bổ sung biến môi trường khi chạy theo `.env.example`, kiểm tra lại thành công; không sửa file cấu hình/source.

Files changed:
- `README.md`
- `docs/progress/phase-1e-verification.md`

Remaining issues:
- None.

Phase 1 completion status:
- COMPLETED — UC01–UC05, auth restore, protected routes, tích hợp thực tế và PostgreSQL persistence PASS; không còn blocker Phase 1.

Next stage:
- Phase 2.
