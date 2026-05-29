"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard, FileText, Search, BarChart3,
  Activity, Settings, LogOut, ChevronRight,
} from "lucide-react";
import { useAuthStore } from "@/store/auth";
import { logout } from "@/lib/auth";
import { useRouter } from "next/navigation";

const NAV_ITEMS = [
  { label: "Dashboard",  href: "/dashboard",           icon: LayoutDashboard },
  { label: "Reports",    href: "/dashboard/reports",   icon: FileText },
  { label: "Search",     href: "/dashboard/search",    icon: Search },
  { label: "Analytics",  href: "/dashboard/analytics", icon: BarChart3 },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user, clearAuth } = useAuthStore();
  const router = useRouter();

  const handleLogout = async () => {
    await logout();
    clearAuth();
    router.push("/login");
  };

  return (
    <aside className="fixed left-0 top-0 h-screen w-60 flex flex-col z-30"
      style={{ backgroundColor: "var(--bg-surface)", borderRight: "1px solid var(--border-color)" }}>

      {/* Logo */}
      <div className="h-16 flex items-center px-5 gap-2.5"
        style={{ borderBottom: "1px solid var(--border-subtle)" }}>
        <div className="w-7 h-7 rounded-lg flex items-center justify-center" style={{ backgroundColor: "#0F766E" }}>
          <Activity size={14} className="text-white" />
        </div>
        <div>
          <span className="text-sm font-bold text-text-primary tracking-wide">RadSight</span>
          <span className="block text-[10px] text-text-muted font-mono">v1.0 · AI Platform</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-0.5">
        <p className="text-[10px] uppercase tracking-widest text-text-muted px-2 mb-2">Navigation</p>
        {NAV_ITEMS.map(({ label, href, icon: Icon }) => {
          const active = pathname === href || (href !== "/dashboard" && pathname.startsWith(href));
          return (
            <Link key={href} href={href}
              className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all group",
                active
                  ? "bg-accent-blue/10 text-accent-blue"
                  : "text-text-secondary hover:text-text-primary hover:bg-surface"
              )}>
              <Icon size={15} />
              <span className="flex-1">{label}</span>
              {active && <ChevronRight size={12} className="opacity-60" />}
            </Link>
          );
        })}
      </nav>

      {/* User section */}
      <div className="px-3 py-4 space-y-0.5"
        style={{ borderTop: "1px solid var(--border-subtle)" }}>
        <div className="flex items-center gap-3 px-3 py-2 mb-1">
          <div className="w-7 h-7 rounded-full bg-accent-violet/20 flex items-center justify-center text-xs font-bold text-accent-violet">
            {user?.full_name?.[0] ?? "U"}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-medium text-text-primary truncate">{user?.full_name ?? "User"}</p>
            <p className="text-[10px] text-text-muted capitalize">{user?.role ?? "—"}</p>
          </div>
        </div>
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-text-secondary hover:text-rose-400 hover:bg-rose-400/5 transition-colors">
          <LogOut size={14} />
          <span>Sign out</span>
        </button>
      </div>
    </aside>
  );
}
