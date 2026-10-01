import type { ChatEvent, Message } from "../../lib/chat-types";
export interface ChatState { messages: Message[]; deleted: string[] }
export const emptyChat: ChatState = { messages: [], deleted: [] };
export function ordered(messages: Message[]) {
  return [...messages].sort((a, b) => a.created_at.localeCompare(b.created_at) || a.id.localeCompare(b.id));
}
export function applyEvent(state: ChatState, event: ChatEvent): ChatState {
  if (event.type === "message.deleted") return { messages: state.messages.filter(m => m.id !== event.data.message_id), deleted: [...new Set([...state.deleted, event.data.message_id])] };
  if (event.type === "reaction.updated") return { ...state, messages: state.messages.map(m => m.id === event.data.message_id ? { ...m, reactions: event.data.reactions } : m) };
  const incoming = event.data;
  if (state.deleted.includes(incoming.id)) return state;
  const existing = state.messages.find(m => m.id === incoming.id);
  if (existing && event.type === "message.created") return state;
  if (existing && (existing.edited_at ?? "") > (incoming.edited_at ?? "")) return state;
  return { ...state, messages: ordered([...state.messages.filter(m => m.id !== incoming.id), incoming]) };
}
export function applyRest(state: ChatState, message: Message): ChatState {
  const existing = state.messages.find(m => m.id === message.id);
  return applyEvent(state, { type: "message.updated", data: existing ? { ...message, reactions: existing.reactions } : message });
}
export function mergeHistory(state: ChatState, page: Message[]): ChatState {
  const known = new Set([...state.messages.map(m => m.id), ...state.deleted]);
  return { ...state, messages: ordered([...state.messages, ...page.filter(m => !known.has(m.id))]) };
}
export function validateFile(file: Pick<File, "name" | "size">): string {
  if (!file.size) return "Tệp không được để trống.";
  if (file.size > 25 * 1024 * 1024) return "Tệp tối đa 25 MB.";
  if (!/\.(pdf|docx?|txt|png|jpe?g)$/i.test(file.name)) return "Chỉ hỗ trợ PDF, Word, TXT, PNG và JPG.";
  return "";
}
