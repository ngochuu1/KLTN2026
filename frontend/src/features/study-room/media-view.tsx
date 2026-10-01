"use client";
import { useEffect, useRef, useState } from "react";
import { Track } from "livekit-client";
import { chatAuth, clearAuth } from "@/features/auth/store";
import { createApiClient } from "@/lib/api";
import { createMedia, type MediaCredential, type MediaSnapshot } from "./media";
import type { Devices } from "./realtime";

function MediaTrack({ track, local }: { track: Track; local: boolean }) {
  const container = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (local && track.kind === Track.Kind.Audio) return;
    const element = track.attach();
    if (element instanceof HTMLVideoElement) { element.playsInline = true; element.style.width = "100%"; element.style.maxWidth = "360px"; }
    element.autoplay = true; element.muted = local;
    container.current?.appendChild(element);
    return () => { track.detach(element); element.remove(); };
  }, [track, local]);
  return <div ref={container} />;
}

export function MediaPanel({ id, sync, onDisconnect }: { id: string; sync: (devices: Devices) => void; onDisconnect: () => void }) {
  const [state, setState] = useState<MediaSnapshot>({ status: "Đang kết nối media…", connected: false, participants: [] });
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);
  const client = useRef<ReturnType<typeof createMedia> | null>(null);
  const callbacks = useRef({ sync, onDisconnect });
  useEffect(() => { callbacks.current = { sync, onDisconnect }; }, [sync, onDisconnect]);
  useEffect(() => {
    const request = createApiClient({ ...chatAuth, clear: clearAuth });
    let last = "";
    const media = createMedia(() => request<MediaCredential>(`/channels/${id}/study-room/media-token`, { method: "POST", protected: true }), snapshot => {
      setState(snapshot);
      const own = snapshot.participants.find(p => p.local);
      if (own && snapshot.connected) {
        const devices = { microphone_enabled: own.microphone_enabled, camera_enabled: own.camera_enabled, screen_sharing: own.screen_sharing };
        const serialized = JSON.stringify(devices);
        if (serialized !== last) { last = serialized; callbacks.current.sync(devices); }
      }
    }, setError, () => { setState({ status: "Đã ngắt kết nối media", connected: false, participants: [] }); callbacks.current.onDisconnect(); });
    client.current = media; void media.connect();
    return () => { client.current = null; media.close(); };
  }, [id]);
  const own = state.participants.find(p => p.local);
  return <section aria-label="Media phòng học">
    <p role="status">{state.status}</p>{error && <p role="alert">{error}</p>}
    <div className="actions">{(["microphone_enabled", "camera_enabled"] as const).map(field => <button key={field}
      disabled={!state.connected || pending} aria-pressed={own?.[field] ?? false}
      onClick={() => { setPending(true); void client.current?.toggle(field, !own?.[field]).finally(() => setPending(false)); }}>
      {field === "microphone_enabled" ? "Microphone" : "Camera"}: {own?.[field] ? "ON" : "OFF"}
    </button>)}<button disabled={!state.connected || pending} aria-pressed={own?.screen_sharing ?? false}
      onClick={() => { setPending(true); void client.current?.toggle("screen_sharing", !own?.screen_sharing).finally(() => setPending(false)); }}>
      {own?.screen_sharing ? "Dừng chia sẻ màn hình" : "Chia sẻ màn hình"}
    </button><button disabled={!state.connected} onClick={() => void client.current?.startAudio()}>Cho phép phát âm thanh</button></div>
    {state.participants.map(person => <article key={person.identity} aria-label={`Media ${person.name}`}>
      <h4>{person.name}{person.local ? " (Bạn)" : ""}</h4>
      <p>Microphone: {person.microphone_enabled ? "ON" : "OFF"} · Camera: {person.camera_enabled ? "ON" : "OFF"}</p>
      <p>Màn hình: {person.screen_sharing ? "ON" : "OFF"}</p>
      {person.tracks.map(track => <div key={track.sid ?? track.mediaStreamTrack.id} data-media-source={track.source}>
        {track.source === Track.Source.ScreenShare && <h5>Màn hình — {person.name}</h5>}
        {track.source === Track.Source.Camera && <h5>Camera — {person.name}</h5>}
        <MediaTrack track={track} local={person.local} />
      </div>)}
    </article>)}
  </section>;
}
