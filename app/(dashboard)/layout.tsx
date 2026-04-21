import { redirect } from "next/navigation";
import { createServerClient } from "@/lib/supabase/server";
import { DashboardNav } from "@/components/dashboard-nav";

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  if (!process.env.NEXT_PUBLIC_SUPABASE_URL) redirect("/");

  try {
    const supabase = await createServerClient();
    const {
      data: { user },
    } = await supabase.auth.getUser();

    if (!user) redirect("/");

    return (
      <div className="min-h-screen bg-slate-950">
        <DashboardNav user={user} />
        <main className="max-w-5xl mx-auto px-4 py-10">{children}</main>
      </div>
    );
  } catch {
    redirect("/");
  }
}
