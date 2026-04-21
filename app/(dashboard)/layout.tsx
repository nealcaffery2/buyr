import { DashboardNav } from "@/components/dashboard-nav";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-slate-950">
      <DashboardNav />
      <main className="max-w-5xl mx-auto px-4 py-10">{children}</main>
    </div>
  );
}
