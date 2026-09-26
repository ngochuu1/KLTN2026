import type { Metadata } from "next";
import { AuthProvider } from "@/features/auth/provider";
import "./globals.css";
export const metadata: Metadata = { title: "KLTN — Tài khoản", description: "Quản lý tài khoản cá nhân" };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="vi"><body><AuthProvider><main>{children}</main></AuthProvider></body></html>;
}
