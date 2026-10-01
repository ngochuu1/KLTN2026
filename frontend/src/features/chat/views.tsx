"use client";
import { useEffect, useRef, useState } from "react";
import { Field, Feedback, formValues, useSubmission, value } from "@/components/forms";
import { chatServices as api } from "@/features/auth/store";
import { useAuth } from "@/features/auth/provider";
import type { Channel, ChannelInput, Message } from "@/lib/chat-types";
import type { Workspace } from "@/lib/workspace-types";
import { useChat } from "./use-chat";
import { validateFile } from "./state";
import { StudyRoom } from "@/features/study-room/views";

function ChannelForm({ channel, save, cancel }: { channel?: Channel; save: (body: ChannelInput) => Promise<void>; cancel: () => void }) {
  const submit = useSubmission();
  return <form onSubmit={event => {
    const data = formValues(event); const name = value(data, "name").trim();
    void submit.run(() => save({ name, description: value(data, "description").trim() || null, type: channel?.type ?? (value(data, "type") === "STUDY_ROOM" ? "STUDY_ROOM" : "TEXT") }), !name || name.length > 100 ? { name: ["Tên Channel phải có 1–100 ký tự."] } : {});
  }}><fieldset disabled={submit.pending}>
    <Field name="name" label="Tên Channel" defaultValue={channel?.name} maxLength={100} required errors={submit.fields} />
    <label htmlFor="channel-description">Mô tả Channel</label><textarea id="channel-description" name="description" defaultValue={channel?.description ?? ""} />
    {!channel && <><label htmlFor="channel-type">Loại Channel</label><select id="channel-type" name="type"><option value="TEXT">TEXT — Chat</option><option value="STUDY_ROOM">STUDY_ROOM — Phòng học</option></select></>}
    <div className="actions"><button>{submit.pending ? "Đang lưu…" : "Lưu Channel"}</button><button type="button" onClick={cancel}>Hủy</button></div>
  </fieldset><Feedback {...submit} /></form>;
}

export function WorkspaceChannels({ workspace }: { workspace: Workspace }) {
  const [channels, setChannels] = useState<Channel[] | null>(null);
  const [selected, setSelected] = useState("");
  const [error, setError] = useState("");
  const [attempt, setAttempt] = useState(0);
  const [form, setForm] = useState<"create" | "edit" | null>(null);
  const submit = useSubmission();
  const manager = workspace.role !== "MEMBER";
  useEffect(() => {
    let active = true;
    api.channels(workspace.id).then(result => {
      if (!active) return;
      setChannels(result); setSelected(current => result.some(c => c.id === current) ? current : (result.find(c => c.is_default) ?? result[0])?.id ?? "");
    }).catch(failure => { if (active) setError(failure instanceof Error ? failure.message : "Không thể tải Channel."); });
    return () => { active = false; };
  }, [workspace.id, attempt]);
  const channel = channels?.find(c => c.id === selected);
  return <section className="workspace-chat" aria-label="Channel và Chat">
    <aside className="channel-sidebar"><h2>Channels</h2>
      {error && <><p role="alert" className="error">{error}</p><button onClick={() => { setError(""); setAttempt(a => a + 1); }}>Tải lại Channel</button></>}
      {!channels && !error && <p role="status">Đang tải Channel…</p>}
      {channels?.length === 0 && <p>Workspace chưa có Channel.</p>}
      <nav aria-label="Danh sách Channel">{channels?.map(item => <button key={item.id} aria-current={selected === item.id ? "page" : undefined} onClick={() => { setSelected(item.id); setForm(null); submit.reset(); }}><span>{item.type === "TEXT" ? "#" : "◇"} {item.name}</span><small>{item.type}</small></button>)}</nav>
      {manager && <button onClick={() => { setForm("create"); submit.reset(); }}>Tạo Channel</button>}
    </aside>
    <div className="channel-main"><Feedback {...submit} />
      {form === "create" && manager && <ChannelForm cancel={() => setForm(null)} save={async body => {
        const created = await api.createChannel(workspace.id, body); setChannels(current => [...(current ?? []), created]); setSelected(created.id); setForm(null); submit.setSuccess("Đã tạo Channel.");
      }} />}
      {channel ? <><header className="channel-header"><h2>{channel.type === "TEXT" ? "#" : "◇"} {channel.name}</h2><p className="description">{channel.description}</p>
        {manager && <div className="actions"><button onClick={() => setForm("edit")}>Sửa Channel</button>{!channel.is_default && <button disabled={submit.pending} onClick={() => {
          if (window.confirm(`Xóa Channel “${channel.name}” và dữ liệu liên quan?`)) void submit.run(async () => {
            await api.deleteChannel(channel.id); const remaining = (channels ?? []).filter(c => c.id !== channel.id); setChannels(remaining); setSelected((remaining.find(c => c.is_default) ?? remaining[0])?.id ?? ""); setForm(null); submit.setSuccess("Đã xóa Channel.");
          });
        }}>Xóa Channel</button>}</div>}
      </header>
        {form === "edit" && manager && <ChannelForm key={`edit-${channel.id}`} channel={channel} cancel={() => setForm(null)} save={async ({ name, description }) => {
          const updated = await api.updateChannel(channel.id, { name, description }); setChannels(current => current?.map(c => c.id === updated.id ? updated : c) ?? []); setForm(null); submit.setSuccess("Đã cập nhật Channel.");
        }} />}
        {channel.type === "TEXT" ? <ChatPanel key={channel.id} channel={channel} /> : <StudyRoom key={channel.id} channel={channel} />}
      </> : channels && <p>Chọn một Channel để bắt đầu.</p>}
    </div>
  </section>;
}

