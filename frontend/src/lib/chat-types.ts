export interface Channel { id: string; workspace_id: string; name: string; description: string | null; type: "TEXT" | "STUDY_ROOM"; is_default: boolean; created_at: string; updated_at: string }
export interface ChannelInput { name: string; description: string | null; type: Channel["type"] }
export interface Attachment { id: string; original_filename: string; content_type: string; size_bytes: number }
export interface Reaction { emoji: string; count: number }
export interface Message { id: string; channel_id: string; content: string | null; sender: { id: string; full_name: string }; created_at: string; edited_at: string | null; attachments: Attachment[]; reactions: Reaction[] }
export type ChatEvent = { type: "message.created" | "message.updated"; data: Message } | { type: "message.deleted"; data: { message_id: string } } | { type: "reaction.updated"; data: { message_id: string; reactions: Reaction[] } };
