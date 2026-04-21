import { redirect } from "next/navigation";
import { createServerClient } from "@/lib/supabase/server";
import { DashboardNav } from "@/components/dashboard-nav";

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const supabase = await createServerClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) redirect("/");

  return (
    <div className="min-h-screen bg-slate-950">
      <DashboardNav user={user} />
      <main className="max-w-7xl mx-auto px-4 py-8">{children}</main>
    </div>
  );
}
