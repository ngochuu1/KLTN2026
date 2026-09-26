import { createApiClient, type AuthBridge } from "./api";
import type { Workspace, WorkspaceInput, WorkspaceMember, Invitation, InvitationInput, InvitationPreview } from "./workspace-types";
export function createWorkspaceServices(bridge: AuthBridge) {
  const api = createApiClient(bridge);
  const path = (id: string) => `/workspaces/${encodeURIComponent(id)}`;
  const invitation = (token: string) => `/workspace-invitations/${encodeURIComponent(token)}`;
  return {
    list: () => api<Workspace[]>("/workspaces", { protected: true }),
    create: (body: WorkspaceInput) => api<Workspace>("/workspaces", { method: "POST", body, protected: true }),
    detail: (id: string) => api<Workspace>(path(id), { protected: true }),
    update: (id: string, body: WorkspaceInput) => api<Workspace>(path(id), { method: "PATCH", body, protected: true }),
    remove: (id: string) => api<void>(path(id), { method: "DELETE", protected: true }),
    leave: (id: string) => api<void>(`${path(id)}/leave`, { method: "POST", protected: true }),
    members: (id: string) => api<WorkspaceMember[]>(`${path(id)}/members`, { protected: true }),
    removeMember: (id: string, userId: string) => api<void>(`${path(id)}/members/${encodeURIComponent(userId)}`, { method: "DELETE", protected: true }),
    changeRole: (id: string, userId: string, role: "ADMIN" | "MEMBER") => api<WorkspaceMember>(`${path(id)}/members/${encodeURIComponent(userId)}/role`, { method: "PATCH", body: { role }, protected: true }),
    invite: (id: string, body: InvitationInput) => api<Invitation & { token: string }>(`${path(id)}/invitations`, { method: "POST", body, protected: true }),
    preview: (token: string) => api<InvitationPreview>(invitation(token), { protected: true }),
    accept: (token: string) => api<Workspace>(`${invitation(token)}/accept`, { method: "POST", protected: true }),
    decline: (token: string) => api<Invitation>(`${invitation(token)}/decline`, { method: "POST", protected: true }),
  };
}
