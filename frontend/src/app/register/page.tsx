"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { api, ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

export default function RegisterPage() {
  const { login } = useAuth();
  const [form, setForm] = useState({
    organization_name: "",
    slug: "",
    owner_name: "",
    owner_email: "",
    owner_password: "",
  });
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  function set<K extends keyof typeof form>(key: K, value: string) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await api.post("/auth/register-organization", form);
      await login(form.owner_email, form.owner_password, form.slug);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
      setSubmitting(false);
    }
  }

  return (
    <main className="flex-1 flex items-center justify-center p-4">
      <form onSubmit={onSubmit} className="w-full max-w-sm space-y-4 bg-white p-6 rounded-xl shadow-sm border border-neutral-200">
        <h1 className="text-xl font-semibold">Create your organization</h1>

        {error && <p className="text-sm text-red-600" role="alert">{error}</p>}

        <Field label="Organization name" value={form.organization_name} onChange={(v) => set("organization_name", v)} />
        <Field label="Organization slug" value={form.slug} onChange={(v) => set("slug", v)} hint="lowercase-with-hyphens" />
        <Field label="Your name" value={form.owner_name} onChange={(v) => set("owner_name", v)} />
        <Field label="Your email" type="email" value={form.owner_email} onChange={(v) => set("owner_email", v)} />
        <Field
          label="Password"
          type="password"
          value={form.owner_password}
          onChange={(v) => set("owner_password", v)}
          hint="At least 10 characters, with upper, lower, and a number"
        />

        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-lg bg-blue-600 py-2.5 text-white font-medium disabled:opacity-50"
        >
          {submitting ? "Creating…" : "Create organization"}
        </button>

        <p className="text-sm text-neutral-600 text-center">
          Already have an account?{" "}
          <Link href="/login" className="text-blue-600 font-medium">
            Sign in
          </Link>
        </p>
      </form>
    </main>
  );
}

function Field({
  label,
  value,
  onChange,
  type = "text",
  hint,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  type?: string;
  hint?: string;
}) {
  return (
    <label className="block">
      <span className="text-sm font-medium text-neutral-700">{label}</span>
      <input
        type={type}
        required
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="mt-1 w-full rounded-lg border border-neutral-300 px-3 py-2 text-base"
      />
      {hint && <span className="text-xs text-neutral-500">{hint}</span>}
    </label>
  );
}
