"use client";

import { useState } from "react";
import { Search } from "lucide-react";

export function SearchBar({
  onSearch,
  loading,
}: {
  onSearch: (address: string) => void;
  loading: boolean;
}) {
  const [address, setAddress] = useState("");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (address.trim()) onSearch(address.trim());
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-3">
      <div className="flex-1 relative">
        <Search
          className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500"
          size={16}
        />
        <input
          type="text"
          aria-label="Property address"
          value={address}
          onChange={(e) => setAddress(e.target.value)}
          placeholder="11206 Cape Primrose San Antonio TX"
          disabled={loading}
          className="w-full bg-slate-900 border border-slate-700 rounded-lg pl-9 pr-4 py-3 text-white text-sm placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
        />
      </div>
      <button
        type="submit"
        disabled={loading || !address.trim()}
        className="bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-medium rounded-lg px-6 text-sm transition-colors"
      >
        {loading ? "Running..." : "Snipe"}
      </button>
    </form>
  );
}
