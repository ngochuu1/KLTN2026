import type { ApiError } from "./types";
export class ApiFailure extends Error {
  constructor(public status: number, public error: ApiError) { super(error.message); }
}
export interface AuthBridge { getToken: () => string | null; refresh: () => Promise<string>; clear: () => void }
export function createApiClient(auth: AuthBridge) {
  return async function request<T>(path: string, options: { method?: string; body?: unknown; protected?: boolean } = {}): Promise<T> {
    const base = process.env.NEXT_PUBLIC_API_BASE_URL;
    if (!base) throw new ApiFailure(0, { code: "CONFIGURATION_ERROR", message: "Chưa cấu hình địa chỉ API.", fields: null });
    async function send(token: string | null): Promise<T> {
      let response: Response;
      try {
        response = await fetch(`${base!.replace(/\/$/, "")}/api/v1${path}`, {
          method: options.method ?? "GET", credentials: "include", cache: "no-store",
          headers: { ...(options.body ? { "Content-Type": "application/json" } : {}), ...(token ? { Authorization: `Bearer ${token}` } : {}) },
          body: options.body ? JSON.stringify(options.body) : undefined,
          signal: AbortSignal.timeout(15000),
        });
      } catch { throw new ApiFailure(0, { code: "NETWORK_ERROR", message: "Không thể kết nối máy chủ. Vui lòng thử lại.", fields: null }); }
      if (!response.ok) {
        let error: ApiError = { code: "UNKNOWN_ERROR", message: "Yêu cầu thất bại. Vui lòng thử lại.", fields: null };
        try {
          const payload: { error?: ApiError } = await response.json();
          if (payload.error && typeof payload.error.code === "string") error = payload.error;
        } catch { /* Non-JSON server/proxy response. */ }
        throw new ApiFailure(response.status, error);
      }
      if (response.status === 204) return undefined as T;
      const payload: { data: T } = await response.json();
      return payload.data;
    }
    const token = options.protected ? auth.getToken() : null;
    try { return await send(token); }
    catch (error) {
      if (!options.protected || !(error instanceof ApiFailure) || error.status !== 401) throw error;
      // Refresh uses an unprotected request, so it can never recurse here.
      let replacement: string;
      try { replacement = auth.getToken() !== token && auth.getToken() ? auth.getToken()! : await auth.refresh(); }
      catch (refreshError) { auth.clear(); throw refreshError; }
      try { return await send(replacement); }
      catch (retryError) {
        if (retryError instanceof ApiFailure && retryError.status === 401) auth.clear();
        throw retryError;
      }
    }
  };
}
