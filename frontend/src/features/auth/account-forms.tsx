"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Field, Feedback, formValues, value, validate, useSubmission } from "@/components/forms";
import { authStore, services } from "./store";
import { useAuth } from "./provider";
import type { UserProfile } from "@/lib/types";
export function RegisterForm() {
  const submit = useSubmission(); const router = useRouter();
  return <><h1>Đăng ký tài khoản</h1><form noValidate onSubmit={event => {
    const data = formValues(event);
    const body = { full_name: value(data, "full_name").trim(), email: value(data, "email").trim(), password: value(data, "password"), confirm_password: value(data, "confirm_password") };
    void submit.run(async () => { await services.register(body); router.replace("/login?registered=1"); }, validate(body, ["password"], ["password", "confirm_password"]));
  }}><fieldset disabled={submit.pending}>
    <Field label="Họ tên" name="full_name" autoComplete="name" required maxLength={100} errors={submit.fields} />
    <Field label="Email" name="email" type="email" autoComplete="email" required maxLength={254} errors={submit.fields} />
    <Field label="Mật khẩu" name="password" type="password" autoComplete="new-password" required errors={submit.fields} />
    <Field label="Xác nhận mật khẩu" name="confirm_password" type="password" autoComplete="new-password" required errors={submit.fields} />
    <button disabled={submit.pending}>{submit.pending ? "Đang đăng ký…" : "Đăng ký"}</button>
  </fieldset><Feedback {...submit} /></form><p>Đã có tài khoản? <Link href="/login">Đăng nhập</Link></p></>;
}
export function LoginForm({ registered }: { registered: boolean }) {
  const submit = useSubmission(); const router = useRouter();
  return <><h1>Đăng nhập</h1>{registered && <p role="status">Đăng ký thành công. Vui lòng đăng nhập.</p>}<form noValidate onSubmit={event => {
    const data = formValues(event); const body = { email: value(data, "email").trim(), password: value(data, "password") };
    void submit.run(async () => { await authStore.login(body); const next = new URLSearchParams(window.location.search).get("next"); router.replace(next?.startsWith("/invitations/") ? next : "/app"); }, validate(body));
  }}><fieldset disabled={submit.pending}>
    <Field label="Email" name="email" type="email" autoComplete="username" required errors={submit.fields} />
    <Field label="Mật khẩu" name="password" type="password" autoComplete="current-password" required errors={submit.fields} />
    <button disabled={submit.pending}>{submit.pending ? "Đang đăng nhập…" : "Đăng nhập"}</button>
  </fieldset><Feedback {...submit} /></form><p><Link href="/register">Đăng ký tài khoản</Link></p></>;
}
export function Landing() {
  const { user } = useAuth(); const submit = useSubmission(); const router = useRouter();
  return <><h1>Xin chào, {user?.full_name}</h1><p>Bạn đã đăng nhập.</p><nav><Link href="/workspaces">Workspace</Link><Link href="/profile">Thông tin cá nhân</Link><Link href="/settings/security">Đổi mật khẩu</Link></nav>
    <button disabled={submit.pending} onClick={() => void submit.run(async () => { await authStore.logout(); router.replace("/login"); })}>{submit.pending ? "Đang đăng xuất…" : "Đăng xuất"}</button><Feedback {...submit} /></>;
}
export function ProfileForm() {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loadError, setLoadError] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const [editing, setEditing] = useState(false);
  const submit = useSubmission();
  useEffect(() => {
    let active = true;
    services.me().then(user => { if (active) { setProfile(user); authStore.setUser(user); } }).catch(() => { if (active) setLoadError(true); });
    return () => { active = false; };
  }, [attempt]);
  if (loadError) return <><p role="alert">Không thể tải thông tin cá nhân.</p><button onClick={() => { setLoadError(false); setAttempt(attempt + 1); }}>Thử lại</button></>;
  if (!profile) return <p role="status">Đang tải thông tin cá nhân…</p>;
  return <><h1>Thông tin cá nhân</h1><form key={`${editing}-${profile.updated_at}`} noValidate onSubmit={event => {
    const data = formValues(event); if (!editing) return;
    const body = { full_name: value(data, "full_name").trim() };
    void submit.run(async () => { const user = await services.update(body); setProfile(user); authStore.setUser(user); setEditing(false); submit.setSuccess("Đã cập nhật thông tin cá nhân."); }, validate(body));
  }}><fieldset disabled={submit.pending}>
    <Field label="Họ tên" name="full_name" defaultValue={profile.full_name} readOnly={!editing} required maxLength={100} errors={submit.fields} />
    <Field label="Email" name="email" type="email" value={profile.email} readOnly />
    {editing ? <div className="actions"><button disabled={submit.pending}>{submit.pending ? "Đang lưu…" : "Lưu"}</button><button type="button" disabled={submit.pending} onClick={() => { setEditing(false); submit.reset(); }}>Hủy</button></div> : <button type="button" onClick={() => { submit.reset(); setEditing(true); }}>Chỉnh sửa</button>}
  </fieldset><Feedback {...submit} /></form><Link href="/app">Về trang chính</Link></>;
}
export function PasswordForm() {
  const submit = useSubmission();
  return <><h1>Đổi mật khẩu</h1><form noValidate onSubmit={event => {
    const form = event.currentTarget; const data = formValues(event);
    const body = { current_password: value(data, "current_password"), new_password: value(data, "new_password"), confirm_new_password: value(data, "confirm_new_password") };
    void submit.run(async () => { await services.changePassword(body); form.reset(); submit.setSuccess("Đổi mật khẩu thành công. Phiên hiện tại được giữ nguyên."); }, validate(body, ["new_password"], ["new_password", "confirm_new_password"]));
  }}><fieldset disabled={submit.pending}>
    <Field label="Mật khẩu hiện tại" name="current_password" type="password" autoComplete="current-password" required errors={submit.fields} />
    <Field label="Mật khẩu mới" name="new_password" type="password" autoComplete="new-password" required errors={submit.fields} />
    <Field label="Xác nhận mật khẩu mới" name="confirm_new_password" type="password" autoComplete="new-password" required errors={submit.fields} />
    <button disabled={submit.pending}>{submit.pending ? "Đang đổi mật khẩu…" : "Đổi mật khẩu"}</button>
  </fieldset><Feedback {...submit} /></form><Link href="/app">Về trang chính</Link></>;
}
