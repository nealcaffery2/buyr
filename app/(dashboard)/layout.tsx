import { DashboardNav } from "@/components/dashboard-nav";

// Dashboard pages read runtime env vars (Supabase client, Google Places key)
// and subscribe to Realtime, so static prerender isn't meaningful.
export const dynamic = "force-dynamic";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="relative min-h-screen bg-slate-950 text-slate-100">
      {/* Ambient backdrop */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 overflow-hidden"
      >
        <div className="absolute -top-40 left-1/2 h-[420px] w-[820px] -translate-x-1/2 rounded-full bg-blue-600/10 blur-[120px]" />
        <div className="absolute -bottom-40 right-[-10%] h-[360px] w-[620px] rounded-full bg-indigo-600/5 blur-[120px]" />
        <div
          className="absolute inset-0 opacity-[0.025]"
          style={{
            backgroundImage:
              "radial-gradient(circle at 1px 1px, rgb(148 163 184) 1px, transparent 0)",
            backgroundSize: "28px 28px",
          }}
        />
      </div>

      <DashboardNav />
      <main className="relative mx-auto max-w-5xl px-4 py-10 sm:py-12">
        {children}
      </main>
    </div>
  );
}
