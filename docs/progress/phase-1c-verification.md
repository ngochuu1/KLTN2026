# Phase 1C Verification

Status: DONE

Tests:
- total: 26
- passed: 26
- failed: 0
- skipped: 0

Verification:
- Chạy từ `backend`: `.venv-win/Scripts/python.exe -m unittest tests.test_account_api -v`.
- Dependency test: `python -m pip install -r requirements-test.txt`.
- PostgreSQL riêng `kltn_test`, lấy từ `TEST_DATABASE_URL` trong environment hoặc `backend/.env`; từ chối development database và database có dữ liệu account/bảng ngoài phạm vi.
- Áp dụng Alembic hiện tại; mỗi test dùng outer transaction và request session/savepoint, rollback sau test. Kiểm tra database không còn dữ liệu sau suite.
- HTTPX ASGITransport gọi trực tiếp FastAPI, không mock nghiệp vụ/PostgreSQL.
- Bao phủ R1–R7, L1–L5, F1–F7, O1–O3, P1–P5, C1–C6; P6 thuộc Frontend, không cần test Backend.
- Kiểm tra error envelope, password/refresh hash, không lộ credentials và cô lập session.
- Lifespan startup/shutdown thật và health endpoint PASS trên database test.

Files changed:
- `backend/requirements-test.txt`
- `backend/tests/test_account_api.py`
- `README.md` — chỉ cập nhật trạng thái hiện tại.
- `docs/progress/phase-1c-verification.md`

Bugs fixed:
- Không phát hiện bug; không sửa implementation, API/database contract hoặc nghiệp vụ.

Remaining issues:
- none

Next:
Phase 1D — Account/Auth Frontend
