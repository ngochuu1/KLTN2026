"use client";
import { useEffect, useSyncExternalStore, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { authStore } from "./store";
export function useAuth() { return useSyncExternalStore(authStore.subscribe, authStore.getSnapshot, authStore.getServerSnapshot); }
export function AuthProvider({ children }: { children: ReactNode }) {
  useEffect(() => { void authStore.restore(); }, []);
  return children;
}
export function AuthGuard({ children, guest = false }: { children: ReactNode; guest?: boolean }) {
  const { authStatus } = useAuth();
  const router = useRouter();
  const redirect = guest ? authStatus === "authenticated" : authStatus === "unauthenticated";
  useEffect(() => { if (redirect) router.replace(guest ? (new URLSearchParams(window.location.search).get("next")?.startsWith("/invitations/") ? new URLSearchParams(window.location.search).get("next")! : "/app") : `/login?next=${encodeURIComponent(window.location.pathname)}`); }, [redirect, guest, router]);
  if (authStatus === "loading" || redirect) return <p role="status">Đang kiểm tra phiên đăng nhập…</p>;
  return children;
}
