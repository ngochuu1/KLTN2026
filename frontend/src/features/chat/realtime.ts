import type { ChatEvent } from "../../lib/chat-types";
export function connectChat(channel: string, auth: { getToken: () => string | null; refresh: () => Promise<string> }, receive: (event: ChatEvent) => void, status: (text: string) => void, resync: () => void) {
  let disposed = false;
  let socket: WebSocket | undefined;
  let timer: ReturnType<typeof setTimeout> | undefined;
  let attempts = 0;
  let authRetried = false;
  function connect() {
    if (disposed) return;
    const base = process.env.NEXT_PUBLIC_API_BASE_URL;
    if (!base) { status("Chưa cấu hình realtime."); return; }
    try {
      const url = new URL(`${base.replace(/\/$/, "")}/api/v1/ws/channels/${channel}`);
      url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
      status(attempts ? "Đang kết nối lại…" : "Đang kết nối…");
      const ws = new WebSocket(url); socket = ws;
      ws.onopen = () => {
        if (disposed) return;
        ws.send(JSON.stringify({ type: "auth", access_token: auth.getToken() }));
        status("Đã kết nối"); attempts = 0; resync();
      };
      ws.onmessage = event => {
        if (disposed) return;
        try {
          const message = JSON.parse(event.data) as ChatEvent;
          if (["message.created", "message.updated", "message.deleted", "reaction.updated"].includes(message.type) && message.data) receive(message);
        } catch { /* Ignore malformed frames; REST history remains available. */ }
      };
      ws.onerror = () => { if (!disposed) status("Mất kết nối realtime."); };
      ws.onclose = async event => {
        if (disposed) return;
        if ([4403, 4404, 1008].includes(event.code)) { status("Không thể truy cập realtime của Channel."); return; }
        if (event.code === 4401) {
          if (authRetried) { status("Phiên realtime không hợp lệ. Vui lòng đăng nhập lại."); return; }
          authRetried = true;
          try { await auth.refresh(); } catch { if (!disposed) status("Phiên đăng nhập đã hết hạn."); return; }
        }
        if (disposed) return;
        status("Mất kết nối · đang thử lại…");
        timer = setTimeout(connect, Math.min(1000 * 2 ** attempts++, 15000));
      };
    } catch { status("Không thể kết nối realtime."); }
  }
  connect();
  return () => { disposed = true; clearTimeout(timer); if (socket) { socket.onclose = null; socket.close(); } };
}
