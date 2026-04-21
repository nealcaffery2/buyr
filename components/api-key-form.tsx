"use client";

import { useState, useEffect } from "react";
import { createBrowserClient } from "@/lib/supabase/client";
import { Save, Eye, EyeOff } from "lucide-react";

type ApiKeys = {
  batchdata_api_key: string;
  propstream_email: string;
  propstream_password: string;
  dealmachine_api_key: string;
  opencorporates_api_key: string;
  google_maps_api_key: string;
};

const FIELDS: Array<{
  key: keyof ApiKeys;
  label: string;
  type?: "password";
  placeholder?: string;
}> = [
  { key: "batchdata_api_key",      label: "BatchData API Key",      type: "password", placeholder: "bd_live_..." },
  { key: "propstream_email",       label: "PropStream Email",                          placeholder: "you@example.com" },
  { key: "propstream_password",    label: "PropStream Password",    type: "password" },
  { key: "dealmachine_api_key",    label: "DealMachine API Key",    type: "password", placeholder: "dm_..." },
  { key: "opencorporates_api_key", label: "OpenCorporates API Key", type: "password" },
  { key: "google_maps_api_key",    label: "Google Maps API Key",    type: "password" },
];

const EMPTY: ApiKeys = {
  batchdata_api_key: "",
  propstream_email: "",
  propstream_password: "",
  dealmachine_api_key: "",
  opencorporates_api_key: "",
  google_maps_api_key: "",
};

export function ApiKeyForm() {
  const supabase = createBrowserClient();
  const [keys, setKeys] = useState<ApiKeys>(EMPTY);
  const [visible, setVisible] = useState<Set<string>>(new Set());
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    supabase
      .from("team_api_keys")
      .select("*")
      .eq("id", "team")
      .single()
      .then(({ data }) => {
        if (data) setKeys({ ...EMPTY, ...data });
      });
  }, [supabase]);

  function toggleVisible(key: string) {
    setVisible((prev) => {
      const next = new Set(prev);
      next.has(key) ? next.delete(key) : next.add(key);
      return next;
    });
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);

    const { error: err } = await supabase
      .from("team_api_keys")
      .upsert({ id: "team", ...keys, updated_at: new Date().toISOString() }, { onConflict: "id" });

    setSaving(false);
    if (err) {
      setError(`Save failed: ${err.message}`);
    } else {
      setError(null);
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    }
  }

  return (
    <form
      onSubmit={handleSave}
      className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-5"
    >
      <div>
        <h2 className="text-white font-medium mb-1">API Keys</h2>
        <p className="text-slate-400 text-sm">
          Shared across your team. Stored in your Supabase project.
        </p>
      </div>

      <div className="space-y-4">
        {FIELDS.map(({ key, label, type, placeholder }) => (
          <div key={key}>
            <label className="block text-sm text-slate-300 mb-1">{label}</label>
            <div className="relative">
              <input
                type={type === "password" ? (visible.has(key) ? "text" : "password") : "text"}
                value={keys[key]}
                onChange={(e) => setKeys((prev) => ({ ...prev, [key]: e.target.value }))}
                placeholder={placeholder}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 pr-9"
              />
              {type === "password" && (
                <button
                  type="button"
                  onClick={() => toggleVisible(key)}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"
                >
                  {visible.has(key) ? <EyeOff size={14} /> : <Eye size={14} />}
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      {error && <p className="text-red-400 text-xs">{error}</p>}

      <button
        type="submit"
        disabled={saving}
        className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-sm font-medium rounded-lg px-4 py-2 transition-colors"
      >
        <Save size={14} />
        {saving ? "Saving..." : saved ? "Saved!" : "Save API Keys"}
      </button>
    </form>
  );
}
