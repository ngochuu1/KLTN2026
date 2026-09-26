"use client";
import { useRef, useState, type InputHTMLAttributes, type FormEvent } from "react";
import { ApiFailure } from "@/lib/api";
export type Fields = Record<string, string[]>;
const messages: Record<string, string> = {
  INVALID_CREDENTIALS: "Email hoặc mật khẩu không chính xác",
  ACCOUNT_LOCKED: "Tài khoản đang bị khóa.",
  EMAIL_ALREADY_EXISTS: "Email đã được sử dụng.",
  CURRENT_PASSWORD_INCORRECT: "Mật khẩu hiện tại không chính xác.",
  NEW_PASSWORD_SAME_AS_CURRENT: "Mật khẩu mới phải khác mật khẩu hiện tại.",
  PASSWORD_CONFIRMATION_MISMATCH: "Xác nhận mật khẩu không khớp.",
};
const businessFields: Record<string, string> = { EMAIL_ALREADY_EXISTS: "email", CURRENT_PASSWORD_INCORRECT: "current_password", NEW_PASSWORD_SAME_AS_CURRENT: "new_password", PASSWORD_CONFIRMATION_MISMATCH: "confirm_new_password" };
export function useSubmission() {
  const lock = useRef(false);
  const [pending, setPending] = useState(false);
  const [fields, setFields] = useState<Fields>({});
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  function reset() { setFields({}); setError(""); setSuccess(""); }
  async function run(action: () => Promise<void>, validation: Fields = {}) {
    if (lock.current) return;
    reset(); setFields(validation);
    if (Object.keys(validation).length) return;
    lock.current = true; setPending(true);
    try { await action(); }
    catch (failure) {
      if (failure instanceof ApiFailure) {
        const message = messages[failure.error.code] ?? failure.error.message;
        const field = businessFields[failure.error.code];
        setFields({ ...(field ? { [field]: [message] } : {}), ...failure.error.fields });
        setError(message);
      } else setError("Có lỗi xảy ra. Vui lòng thử lại.");
    } finally { lock.current = false; setPending(false); }
  }
  return { pending, fields, error, success, setSuccess, reset, run };
}
export function Field({ label, name, errors, ...props }: InputHTMLAttributes<HTMLInputElement> & { label: string; name: string; errors?: Fields }) {
  const messages = errors?.[name];
  return <div className="field"><label htmlFor={name}>{label}</label><input {...props} name={name} id={name} aria-invalid={!!messages} aria-describedby={messages ? `${name}-error` : undefined} />{messages && <p className="error" id={`${name}-error`}>{messages.join(" ")}</p>}</div>;
}
export function Feedback({ error, success }: { error: string; success: string }) {
  return <>{error && <p className="error" role="alert">{error}</p>}{success && <p className="success" role="status">{success}</p>}</>;
}
export function formValues(event: FormEvent<HTMLFormElement>) { event.preventDefault(); return new FormData(event.currentTarget); }
export function value(data: FormData, name: string) { return String(data.get(name) ?? ""); }
export function validate(data: Record<string, string>, passwords: string[] = [], confirmation?: [string, string]): Fields {
  const errors: Fields = {};
  for (const [key, value] of Object.entries(data)) {
    if (!(key.includes("password") ? value : value.trim())) errors[key] = ["Vui lòng nhập trường này."];
    else if (key === "email" && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim())) errors[key] = ["Email không hợp lệ."];
    else if (key === "full_name" && value.trim().length > 100) errors[key] = ["Họ tên tối đa 100 ký tự."];
    else if (passwords.includes(key) && (value.length < 8 || value.length > 128)) errors[key] = ["Mật khẩu phải có 8–128 ký tự."];
    else if (key.includes("password") && value.length > 128) errors[key] = ["Mật khẩu tối đa 128 ký tự."];
  }
  if (confirmation && data[confirmation[0]] !== data[confirmation[1]]) errors[confirmation[1]] = ["Xác nhận mật khẩu không khớp."];
  return errors;
}
