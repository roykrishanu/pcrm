"use client";

import { RequireAuth } from "@/components/RequireAuth";
import { useAuth } from "@/lib/auth-context";

export default function AccountPage() {
  return (
    <RequireAuth>
      <AccountContent />
    </RequireAuth>
  );
}

function AccountContent() {
  const { user, logout } = useAuth();
  if (!user) return null;

  return (
    <div className="flex-1 p-4 space-y-4">
      <h1 className="text-lg font-semibold">Account</h1>
      <div className="bg-white border border-neutral-200 rounded-xl p-4 space-y-1">
        <p className="font-medium">{user.name}</p>
        <p className="text-sm text-neutral-500">{user.email}</p>
        <p className="text-sm text-neutral-500">{user.role_name ?? "No role assigned"}</p>
        {!user.is_email_verified && (
          <p className="text-xs text-amber-600 mt-2">Email not verified yet — check your inbox.</p>
        )}
      </div>
      <button onClick={logout} className="w-full rounded-lg border border-red-200 text-red-600 py-2.5 font-medium">
        Sign out
      </button>
    </div>
  );
}
