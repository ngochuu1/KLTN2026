import { Room, RoomEvent, Track, createLocalAudioTrack, createLocalVideoTrack, createLocalScreenTracks, type LocalTrack } from "livekit-client";

export type MediaSnapshot = {
  status: string; connected: boolean;
  participants: { identity: string; name: string; local: boolean; microphone_enabled: boolean; camera_enabled: boolean; screen_sharing: boolean; tracks: Track[] }[];
};
export type MediaCredential = { url: string; token: string; identity: string; room: string };
const sdk = { room: () => new Room(), audio: createLocalAudioTrack, video: createLocalVideoTrack,
  screen: async () => (await createLocalScreenTracks({ audio: false }))[0] };

export function createMedia(
  credential: () => Promise<MediaCredential>,
  receive: (state: MediaSnapshot) => void,
  error: (message: string) => void,
  disconnected: () => void,
  dependencies = sdk,
) {
  const room = dependencies.room();
  let disposed = false;
  let connected = false;
  const pending = new Set<string>();
  const local = new Map<string, LocalTrack>();
  function snapshot(status = connected ? "Đã kết nối media" : "Đang kết nối media…") {
    if (disposed) return;
    receive({ status, connected, participants: [room.localParticipant, ...room.remoteParticipants.values()].map(person => {
      const tracks = [...person.trackPublications.values()].filter(p => p.track && !p.isMuted && p.track.mediaStreamTrack.readyState !== "ended");
      return { identity: person.identity, name: person.name || person.identity, local: person === room.localParticipant,
        microphone_enabled: tracks.some(p => p.source === Track.Source.Microphone),
        camera_enabled: tracks.some(p => p.source === Track.Source.Camera),
        screen_sharing: tracks.some(p => p.source === Track.Source.ScreenShare),
        tracks: tracks.map(p => p.track!),
      };
    }) });
  }
  const update = () => snapshot();
  for (const event of [RoomEvent.TrackSubscribed, RoomEvent.TrackMuted, RoomEvent.TrackUnmuted,
    RoomEvent.LocalTrackPublished, RoomEvent.LocalTrackUnpublished, RoomEvent.ParticipantConnected, RoomEvent.ParticipantDisconnected]) room.on(event, update);
  // LiveKit emits unsubscribe before clearing publication.track and its map entry.
  room.on(RoomEvent.TrackUnsubscribed, () => queueMicrotask(update));
  room.on(RoomEvent.Reconnecting, () => { connected = false; snapshot("Đang kết nối lại media…"); });
  room.on(RoomEvent.Reconnected, () => { connected = true; snapshot(); });
  room.on(RoomEvent.Disconnected, () => { if (!disposed) { close(); disconnected(); } });
  function close() {
    if (disposed) return;
    disposed = true; connected = false;
    for (const track of local.values()) track.stop();
    local.clear(); room.removeAllListeners(); void room.disconnect(true);
  }
  async function connect() {
    snapshot();
    try {
      const grant = await credential();
      if (disposed) return;
      await room.connect(grant.url, grant.token);
      if (disposed) { await room.disconnect(true); return; }
      connected = true; snapshot();
    } catch {
      if (!disposed) { error("Không thể kết nối máy chủ media. Kiểm tra cấu hình hoặc thử tham gia lại."); close(); disconnected(); }
    }
  }
  async function toggle(device: "microphone_enabled" | "camera_enabled" | "screen_sharing", enabled: boolean) {
    if (disposed || (enabled && !connected) || pending.has(device)) return;
    pending.add(device);
    let acquired: LocalTrack | undefined;
    try {
      const existing = local.get(device);
      if (enabled && !existing) {
        acquired = device === "screen_sharing" ? await dependencies.screen() : device === "microphone_enabled" ? await dependencies.audio() : await dependencies.video();
        if (disposed) { acquired.stop(); return; }
        local.set(device, acquired);
        acquired.mediaStreamTrack.addEventListener("ended", () => {
          if (!disposed) void toggle(device, false);
        }, { once: true });
        await room.localParticipant.publishTrack(acquired, { source: device === "screen_sharing" ? Track.Source.ScreenShare : device === "microphone_enabled" ? Track.Source.Microphone : Track.Source.Camera });
        if (disposed) { acquired.stop(); await room.localParticipant.unpublishTrack(acquired, true); return; }
        if (acquired.mediaStreamTrack.readyState === "ended") throw new Error("Device ended while publishing");
      } else if (!enabled && existing) {
        local.delete(device); existing.stop(); await room.localParticipant.unpublishTrack(existing, true);
      }
      error("");
    } catch {
      if (acquired) { acquired.stop(); local.delete(device); await room.localParticipant.unpublishTrack(acquired, true).catch(() => {}); }
      if (!disposed) error(device === "screen_sharing" ? "Không thể chia sẻ màn hình: yêu cầu đã bị hủy/từ chối, trình duyệt không hỗ trợ hoặc kết nối lỗi." : "Không thể sử dụng microphone/camera. Hãy kiểm tra quyền truy cập, thiết bị và kết nối.");
    } finally { pending.delete(device); snapshot(); }
  }
  return { connect, toggle, close, startAudio: () => room.startAudio().catch(() => error("Trình duyệt chưa cho phép phát âm thanh. Hãy thử lại.")) };
}
