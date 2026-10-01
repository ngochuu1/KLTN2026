"use client";
import { useEffect, useRef, useState } from "react";
import { chatAuth } from "@/features/auth/store";
import type { Channel } from "@/lib/chat-types";
import { connectRoom, type RoomState } from "./realtime";
import { MediaPanel } from "./media-view";

export function StudyRoom({ channel }: { channel: Channel }) {
  const [room, setRoom] = useState<RoomState | null>(null);
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const [mediaActive, setMediaActive] = useState(false);
  const [mediaError, setMediaError] = useState("");
  const connection = useRef<ReturnType<typeof connectRoom> | null>(null);
  useEffect(() => {
    const client = connectRoom(channel.id, chatAuth, state => { setRoom(state); setPending(false); setError(""); }, message => { setRoom(null); setPending(false); setError(message); });
    connection.current = client;
    return () => { connection.current = null; client.close(); };
  }, [channel.id, attempt]);
  return <section aria-label="Phòng tự học">
    <h3>Phòng tự học · {channel.name}</h3>
    {mediaError && <p role="alert">{mediaError}</p>}
    {room?.self_state === "IN_ROOM" && mediaActive && !error ? <MediaPanel id={channel.id}
      sync={devices => connection.current?.devices(devices)}
      onDisconnect={() => { setMediaActive(false); setMediaError("Media đã ngắt hoặc không thể kết nối. Hãy tham gia lại phòng."); connection.current?.command("leave"); }} /> :
      <div className="actions"><button disabled>Microphone: OFF</button><button disabled>Camera: OFF</button><button disabled>Chia sẻ màn hình</button></div>}
    {error ? <><p role="alert" className="error">{error}</p><button onClick={() => { setError(""); setRoom(null); setAttempt(n => n + 1); }}>Kết nối lại</button></> : !room ? <p role="status">Đang tải phòng…</p> : <>
      <p role="status">{room.self_state === "IN_ROOM" ? "Bạn đang ở trong phòng." : "Bạn đang ở ngoài phòng."}</p>
      <button disabled={pending} onClick={() => { setPending(true); setMediaError(""); setMediaActive(room.self_state !== "IN_ROOM"); connection.current?.command(room.self_state === "IN_ROOM" ? "leave" : "join"); }}>{room.self_state === "IN_ROOM" ? "Rời phòng" : "Tham gia phòng"}</button>
      <h4>Thành viên trong phòng ({room.participants.length})</h4>
      {!room.participants.length && <p>Chưa có thành viên trong phòng.</p>}
      <ul aria-label="Thành viên trong phòng">{room.participants.map(person => <li key={person.user_id}>{person.full_name} · Đang trong phòng · Microphone: {person.microphone_enabled ? "ON" : "OFF"} · Camera: {person.camera_enabled ? "ON" : "OFF"} · Màn hình: {person.screen_sharing ? "ON" : "OFF"}</li>)}</ul>
    </>}
  </section>;
}
