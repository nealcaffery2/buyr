"use client";

import { useState } from "react";
import type { Buyer } from "@/app/(dashboard)/search/page";
import { formatCurrency, formatDate, daysSince } from "@/lib/utils";
import {
  ChevronDown,
  ChevronUp,
  Copy,
  Check,
  Phone,
  Mail,
  MapPin,
  Building2,
  TrendingUp,
} from "lucide-react";

export function BuyerCard({ rank, buyer }: { rank: number; buyer: Buyer }) {
  const [expanded, setExpanded] = useState(false);
  const [copied, setCopied] = useState(false);

  const days = daysSince(buyer.last_purchase);
  const isActive = buyer.purchase_count >= 3 && days !== null && days <= 90;

  function copyContact() {
    const phones = buyer.contacts
      .map((c) => c.phone)
      .filter(Boolean)
      .join(", ");
    const emails = buyer.contacts
      .map((c) => c.email)
      .filter(Boolean)
      .join(", ");
    const text = [buyer.name, phones, emails].filter(Boolean).join("\n");
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
      <div className="p-5">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-3 min-w-0">
            <span className="flex-shrink-0 w-7 h-7 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-xs font-bold text-slate-300">
              {rank}
            </span>
            <div className="min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <h3 className="font-semibold text-white text-sm leading-tight">
                  {buyer.name}
                </h3>
                {isActive && (
                  <span className="flex items-center gap-1 bg-green-900/50 text-green-400 border border-green-800 text-xs px-2 py-0.5 rounded-full">
                    <TrendingUp size={10} />
                    Active Buyer
                  </span>
                )}
              </div>
              <div className="flex items-center gap-3 mt-1.5 flex-wrap">
                <Stat
                  label="Purchases"
                  value={String(buyer.purchase_count)}
                  highlight
                />
                <Stat
                  label="Last Buy"
                  value={formatDate(buyer.last_purchase)}
                />
                <Stat
                  label="Avg Price"
                  value={formatCurrency(buyer.avg_price)}
                />
              </div>
            </div>
          </div>
          <button
            onClick={copyContact}
            className="flex-shrink-0 flex items-center gap-1.5 text-xs text-slate-400 hover:text-white border border-slate-700 hover:border-slate-500 rounded-md px-2.5 py-1.5 transition-colors"
          >
            {copied ? <Check size={12} /> : <Copy size={12} />}
            {copied ? "Copied" : "Copy"}
          </button>
        </div>

        {(buyer.registered_agent || buyer.contacts.length > 0) && (
          <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-3">
            {buyer.registered_agent && (
              <div className="bg-slate-800/50 rounded-lg p-3">
                <div className="flex items-center gap-1.5 text-slate-400 text-xs mb-1.5">
                  <Building2 size={11} />
                  Registered Agent
                </div>
                <p className="text-white text-sm font-medium">
                  {buyer.registered_agent}
                </p>
                {buyer.agent_address && (
                  <p className="text-slate-400 text-xs mt-0.5 flex items-start gap-1">
                    <MapPin size={10} className="mt-0.5 flex-shrink-0" />
                    {buyer.agent_address}
                  </p>
                )}
              </div>
            )}

            {buyer.contacts.length > 0 && (
              <div className="bg-slate-800/50 rounded-lg p-3">
                <div className="text-slate-400 text-xs mb-1.5">
                  Contact Info
                </div>
                <div className="space-y-1.5">
                  {buyer.contacts.slice(0, 2).map((c, i) => (
                    <div key={i} className="space-y-0.5">
                      {c.phone && (
                        <div className="flex items-center gap-1.5 text-sm text-white">
                          <Phone size={11} className="text-slate-400" />
                          {c.phone}
                          <Source label={c.source} />
                        </div>
                      )}
                      {c.email && (
                        <div className="flex items-center gap-1.5 text-sm text-white">
                          <Mail size={11} className="text-slate-400" />
                          {c.email}
                          <Source label={c.source} />
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {buyer.transactions?.length > 0 && (
        <>
          <button
            onClick={() => setExpanded(!expanded)}
            className="w-full flex items-center justify-center gap-1.5 text-xs text-slate-500 hover:text-slate-300 py-2.5 border-t border-slate-800 transition-colors"
          >
            {expanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
            {expanded
              ? "Hide"
              : `View ${buyer.transactions.length} deed records`}
          </button>

          {expanded && (
            <div className="border-t border-slate-800 divide-y divide-slate-800/50">
              {buyer.transactions.map((t, i) => (
                <div key={i} className="px-5 py-3 flex items-center gap-4">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-white truncate">
                      {t.property_address}
                    </p>
                    <p className="text-xs text-slate-500">
                      from {t.grantor_name}
                    </p>
                  </div>
                  <div className="text-right flex-shrink-0">
                    <p className="text-sm text-white">
                      {formatCurrency(t.sale_price)}
                    </p>
                    <p className="text-xs text-slate-500">
                      {formatDate(t.sale_date)}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

function Stat({
  label,
  value,
  highlight,
}: {
  label: string;
  value: string;
  highlight?: boolean;
}) {
  return (
    <div className="text-xs">
      <span className="text-slate-500">{label}: </span>
      <span className={highlight ? "text-blue-400 font-medium" : "text-slate-300"}>
        {value}
      </span>
    </div>
  );
}

function Source({ label }: { label: string }) {
  const colors: Record<string, string> = {
    batchdata: "bg-blue-900/50 text-blue-300 border-blue-800",
    propstream: "bg-purple-900/50 text-purple-300 border-purple-800",
    dealmachine: "bg-orange-900/50 text-orange-300 border-orange-800",
    opencorporates: "bg-slate-700 text-slate-300 border-slate-600",
    freepeoplesearch: "bg-slate-700 text-slate-300 border-slate-600",
  };
  const cls = colors[label.toLowerCase()] ?? "bg-slate-700 text-slate-300 border-slate-600";
  return (
    <span className={`text-xs border px-1.5 py-0.5 rounded ${cls}`}>
      {label}
    </span>
  );
}
