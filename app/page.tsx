import { redirect } from "next/navigation";
import { createServerClient } from "@/lib/supabase/server";
import { AuthForm } from "@/components/auth-form";

export default async function HomePage() {
  const supabase = await createServerClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (user) redirect("/search");

  return (
    <main className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 to-slate-800">
      <div className="w-full max-w-md px-6">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">Buyr</h1>
          <p className="text-slate-400 text-sm">
            Drop an address. Find the top 10 cash buyers.
          </p>
        </div>
        <AuthForm />
      </div>
    </main>
  );
}
