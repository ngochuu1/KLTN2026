import { createApiClient, type AuthBridge } from "./api";
import type { Channel, ChannelInput, Message, Reaction } from "./chat-types";
export function createChatServices(bridge: AuthBridge) {
  const request = createApiClient(bridge);
  const options = { protected: true };
  return {
    channels: (workspace: string) => request<Channel[]>(`/workspaces/${workspace}/channels`, options),
    createChannel: (workspace: string, body: ChannelInput) => request<Channel>(`/workspaces/${workspace}/channels`, { ...options, method: "POST", body }),
    updateChannel: (id: string, body: Omit<ChannelInput, "type">) => request<Channel>(`/channels/${id}`, { ...options, method: "PATCH", body }),
    deleteChannel: (id: string) => request<void>(`/channels/${id}`, { ...options, method: "DELETE" }),
    history: (id: string, before?: string) => request<Message[]>(`/channels/${id}/messages?limit=50${before ? `&before_message_id=${encodeURIComponent(before)}` : ""}`, options),
    send: (id: string, content: string) => request<Message>(`/channels/${id}/messages`, { ...options, method: "POST", body: { content } }),
    upload: (id: string, file: File, content: string) => {
      const body = new FormData(); body.append("file", file); if (content.trim()) body.append("content", content.trim());
      return request<Message>(`/channels/${id}/messages/attachments`, { ...options, method: "POST", body });
    },
    edit: (id: string, content: string) => request<Message>(`/messages/${id}`, { ...options, method: "PATCH", body: { content } }),
    remove: (id: string) => request<void>(`/messages/${id}`, { ...options, method: "DELETE" }),
    react: (id: string, emoji: string) => request<Reaction[]>(`/messages/${id}/reactions/${encodeURIComponent(emoji)}`, { ...options, method: "PUT" }),
    unreact: (id: string, emoji: string) => request<void>(`/messages/${id}/reactions/${encodeURIComponent(emoji)}`, { ...options, method: "DELETE" }),
    download: (id: string) => request<Blob>(`/attachments/${id}/download`, { ...options, download: true }),
  };
}