function MessageItem({ message, chat }: { message: Message; chat: ReturnType<typeof useChat> }) {
  const { user } = useAuth(); const submit = useSubmission();
  const [editing, setEditing] = useState(false);
  const own = message.sender.id === user?.id;
  return <li className="chat-message" data-message-id={message.id}>
    <div className="message-meta"><strong>{message.sender.full_name}</strong><time dateTime={message.created_at}>{new Date(message.created_at).toLocaleString("vi-VN")}</time>{message.edited_at && <small>Đã chỉnh sửa</small>}</div>
    {editing ? <form onSubmit={event => { const content = value(formValues(event), "content").trim(); void submit.run(async () => { chat.saved(await api.edit(message.id, content)); setEditing(false); }, content ? {} : { content: ["Nội dung không được để trống."] }); }}>
      <label htmlFor={`edit-${message.id}`}>Sửa tin nhắn</label><textarea id={`edit-${message.id}`} name="content" defaultValue={message.content ?? ""} disabled={submit.pending} required />
      {submit.fields.content && <p role="alert" className="error">{submit.fields.content.join(" ")}</p>}
      <div className="actions"><button disabled={submit.pending}>Lưu tin nhắn</button><button type="button" onClick={() => setEditing(false)}>Hủy</button></div>
    </form> : message.content && <p className="description">{message.content}</p>}
    {message.attachments.map(file => <button className="attachment" key={file.id} disabled={submit.pending} onClick={() => void submit.run(async () => {
      const blob = await api.download(file.id); const url = URL.createObjectURL(blob); const link = document.createElement("a"); link.href = url; link.download = file.original_filename; link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
    })}>Tải {file.original_filename} ({Math.ceil(file.size_bytes / 1024)} KB)</button>)}
    <div className="reactions" aria-label="Cảm xúc">{message.reactions.map(reaction => <span key={reaction.emoji}>{reaction.emoji} {reaction.count}</span>)}</div>
    <details><summary>Thêm / gỡ cảm xúc</summary><div className="actions">{[...new Set(["👍", "❤️", "🎉", ...message.reactions.map(r => r.emoji)])].map(emoji => <div key={emoji} className="reaction-actions">
      <button aria-label={`Thêm ${emoji}`} disabled={submit.pending} onClick={() => void submit.run(() => chat.react(message.id, emoji))}>{emoji} +</button>
      <button aria-label={`Gỡ ${emoji} của tôi`} disabled={submit.pending} onClick={() => void submit.run(() => chat.react(message.id, emoji, true))}>{emoji} −</button>
    </div>)}</div><small>Gỡ chỉ áp dụng cho cảm xúc của bạn.</small></details>
    {own && !editing && <div className="actions message-actions"><button onClick={() => { submit.reset(); setEditing(true); }}>Sửa tin nhắn</button><button disabled={submit.pending} onClick={() => {
      if (window.confirm("Xóa tin nhắn này?")) void submit.run(async () => { await api.remove(message.id); chat.receive({ type: "message.deleted", data: { message_id: message.id } }); });
    }}>Xóa tin nhắn</button></div>}
    {submit.pending && <p role="status">Đang xử lý…</p>}<Feedback {...submit} />
  </li>;
}

function ChatPanel({ channel }: { channel: Channel }) {
  const chat = useChat(channel.id); const submit = useSubmission();
  const [content, setContent] = useState(""); const [file, setFile] = useState<File | null>(null); const [fileError, setFileError] = useState("");
  const fileInput = useRef<HTMLInputElement>(null);
  return <div className="chat-panel"><p className="connection-status" role="status">{chat.connection}</p>
    {chat.error && <p role="alert" className="error">{chat.error}</p>}
    <div className="actions"><button disabled={chat.loading} onClick={() => void chat.load()}>Tải lại tin nhắn</button>{chat.more && <button disabled={chat.loading} onClick={() => void chat.load(true)}>Tin nhắn cũ hơn</button>}</div>
    {chat.loading && <p role="status">Đang tải tin nhắn…</p>}
    {!chat.loading && !chat.error && !chat.messages.length && <p>Chưa có tin nhắn. Hãy bắt đầu cuộc trò chuyện.</p>}
    <ol className="message-list" aria-label="Tin nhắn">{chat.messages.map(message => <MessageItem key={message.id} message={message} chat={chat} />)}</ol>
    <form className="message-composer" onSubmit={event => {
      event.preventDefault();
      if ((!content.trim() && !file) || fileError) return;
      void submit.run(async () => { const sent = file ? await api.upload(channel.id, file, content) : await api.send(channel.id, content.trim()); chat.saved(sent); setContent(""); setFile(null); if (fileInput.current) fileInput.current.value = ""; });
    }}><fieldset disabled={submit.pending}>
      <label htmlFor="message-content">Nhắn vào #{channel.name}</label><textarea id="message-content" value={content} onChange={event => setContent(event.target.value)} placeholder="Viết tin nhắn…" />
      <label htmlFor="message-file">Đính kèm tệp (tối đa 25 MB)</label><input ref={fileInput} id="message-file" type="file" accept=".pdf,.doc,.docx,.txt,.png,.jpg,.jpeg" onChange={event => {
        const selected = event.target.files?.[0] ?? null; setFile(selected); setFileError(selected ? validateFile(selected) : "");
      }} />
      {file && <p>{file.name} <button type="button" onClick={() => { setFile(null); setFileError(""); if (fileInput.current) fileInput.current.value = ""; }}>Bỏ tệp</button></p>}
      {fileError && <p role="alert" className="error">{fileError}</p>}
      <button disabled={submit.pending || !!fileError || (!content.trim() && !file)}>{submit.pending ? file ? "Đang tải tệp…" : "Đang gửi…" : "Gửi tin nhắn"}</button>
    </fieldset><Feedback {...submit} /></form>
  </div>;
}
