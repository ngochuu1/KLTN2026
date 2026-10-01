"use client";
import { createWorkspaceServices } from "@/lib/workspace-services";
import { createChatServices } from "@/lib/chat-services";
import { createServices } from "@/lib/services";
import type { LoginRequest, User } from "@/lib/types";
type AuthState = { user: User | null; accessToken: string | null; authStatus: "loading" | "authenticated" | "unauthenticated" };
const initial: AuthState = { user: null, accessToken: null, authStatus: "loading" };
let state = initial;
const listeners = new Set<() => void>();
function set(next: AuthState) { state = next; listeners.forEach(listener => listener()); }
let refreshFlight: Promise<string> | null = null;
let restoreFlight: Promise<void> | null = null;
let revision = 0;
export function clearAuth() { revision++; set({ user: null, accessToken: null, authStatus: "unauthenticated" }); }
async function refresh(): Promise<string> {
  if (!refreshFlight) {
    const started = revision;
    refreshFlight = services.refresh().then(result => {
      if (started !== revision) throw new Error("Authentication changed");
      set({ ...state, accessToken: result.access_token });
      return result.access_token;
    }).finally(() => { refreshFlight = null; });
  }
  return refreshFlight;
}
export const services = createServices({ getToken: () => state.accessToken, refresh, clear: clearAuth });
export const workspaceServices = createWorkspaceServices({ getToken: () => state.accessToken, refresh, clear: clearAuth });
export const chatServices = createChatServices({ getToken: () => state.accessToken, refresh, clear: clearAuth });
export const chatAuth = { getToken: () => state.accessToken, refresh };
export const authStore = {
  subscribe(listener: () => void) { listeners.add(listener); return () => { listeners.delete(listener); }; },
  getSnapshot: () => state,
  getServerSnapshot: () => initial,
  restore() {
    if (!restoreFlight) restoreFlight = (async () => {
      try { await refresh(); const user = await services.me(); set({ ...state, user, authStatus: "authenticated" }); }
      catch { clearAuth(); }
    })();
    return restoreFlight;
  },
  async login(body: LoginRequest) {
    const result = await services.login(body);
    revision++;
    set({ user: result.user, accessToken: result.access_token, authStatus: "authenticated" });
  },
  setUser(user: User) { if (state.authStatus === "authenticated") set({ ...state, user }); },
  async logout() { await services.logout(); clearAuth(); },
};
