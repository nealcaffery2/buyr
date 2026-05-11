"use client";

import { useState, useRef } from "react";
import { createBrowserClient } from "@/lib/supabase/client";
import { Upload, CheckCircle, AlertCircle } from "lucide-react";
import * as XLSX from "xlsx";

type ParsedWholesaler = { name: string; state: string };

export function WholesalerUpload() {
  const supabase = createBrowserClient();
  const inputRef = useRef<HTMLInputElement>(null);
  const [status, setStatus] = useState<
    "idle" | "parsing" | "uploading" | "done" | "error"
  >("idle");
  const [count, setCount] = useState(0);
  const [error, setError] = useState<string | null>(null);

  async function handleFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    setStatus("parsing");
    setError(null);

    try {
      const buffer = await file.arrayBuffer();
      const wb = XLSX.read(buffer, { type: "array" });
      const ws = wb.Sheets[wb.SheetNames[0]];
      const rows = XLSX.utils.sheet_to_json<Record<string, string>>(ws, {
        defval: "",
      });

      const wholesalers: ParsedWholesaler[] = [];
      for (const row of rows) {
        const name =
          row["LLC Name"] ||
          row["Name"] ||
          row["Wholesaler"] ||
          row["Company"] ||
          Object.values(row)[0];
        const state =
          row["State"] ||
          row["ST"] ||
          row["state"] ||
          Object.values(row)[1] ||
          "";
        const stateRaw = String(state).trim().toUpperCase();
        // Reject full state names and anything that isn't exactly 2 alpha chars
        const stateCode = /^[A-Z]{2}$/.test(stateRaw) ? stateRaw : "";
        if (name?.trim() && stateCode) {
          wholesalers.push({
            name: String(name).trim(),
            state: stateCode,
          });
        }
      }

      if (wholesalers.length === 0) {
        throw new Error(
          'No wholesalers found. Expected columns: "LLC Name" and "State".'
        );
      }

      setStatus("uploading");

      const { error: upsertErr } = await supabase
        .from("wholesalers")
        .upsert(wholesalers.map((w) => ({ ...w, source: "user_sheet" })), {
          onConflict: "name,state",
        });

      if (upsertErr) throw new Error(upsertErr.message);

      setCount(wholesalers.length);
      setStatus("done");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
      setStatus("error");
    }

    if (inputRef.current) inputRef.current.value = "";
  }

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
      <div>
        <h2 className="text-white font-medium mb-1">Wholesaler List</h2>
        <p className="text-slate-400 text-sm">
          Upload an Excel file with your wholesaler LLCs. Expected columns:{" "}
          <code className="text-blue-400">LLC Name</code> and{" "}
          <code className="text-blue-400">State</code>.
        </p>
      </div>

      <div
        className="border-2 border-dashed border-slate-700 hover:border-slate-500 rounded-lg p-8 text-center cursor-pointer transition-colors"
        onClick={() => inputRef.current?.click()}
      >
        <Upload className="mx-auto text-slate-500 mb-2" size={24} />
        <p className="text-slate-400 text-sm">
          Click to upload <span className="text-slate-300">.xlsx</span> or{" "}
          <span className="text-slate-300">.csv</span>
        </p>
        <input
          ref={inputRef}
          type="file"
          accept=".xlsx,.xls,.csv"
          onChange={handleFile}
          className="hidden"
        />
      </div>

      {status === "parsing" && (
        <p className="text-slate-400 text-sm">Parsing file...</p>
      )}
      {status === "uploading" && (
        <p className="text-slate-400 text-sm">Uploading to database...</p>
      )}
      {status === "done" && (
        <div className="flex items-center gap-2 text-green-400 text-sm">
          <CheckCircle size={14} />
          {count} wholesalers uploaded successfully
        </div>
      )}
      {status === "error" && (
        <div className="flex items-center gap-2 text-red-400 text-sm">
          <AlertCircle size={14} />
          {error}
        </div>
      )}
    </div>
  );
}
