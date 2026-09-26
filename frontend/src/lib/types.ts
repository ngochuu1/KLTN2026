export type AccountStatus = "ACTIVE" | "LOCKED";
export type SystemRole = "USER" | "ADMIN";
export interface User { id: string; full_name: string; email: string; status: AccountStatus; system_role: SystemRole }
export interface UserProfile extends User { created_at: string; updated_at: string }
export interface RegisterRequest { full_name: string; email: string; password: string; confirm_password: string }
export interface LoginRequest { email: string; password: string }
export interface RefreshResponse { access_token: string; token_type: "bearer"; expires_in: number }
export interface LoginResponse extends RefreshResponse { user: User }
export interface UpdateProfileRequest { full_name: string }
export interface ChangePasswordRequest { current_password: string; new_password: string; confirm_new_password: string }
export interface ApiError { code: string; message: string; fields: Record<string, string[]> | null }
