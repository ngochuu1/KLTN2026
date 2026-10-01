"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { chatAuth, chatServices as api } from "@/features/auth/store";
import type { ChatEvent, Message } from "@/lib/chat-types";
import { applyEvent, applyRest, emptyChat, mergeHistory, type ChatState } from "./state";
import { connectChat } from "./realtime";
export function useChat(id: string) {
  const [state, setState] = useState(emptyChat);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [connection, setConnection] = useState("Đang kết nối…");
  const [more, setMore] = useState(false);
  const cursor = useRef<string | undefined>(undefined);
  const active = useRef(false);
  const generation = useRef(0);
  const fetching = useRef(false);
  const buffer = useRef<((current: ChatState) => ChatState)[] | null>(null);
  const reactionRevision = useRef(new Map<string, number>());
  const receive = useCallback((event: ChatEvent) => {
    if (!active.current) return;
    if ((event.type === "message.created" || event.type === "message.updated") && event.data.channel_id !== id) return;
    if (event.type === "reaction.updated") reactionRevision.current.set(event.data.message_id, (reactionRevision.current.get(event.data.message_id) ?? 0) + 1);
    buffer.current?.push(current => applyEvent(current, event));
    setState(current => applyEvent(current, event));
  }, [id]);
  const load = useCallback(async (older = false) => {
    if (fetching.current || !active.current) return;
    const started = generation.current;
    fetching.current = true; buffer.current = []; setLoading(true); setError("");
    try {
      const page = await api.history(id, older ? cursor.current : undefined);
      if (!active.current || started !== generation.current) return;
      const events = buffer.current ?? [];
      setState(current => events.reduce((next, update) => update(next), older ? mergeHistory(current, page) : mergeHistory(emptyChat, page)));
      cursor.current = page.at(-1)?.id; setMore(page.length === 50);
    } catch (failure) { if (active.current && started === generation.current) setError(failure instanceof Error ? failure.message : "Không thể tải tin nhắn."); }
    finally { if (started === generation.current) { fetching.current = false; buffer.current = null; if (active.current) setLoading(false); } }
  }, [id]);
  useEffect(() => {
    const started = generation.current;
    active.current = true;
    const disconnect = connectChat(id, chatAuth, receive, setConnection, () => { void load(); });
    void load();
    return () => { active.current = false; generation.current = started + 1; fetching.current = false; buffer.current = null; disconnect(); };
  }, [id, load, receive]);
  function saved(message: Message) {
    if (!active.current) return;
    buffer.current?.push(current => applyRest(current, message));
    setState(current => applyRest(current, message));
  }
  async function react(messageId: string, emoji: string, remove = false) {
    const revision = reactionRevision.current.get(messageId) ?? 0;
    if (!remove) {
      const reactions = await api.react(messageId, emoji);
      if ((reactionRevision.current.get(messageId) ?? 0) === revision) receive({ type: "reaction.updated", data: { message_id: messageId, reactions } });
    } else {
      await api.unreact(messageId, emoji);
      if ((reactionRevision.current.get(messageId) ?? 0) !== revision || !active.current) return;
      // The DELETE response is empty and summaries do not identify reactors.
      // Fetch the target's page, including when it is in older loaded history.
      const index = state.messages.findIndex(message => message.id === messageId);
      const page = await api.history(id, state.messages[index + 1]?.id);
      const message = page.find(item => item.id === messageId);
      if (message && (reactionRevision.current.get(messageId) ?? 0) === revision) receive({ type: "reaction.updated", data: { message_id: messageId, reactions: message.reactions } });
    }
  }
  return { messages: state.messages, loading, error, connection, more, load, receive, saved, react };
}
