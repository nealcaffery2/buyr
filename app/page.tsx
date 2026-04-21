import { redirect } from "next/navigation";
import { createServerClient } from "@/lib/supabase/server";
import { AuthForm } from "@/components/auth-form";
import { Zap } from "lucide-react";

export default async function HomePage() {
  // Gracefully skip auth check when env vars aren't configured yet
  if (process.env.NEXT_PUBLIC_SUPABASE_URL) {
    try {
      const supabase = await createServerClient();
      const {
        data: { user },
      } = await supabase.auth.getUser();
      if (user) redirect("/search");
    } catch {
      // Supabase not configured — show login page anyway
    }
  }

  return (
    <main className="min-h-screen bg-slate-950 flex flex-col">
      {/* Hero */}
      <div className="flex-1 flex flex-col items-center justify-center px-4 py-16">
        <div className="w-full max-w-md space-y-8 animate-fade-up">
          {/* Logo mark */}
          <div className="text-center">
            <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-blue-600 mb-5">
              <Zap size={28} className="text-white" fill="white" />
            </div>
            <h1 className="text-4xl font-bold text-white tracking-tight">
              Buyr
            </h1>
            <p className="mt-2 text-slate-400 text-base">
              Drop an address. Get your top 10 cash buyers in seconds.
            </p>
          </div>

          {/* Feature pills */}
          <div className="flex flex-wrap justify-center gap-2">
            {["County Deed Records", "OpenCorporates", "BatchData Skip Trace"].map((f) => (
              <span
                key={f}
                className="text-xs text-slate-400 bg-slate-800/60 border border-slate-700/60 rounded-full px-3 py-1"
              >
                {f}
              </span>
            ))}
          </div>

          {/* Auth card */}
          <AuthForm />
        </div>
      </div>

      <p className="text-center text-slate-700 text-xs pb-6">
        Wholesaler sniping tool — find buyers, close faster.
      </p>
    </main>
  );
}
