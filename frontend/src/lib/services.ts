import { createApiClient, type AuthBridge } from "./api";
import type { RegisterRequest, LoginRequest, LoginResponse, RefreshResponse, User, UserProfile, UpdateProfileRequest, ChangePasswordRequest } from "./types";
export function createServices(bridge: AuthBridge) {
  const api = createApiClient(bridge);
  return {
    register: (body: RegisterRequest) => api<User & { created_at: string }>("/auth/register", { method: "POST", body }),
    login: (body: LoginRequest) => api<LoginResponse>("/auth/login", { method: "POST", body }),
    refresh: () => api<RefreshResponse>("/auth/refresh", { method: "POST" }),
    logout: () => api<void>("/auth/logout", { method: "POST", protected: true }),
    me: () => api<UserProfile>("/users/me", { protected: true }),
    update: (body: UpdateProfileRequest) => api<UserProfile>("/users/me", { method: "PATCH", body, protected: true }),
    changePassword: (body: ChangePasswordRequest) => api<void>("/users/me/change-password", { method: "POST", body, protected: true }),
  };
}
