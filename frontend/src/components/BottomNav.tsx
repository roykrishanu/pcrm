"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

// Mobile bottom nav (spec section 6). Only lists sections that actually
// exist — Properties/Visits tabs are NOT here yet because those features
// aren't built (section 85: no fake buttons that go nowhere).
const ITEMS = [
  { href: "/leads", label: "Leads" },
  { href: "/account", label: "Account" },
];

export function BottomNav() {
  const pathname = usePathname();
  return (
    <nav className="md:hidden fixed bottom-0 inset-x-0 z-20 border-t border-neutral-200 bg-white">
      <ul className="flex">
        {ITEMS.map((item) => {
          const active = pathname?.startsWith(item.href);
          return (
            <li key={item.href} className="flex-1">
              <Link
                href={item.href}
                className={`flex flex-col items-center py-3 text-xs font-medium ${
                  active ? "text-blue-600" : "text-neutral-500"
                }`}
              >
                {item.label}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
