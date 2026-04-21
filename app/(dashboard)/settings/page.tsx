"use client";

import { useState } from "react";
import { Upload, KeyRound } from "lucide-react";
import { WholesalerUpload } from "@/components/wholesaler-upload";
import { ApiKeyForm } from "@/components/api-key-form";

const TABS = [
  { id: "wholesalers", label: "Wholesaler List", icon: Upload },
  { id: "api-keys", label: "API Keys", icon: KeyRound },
] as const;

type TabId = (typeof TABS)[number]["id"];

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<TabId>("wholesalers");

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white">
          Settings
        </h1>
        <p className="mt-1 text-sm text-slate-400">
          Configure your wholesaler list and API credentials.
        </p>
      </div>

      <div
        role="tablist"
        aria-label="Settings sections"
        className="inline-flex gap-1 rounded-lg border border-slate-800 bg-slate-900/60 p-1 backdrop-blur"
      >
        {TABS.map(({ id, label, icon: Icon }) => {
          const active = activeTab === id;
          return (
            <button
              key={id}
              role="tab"
              aria-selected={active}
              onClick={() => setActiveTab(id)}
              className={`flex items-center gap-2 rounded-md px-3.5 py-1.5 text-sm font-medium transition-all ${
                active
                  ? "bg-slate-800 text-white shadow-sm ring-1 ring-slate-700"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <Icon size={13} />
              {label}
            </button>
          );
        })}
      </div>

      <div className="animate-fade-in">
        {activeTab === "wholesalers" && <WholesalerUpload />}
        {activeTab === "api-keys" && <ApiKeyForm />}
      </div>
    </div>
  );
}
