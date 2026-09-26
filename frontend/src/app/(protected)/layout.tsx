import { AuthGuard } from "@/features/auth/provider";
export default function Layout({ children }: { children: React.ReactNode }) { return <AuthGuard>{children}</AuthGuard>; }
