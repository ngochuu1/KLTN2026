// The browser cannot follow a bearer-authenticated cross-origin redirect to a
// private S3 bucket without bucket CORS. Relay the authorized download server-side.
export async function GET(request: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const base = process.env.NEXT_PUBLIC_API_BASE_URL;
  const authorization = request.headers.get("authorization");
  const failure = (status: number, code: string, message: string) => Response.json({ error: { code, message, fields: null } }, { status });
  if (!authorization) return failure(401, "AUTHENTICATION_REQUIRED", "Yêu cầu đăng nhập");
  if (!/^[0-9a-f-]{36}$/i.test(id)) return failure(422, "VALIDATION_ERROR", "Tệp không hợp lệ");
  if (!base) return failure(503, "CONFIGURATION_ERROR", "Chưa cấu hình địa chỉ API");
  try {
    const response = await fetch(`${base.replace(/\/$/, "")}/api/v1/attachments/${id}/download`, {
      headers: { Authorization: authorization }, redirect: "manual", cache: "no-store", signal: AbortSignal.timeout(15000),
    });
    if (response.status !== 307) {
      if (!response.ok) return new Response(response.body, { status: response.status, headers: { "Content-Type": "application/json", "Cache-Control": "no-store" } });
      return failure(502, "ATTACHMENT_DOWNLOAD_FAILED", "Không thể tải tệp");
    }
    const location = response.headers.get("location");
    if (!location || !/^https?:\/\//.test(location)) return failure(502, "ATTACHMENT_DOWNLOAD_FAILED", "Không thể tải tệp");
    // Never forward the application bearer token to object storage.
    const object = await fetch(location, { cache: "no-store", redirect: "error", signal: AbortSignal.timeout(120000) });
    if (!object.ok) return failure(502, "ATTACHMENT_DOWNLOAD_FAILED", "Không thể tải tệp");
    return new Response(object.body, { headers: { "Content-Type": "application/octet-stream", "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff" } });
  } catch { return failure(502, "ATTACHMENT_DOWNLOAD_FAILED", "Không thể tải tệp. Vui lòng thử lại."); }
}
