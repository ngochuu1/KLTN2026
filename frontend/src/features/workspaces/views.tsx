"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";
import { ApiFailure } from "@/lib/api";
import { Field, Feedback, formValues, value, useSubmission } from "@/components/forms";
import { workspaceServices as api } from "@/features/auth/store";
import { useAuth } from "@/features/auth/provider";
import type { Workspace, WorkspaceInput, WorkspaceMember } from "@/lib/workspace-types";
import { WorkspaceChannels } from "@/features/chat/views";

function useLoad<T>(load: () => Promise<T>) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState("");
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    let active = true;
    load().then(result => { if (active) setData(result); }).catch(failure => {
      if (active) setError(failure instanceof ApiFailure ? failure.message : "Không thể tải dữ liệu.");
    });
    return () => { active = false; };
  }, [load, attempt]);
  return { data, setData, error, retry: () => { setError(""); setData(null); setAttempt(attempt + 1); } };
}
function LoadState({ error, retry }: { error: string; retry: () => void }) {
  return error ? <><p role="alert" className="error">{error}</p><button onClick={retry}>Thử lại</button></> : <p role="status">Đang tải…</p>;
}
function Back() { return <nav><Link href="/workspaces">Danh sách Workspace</Link><Link href="/app">Trang chính</Link></nav>; }
function WorkspaceForm({ workspace, save, cancel }: { workspace?: Workspace; save: (body: WorkspaceInput) => Promise<void>; cancel: () => void }) {
  const submit = useSubmission();
  return <form noValidate onSubmit={event => {
    const data = formValues(event); const name = value(data, "name").trim();
    void submit.run(() => save({ name, description: value(data, "description").trim() || null }), !name || name.length > 120 ? { name: ["Tên phải có 1–120 ký tự."] } : {});
  }}><fieldset disabled={submit.pending}>
    <Field label="Tên Workspace" name="name" required maxLength={120} defaultValue={workspace?.name} errors={submit.fields} />
    <label htmlFor="description">Mô tả</label><textarea id="description" name="description" defaultValue={workspace?.description ?? ""} />
    <div className="actions"><button>{submit.pending ? "Đang lưu…" : workspace ? "Lưu" : "Tạo Workspace"}</button><button type="button" onClick={cancel}>Hủy</button></div>
  </fieldset><Feedback {...submit} /></form>;
}
export function WorkspaceList() {
  const state = useLoad(api.list); const [creating, setCreating] = useState(false); const router = useRouter();
  return <><h1>Workspace của bạn</h1><Back />{!state.data ? <LoadState {...state} /> : state.data.length ? <ul>{state.data.map(workspace => <li key={workspace.id}><Link href={`/workspaces/${workspace.id}`}>{workspace.name}</Link> — {workspace.role}</li>)}</ul> : <p>Bạn chưa tham gia Workspace nào. Tạo Workspace hoặc nhập mã lời mời bên dưới.</p>}
    {creating ? <WorkspaceForm cancel={() => setCreating(false)} save={async body => { const workspace = await api.create(body); router.push(`/workspaces/${workspace.id}`); }} /> : <button onClick={() => setCreating(true)}>Tạo Workspace</button>}
    <form onSubmit={event => { const data = formValues(event); const token = value(data, "token").trim(); if (token) router.push(`/invitations/${encodeURIComponent(token)}`); }}><Field label="Mã lời mời" name="token" required /><button>Xem lời mời</button></form>
  </>;
}
function Invite({ id }: { id: string }) {
  const submit = useSubmission(); const copy = useSubmission(); const [link, setLink] = useState("");
  return <section><h2>Mời thành viên</h2><form onSubmit={event => {
    const data = formValues(event); const userId = value(data, "invitee_user_id").trim(); const expires = value(data, "expires_at");
    void submit.run(async () => { setLink(""); copy.reset(); const result = await api.invite(id, { ...(userId ? { invitee_user_id: userId } : {}), ...(expires ? { expires_at: new Date(expires).toISOString() } : {}) }); setLink(`${window.location.origin}/invitations/${encodeURIComponent(result.token)}`); submit.setSuccess("Đã tạo lời mời."); }, userId && !/^[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}$/i.test(userId) ? { invitee_user_id: ["User ID phải là UUID hợp lệ."] } : {});
  }}><fieldset disabled={submit.pending}><Field label="User ID người nhận (để trống để tạo lời mời chung)" name="invitee_user_id" errors={submit.fields} /><Field label="Hết hạn (không bắt buộc)" name="expires_at" type="datetime-local" errors={submit.fields} /><button>{submit.pending ? "Đang tạo…" : "Tạo lời mời"}</button></fieldset><Feedback {...submit} /></form>
  {link && <><Field label="Liên kết lời mời" name="invitation_link" value={link} readOnly onFocus={event => event.target.select()} /><button disabled={copy.pending} onClick={() => void copy.run(async () => { await navigator.clipboard.writeText(link); copy.setSuccess("Đã sao chép."); })}>Sao chép</button><Feedback {...copy} /></>}</section>;
}
function Members({ workspace, changed }: { workspace: Workspace; changed: () => void }) {
  const [load] = useState(() => () => api.members(workspace.id)); const state = useLoad(load); const submit = useSubmission(); const { user } = useAuth();
  function replace(member: WorkspaceMember) { state.setData(current => current?.map(item => item.user_id === member.user_id ? member : item) ?? null); }
  return <section><h2>Thành viên</h2>{!state.data ? <LoadState {...state} /> : <ul className="members">{state.data.map(member => <li key={member.user_id}><strong>{member.full_name}</strong><p>{member.email}</p><p>Vai trò: {member.role} · Tham gia: {new Date(member.joined_at).toLocaleString("vi-VN")}</p>
    {workspace.role === "OWNER" && member.role !== "OWNER" && <label>Vai trò của {member.full_name}<select aria-label={`Vai trò của ${member.full_name}`} disabled={submit.pending} value={member.role} onChange={event => { const role = event.target.value; if (role === "ADMIN" || role === "MEMBER") void submit.run(async () => { replace(await api.changeRole(workspace.id, member.user_id, role)); submit.setSuccess("Đã đổi vai trò."); }); }}><option value="ADMIN">ADMIN</option><option value="MEMBER">MEMBER</option></select></label>}
    {workspace.role !== "MEMBER" && member.role !== "OWNER" && <button disabled={submit.pending} onClick={() => { if (window.confirm(`Xóa ${member.full_name} khỏi Workspace?`)) void submit.run(async () => { await api.removeMember(workspace.id, member.user_id); state.setData(current => current?.filter(item => item.user_id !== member.user_id) ?? null); if (member.user_id === user?.id) changed(); else submit.setSuccess("Đã xóa thành viên."); }); }}>Xóa thành viên</button>}
  </li>)}</ul>}<Feedback {...submit} /></section>;
}
export function WorkspaceDetail({ id }: { id: string }) {
  const [load] = useState(() => () => api.detail(id)); const state = useLoad(load); const [editing, setEditing] = useState(false); const submit = useSubmission(); const router = useRouter();
  function leavePage() { state.setData(null); router.replace("/workspaces"); }
  if (!state.data) return <><Back /><LoadState {...state} /></>;
  const workspace = state.data;
  return <><Back /><h1>{workspace.name}</h1><p className="description">{workspace.description || "Chưa có mô tả."}</p><p>Vai trò của bạn: <strong>{workspace.role}</strong></p>
    <WorkspaceChannels key={workspace.id} workspace={workspace} />
    {workspace.role !== "MEMBER" && <>{editing ? <WorkspaceForm workspace={workspace} cancel={() => setEditing(false)} save={async body => { state.setData(await api.update(id, body)); setEditing(false); submit.setSuccess("Đã cập nhật Workspace."); }} /> : <button onClick={() => { submit.reset(); setEditing(true); }}>Chỉnh sửa Workspace</button>}<Invite id={id} /></>}
    <Members workspace={workspace} changed={leavePage} /><Feedback {...submit} />
    {workspace.role === "OWNER" ? <><p>OWNER không thể rời Workspace.</p><button disabled={submit.pending} onClick={() => { if (window.confirm(`Xóa Workspace “${workspace.name}”? Tất cả thành viên sẽ mất quyền truy cập.`)) void submit.run(async () => { await api.remove(id); leavePage(); }); }}>Xóa Workspace</button></> : <button disabled={submit.pending} onClick={() => { if (window.confirm(`Rời Workspace “${workspace.name}”?`)) void submit.run(async () => { await api.leave(id); leavePage(); }); }}>Rời Workspace</button>}
  </>;
}
export function InvitationPage({ token }: { token: string }) {
  const [load] = useState(() => () => api.preview(token)); const state = useLoad(load); const submit = useSubmission(); const [declined, setDeclined] = useState(false); const router = useRouter();
  let content: ReactNode;
  if (declined) content = <p role="status">Đã từ chối lời mời. Bạn không được thêm vào Workspace.</p>;
  else if (!state.data) content = <LoadState {...state} />;
  else content = <><h2>{state.data.name}</h2><p>{state.data.description}</p>{state.data.expires_at && <p>Hết hạn: {new Date(state.data.expires_at).toLocaleString("vi-VN")}</p>}<div className="actions"><button disabled={submit.pending} onClick={() => void submit.run(async () => { const workspace = await api.accept(token); router.replace(`/workspaces/${workspace.id}`); })}>Tham gia</button><button disabled={submit.pending} onClick={() => void submit.run(async () => { await api.decline(token); setDeclined(true); })}>Từ chối</button></div>{submit.pending && <p role="status">Đang xử lý…</p>}<Feedback {...submit} /></>;
  return <><h1>Lời mời Workspace</h1>{content}<Back /></>;
}
