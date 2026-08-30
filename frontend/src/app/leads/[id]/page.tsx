"use client";

import { useEffect, useState, type FormEvent } from "react";
import { useParams, useRouter } from "next/navigation";
import { RequireAuth } from "@/components/RequireAuth";
import { api, ApiError } from "@/lib/api";
import type { Lead, LeadActivity } from "@/lib/types";

const STATUS_OPTIONS = [
  "new", "contacted", "qualified", "property_suggested", "interested",
  "site_visit_scheduled", "site_visit_completed", "negotiation", "booking",
  "won", "lost", "nurture",
];

export default function LeadDetailPage() {
  return (
    <RequireAuth>
      <LeadDetailContent />
    </RequireAuth>
  );
}

function LeadDetailContent() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [lead, setLead] = useState<Lead | null>(null);
  const [activities, setActivities] = useState<LeadActivity[]>([]);
  const [note, setNote] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);

  async function refresh() {
    try {
      const [leadData, activityData] = await Promise.all([
        api.get<Lead>(`/leads/${id}`),
        api.get<LeadActivity[]>(`/leads/${id}/activities`),
      ]);
      setLead(leadData);
      setActivities(activityData);
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) setNotFound(true);
      else setError(err instanceof ApiError ? err.message : "Failed to load lead.");
    }
  }

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  async function changeStatus(status_key: string) {
    try {
      const updated = await api.post<Lead>(`/leads/${id}/status`, { status_key });
      setLead(updated);
      refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to update status.");
    }
  }

  async function addNote(e: FormEvent) {
    e.preventDefault();
    if (!note.trim()) return;
    try {
      await api.post(`/leads/${id}/activities`, { type: "note", payload: { text: note } });
      setNote("");
      refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to add note.");
    }
  }

  if (notFound) {
    return (
      <div className="p-4">
        <p className="text-neutral-500">Lead not found.</p>
        <button onClick={() => router.push("/leads")} className="text-blue-600 mt-2">
          Back to leads
        </button>
      </div>
    );
  }

  if (!lead) return <div className="p-4 text-neutral-500">Loading…</div>;

  return (
    <div className="flex-1 flex flex-col">
      <header className="sticky top-0 z-10 bg-white border-b border-neutral-200 p-4">
        <button onClick={() => router.push("/leads")} className="text-sm text-blue-600 mb-2">
          ← Leads
        </button>
        <h1 className="text-lg font-semibold">{lead.name}</h1>
        <p className="text-sm text-neutral-500">{lead.phone ?? lead.email ?? "No contact info"}</p>
      </header>

      <main className="flex-1 p-4 space-y-4">
        {error && <p className="text-sm text-red-600">{error}</p>}

        {/* Quick actions — what to do next (section 74) */}
        <div className="grid grid-cols-3 gap-2">
          <QuickAction href={lead.phone ? `tel:${lead.phone}` : undefined} label="Call" />
          <QuickAction
            href={lead.whatsapp_number ? `https://wa.me/${lead.whatsapp_number.replace(/\D/g, "")}` : undefined}
            label="WhatsApp"
          />
          <QuickAction href={lead.email ? `mailto:${lead.email}` : undefined} label="Email" />
        </div>

        <label className="block">
          <span className="text-sm font-medium text-neutral-700">Status</span>
          <select
            value={lead.status_key}
            onChange={(e) => changeStatus(e.target.value)}
            className="mt-1 w-full rounded-lg border border-neutral-300 px-3 py-2 text-base capitalize"
          >
            {STATUS_OPTIONS.map((s) => (
              <option key={s} value={s}>
                {s.replace(/_/g, " ")}
              </option>
            ))}
          </select>
        </label>

        <div className="grid grid-cols-2 gap-3 text-sm">
          <Info label="Score" value={String(lead.score)} />
          <Info label="Temperature" value={lead.temperature.replace("_", " ")} />
          <Info label="Source" value={lead.source ?? "—"} />
          <Info label="Budget" value={lead.budget_min || lead.budget_max ? `${lead.budget_min ?? "?"} – ${lead.budget_max ?? "?"}` : "—"} />
        </div>

        <section>
          <h2 className="text-sm font-semibold text-neutral-700 mb-2">Timeline</h2>
          <form onSubmit={addNote} className="flex gap-2 mb-3">
            <input
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="Add a note…"
              className="flex-1 rounded-lg border border-neutral-300 px-3 py-2 text-base"
            />
            <button type="submit" className="rounded-lg bg-blue-600 text-white px-4">
              Add
            </button>
          </form>
          <ul className="space-y-2">
            {activities.map((a) => (
              <li key={a.id} className="bg-white border border-neutral-200 rounded-lg p-3 text-sm">
                <p className="font-medium capitalize">{a.type.replace(/_/g, " ")}</p>
                {a.payload && <p className="text-neutral-500 mt-1">{JSON.stringify(a.payload)}</p>}
                <p className="text-xs text-neutral-400 mt-1">{new Date(a.created_at).toLocaleString()}</p>
              </li>
            ))}
          </ul>
        </section>
      </main>
    </div>
  );
}

function QuickAction({ href, label }: { href?: string; label: string }) {
  if (!href) {
    return (
      <span className="text-center text-sm rounded-lg border border-neutral-200 py-3 text-neutral-300">{label}</span>
    );
  }
  return (
    <a href={href} className="text-center text-sm rounded-lg border border-neutral-300 py-3 font-medium text-blue-600">
      {label}
    </a>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-white border border-neutral-200 rounded-lg p-3">
      <p className="text-xs text-neutral-400">{label}</p>
      <p className="font-medium capitalize">{value}</p>
    </div>
  );
}
