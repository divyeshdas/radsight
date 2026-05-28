import { Sidebar } from "@/components/layout/Sidebar";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen" style={{ backgroundColor: "var(--bg-primary)" }}>
      <Sidebar />
      <main className="flex-1 ml-60 flex flex-col min-h-screen">
        {children}
      </main>
    </div>
  );
}
