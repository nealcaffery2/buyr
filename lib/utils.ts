import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import type { Buyer } from "@/app/(dashboard)/search/page";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(amount: number | null): string {
  if (!amount) return "N/A";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(amount);
}

export function formatDate(dateStr: string | null): string {
  if (!dateStr) return "N/A";
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export function daysSince(dateStr: string | null): number | null {
  if (!dateStr) return null;
  const ms = Date.now() - new Date(dateStr).getTime();
  return Math.floor(ms / (1000 * 60 * 60 * 24));
}

export function exportToCsv(buyers: Buyer[], filename: string) {
  const rows = buyers.map((b) => ({
    Rank: buyers.indexOf(b) + 1,
    "LLC Name": b.name,
    "Purchase Count": b.purchase_count,
    "Last Purchase": b.last_purchase ?? "",
    "Avg Price": b.avg_price ?? "",
    Score: b.score,
    "Registered Agent": b.registered_agent ?? "",
    "Agent Address": b.agent_address ?? "",
    Phone: b.contacts.map((c) => c.phone).filter(Boolean).join("; "),
    Email: b.contacts.map((c) => c.email).filter(Boolean).join("; "),
    "Contact Source": b.contacts.map((c) => c.source).join("; "),
  }));

  const headers = Object.keys(rows[0]);
  const csv = [
    headers.join(","),
    ...rows.map((r) =>
      headers
        .map((h) => `"${String(r[h as keyof typeof r]).replace(/"/g, '""')}"`)
        .join(",")
    ),
  ].join("\n");

  const blob = new Blob([csv], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${filename}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}
