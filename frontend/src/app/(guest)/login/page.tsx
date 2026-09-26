import { LoginForm } from "@/features/auth/account-forms";
export default async function Page({ searchParams }: { searchParams: Promise<{ registered?: string }> }) { return <LoginForm registered={(await searchParams).registered === "1"} />; }
