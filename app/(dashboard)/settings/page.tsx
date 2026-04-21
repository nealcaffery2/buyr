"use client";

import { useState } from "react";
import { WholesalerUpload } from "@/components/wholesaler-upload";
import { ApiKeyForm } from "@/components/api-key-form";

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<"wholesalers" | "api-keys">(
    "wholesalers"
  );

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white mb-1">Settings</h1>
        <p className="text-slate-400 text-sm">
          Configure your wholesaler list and API credentials.
        </p>
      </div>

      <div className="flex gap-1 bg-slate-900 rounded-lg p-1 w-fit">
        {(["wholesalers", "api-keys"] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${
              activeTab === tab
                ? "bg-slate-700 text-white"
                : "text-slate-400 hover:text-white"
            }`}
          >
            {tab === "wholesalers" ? "Wholesaler List" : "API Keys"}
          </button>
        ))}
      </div>

      {activeTab === "wholesalers" && <WholesalerUpload />}
      {activeTab === "api-keys" && <ApiKeyForm />}
    </div>
  );
}
