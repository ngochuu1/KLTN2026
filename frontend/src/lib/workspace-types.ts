export type WorkspaceRole = "OWNER" | "ADMIN" | "MEMBER";
export interface Workspace { id: string; name: string; description: string | null; role: WorkspaceRole; created_at: string; updated_at: string }
export interface WorkspaceInput { name: string; description: string | null }
export interface WorkspaceMember { user_id: string; full_name: string; email: string; role: WorkspaceRole; joined_at: string }
export interface InvitationInput { invitee_user_id?: string; expires_at?: string }
export interface Invitation { id: string; workspace_id: string; invitee_user_id: string | null; status: string; expires_at: string | null; created_at: string }
export interface InvitationPreview { workspace_id: string; name: string; description: string | null; expires_at: string | null }
