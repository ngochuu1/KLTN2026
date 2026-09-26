from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from app.core.exceptions import AppError
from app.schemas.common import ErrorDetail, ErrorResponse


def error_response(
    status: int, code: str, message: str,
    fields: dict[str, list[str]] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content=ErrorResponse(error=ErrorDetail(code=code, message=message, fields=fields)).model_dump(),
        headers=headers,
    )


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    headers = {"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None
    return error_response(exc.status_code, exc.code, exc.message, exc.fields, headers)


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    fields: dict[str, list[str]] = {}
    errors = exc.errors()
    confirmation_only = bool(errors) and all(
        error["type"] == "PASSWORD_CONFIRMATION_MISMATCH"
        and error["loc"][-1] == "confirm_new_password"
        for error in errors
    )
    for error in errors:
        location = [str(part) for part in error["loc"] if part not in ("body", "query", "path", "header", "cookie")]
        field = ".".join(location) or "_request"
        kind = error["type"]
        if kind == "missing":
            message = "Trường này là bắt buộc"
        elif kind == "extra_forbidden":
            message = "Trường này không được phép"
        elif kind == "PASSWORD_CONFIRMATION_MISMATCH":
            message = "Mật khẩu xác nhận không khớp"
        elif field == "email":
            message = "Email không đúng định dạng"
        elif field == "current_password" or (field == "password" and request.url.path.endswith("/auth/login")):
            message = "Mật khẩu phải là chuỗi không rỗng, tối đa 128 ký tự"
        elif field in {"password", "current_password", "new_password", "confirm_password", "confirm_new_password"}:
            message = "Mật khẩu phải là chuỗi từ 8 đến 128 ký tự"
        elif field == "full_name":
            message = "Họ tên phải có từ 1 đến 100 ký tự và không chỉ gồm khoảng trắng"
        else:
            message = "Dữ liệu không hợp lệ"
        fields.setdefault(field, []).append(message)
    code = "PASSWORD_CONFIRMATION_MISMATCH" if confirmation_only else "VALIDATION_ERROR"
    # Never return/log Pydantic input, request body, or exception context.
    return error_response(422, code, "Dữ liệu không hợp lệ", fields)


async def http_error_handler(request: Request, exc: HTTPException) -> JSONResponse:
    codes = {404: ("NOT_FOUND", "Không tìm thấy tài nguyên"),
             405: ("METHOD_NOT_ALLOWED", "Phương thức không được hỗ trợ")}
    code, message = codes.get(exc.status_code, ("HTTP_ERROR", "Không thể thực hiện yêu cầu"))
    return error_response(exc.status_code, code, message, headers=exc.headers)


async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
    return error_response(500, "INTERNAL_SERVER_ERROR", "Đã xảy ra lỗi hệ thống")
