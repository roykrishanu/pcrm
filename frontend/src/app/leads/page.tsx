"use client";

import { useEffect, useState, type FormEvent } from "react";
import Link from "next/link";
import { RequireAuth } from "@/components/RequireAuth";
import { api, ApiError } from "@/lib/api";
import type { Lead, Page } from "@/lib/types";

const TEMPERATURE_COLOR: Record<Lead["temperature"], string> = {
  cold: "bg-neutral-200 text-neutral-700",
  warm: "bg-amber-100 text-amber-800",
  hot: "bg-orange-100 text-orange-800",
  very_hot: "bg-red-100 text-red-800",
};

export default function LeadsPage() {
  return (
    <RequireAuth>
      <LeadsContent />
    </RequireAuth>
  );
}

function LeadsContent() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    setLoading(true);
    try {
      const qs = new URLSearchParams({ page: "1", page_size: "50" });
      if (search) qs.set("search", search);
      const data = await api.get<Page<Lead>>(`/leads?${qs}`);
      setLeads(data.items);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load leads.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search]);

  return (
    <div className="flex-1 flex flex-col">
      <header className="sticky top-0 z-10 bg-white border-b border-neutral-200 p-4">
        <div className="flex items-center justify-between gap-3">
          <h1 className="text-lg font-semibold">Leads {total > 0 && <span className="text-neutral-400 font-normal">({total})</span>}</h1>
          <button
            onClick={() => setShowAdd(true)}
            className="rounded-full bg-blue-600 text-white w-10 h-10 flex items-center justify-center text-2xl leading-none shadow-sm"
            aria-label="Add lead"
          >
            +
          </button>
        </div>
        <input
          type="search"
          placeholder="Search name, phone, email…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="mt-3 w-full rounded-lg border border-neutral-300 px-3 py-2 text-base"
        />
      </header>

      <main className="flex-1 p-4 space-y-3">
        {error && <p className="text-sm text-red-600">{error}</p>}
        {loading && <p className="text-sm text-neutral-500">Loading…</p>}
        {!loading && leads.length === 0 && (
          <p className="text-sm text-neutral-500 text-center mt-8">No leads yet. Tap + to add one.</p>
        )}
        {leads.map((lead) => (
          <Link
            key={lead.id}
            href={`/leads/${lead.id}`}
            className="block bg-white rounded-xl border border-neutral-200 p-4 shadow-sm active:bg-neutral-50"
          >
            <div className="flex items-start justify-between gap-2">
              <div>
                <p className="font-medium">{lead.name}</p>
                <p className="text-sm text-neutral-500">{lead.phone ?? lead.email ?? "No contact info"}</p>
              </div>
              <span className={`text-xs font-medium px-2 py-1 rounded-full whitespace-nowrap ${TEMPERATURE_COLOR[lead.temperature]}`}>
                {lead.temperature.replace("_", " ")}
              </span>
            </div>
            <p className="text-xs text-neutral-400 mt-2 capitalize">{lead.status_key.replace(/_/g, " ")}</p>
          </Link>
        ))}
      </main>

      {showAdd && (
        <AddLeadSheet
          onClose={() => setShowAdd(false)}
          onCreated={() => {
            setShowAdd(false);
            refresh();
          }}
        />
      )}
    </div>
  );
}

function AddLeadSheet({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await api.post("/leads", { name, phone: phone || undefined, email: email || undefined });
      onCreated();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to create lead.");
      setSubmitting(false);
    }
  }

  return (
    <div className="fixed inset-0 z-30 bg-black/30 flex items-end md:items-center md:justify-center" onClick={onClose}>
      <form
        onClick={(e) => e.stopPropagation()}
        onSubmit={onSubmit}
        className="w-full md:max-w-sm bg-white rounded-t-2xl md:rounded-2xl p-4 space-y-3"
      >
        <h2 className="text-lg font-semibold">Add lead</h2>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <input
          autoFocus
          required
          placeholder="Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="w-full rounded-lg border border-neutral-300 px-3 py-2 text-base"
        />
        <input
          type="tel"
          placeholder="Phone"
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
          className="w-full rounded-lg border border-neutral-300 px-3 py-2 text-base"
        />
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full rounded-lg border border-neutral-300 px-3 py-2 text-base"
        />
        <div className="flex gap-2 pt-2">
          <button type="button" onClick={onClose} className="flex-1 rounded-lg border border-neutral-300 py-2.5">
            Cancel
          </button>
          <button type="submit" disabled={submitting} className="flex-1 rounded-lg bg-blue-600 text-white py-2.5 disabled:opacity-50">
            {submitting ? "Saving…" : "Save"}
          </button>
        </div>
      </form>
    </div>
  );
}
