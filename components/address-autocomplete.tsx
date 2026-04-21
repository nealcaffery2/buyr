"use client";

import { useEffect, useRef } from "react";
import { Search } from "lucide-react";

// Minimal subset of the Google Maps JS API we use.
type PlaceResult = {
  formatted_address?: string;
  name?: string;
};

type AutocompleteInstance = {
  addListener: (event: string, handler: () => void) => void;
  getPlace: () => PlaceResult;
};

type GoogleMaps = {
  maps: {
    places: {
      Autocomplete: new (
        input: HTMLInputElement,
        opts: {
          types?: string[];
          componentRestrictions?: { country: string | string[] };
          fields?: string[];
        },
      ) => AutocompleteInstance;
    };
  };
};

declare global {
  interface Window {
    google?: GoogleMaps;
    __buyrGoogleMapsLoader?: Promise<GoogleMaps>;
  }
}

function loadGoogleMaps(apiKey: string): Promise<GoogleMaps> {
  if (typeof window === "undefined") return Promise.reject(new Error("SSR"));
  if (window.google?.maps?.places) return Promise.resolve(window.google);
  if (window.__buyrGoogleMapsLoader) return window.__buyrGoogleMapsLoader;

  window.__buyrGoogleMapsLoader = new Promise((resolve, reject) => {
    const existing = document.querySelector<HTMLScriptElement>(
      "script[data-buyr-google-maps]",
    );
    const onReady = () => {
      if (window.google?.maps?.places) resolve(window.google);
      else reject(new Error("Google Maps loaded without places library"));
    };
    if (existing) {
      existing.addEventListener("load", onReady);
      existing.addEventListener("error", () =>
        reject(new Error("Failed to load Google Maps script")),
      );
      return;
    }
    const script = document.createElement("script");
    script.src = `https://maps.googleapis.com/maps/api/js?key=${encodeURIComponent(
      apiKey,
    )}&libraries=places&v=weekly`;
    script.async = true;
    script.defer = true;
    script.dataset.buyrGoogleMaps = "true";
    script.addEventListener("load", onReady);
    script.addEventListener("error", () =>
      reject(new Error("Failed to load Google Maps script")),
    );
    document.head.appendChild(script);
  });

  return window.__buyrGoogleMapsLoader;
}

export function AddressAutocomplete({
  value,
  onChange,
  onSelect,
  disabled,
  placeholder,
}: {
  value: string;
  onChange: (address: string) => void;
  onSelect?: (address: string) => void;
  disabled?: boolean;
  placeholder?: string;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const apiKey = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY;

  useEffect(() => {
    if (!apiKey || !inputRef.current) return;
    let cancelled = false;
    let instance: AutocompleteInstance | null = null;

    loadGoogleMaps(apiKey)
      .then((google) => {
        if (cancelled || !inputRef.current) return;
        instance = new google.maps.places.Autocomplete(inputRef.current, {
          types: ["address"],
          componentRestrictions: { country: "us" },
          fields: ["formatted_address", "name"],
        });
        instance.addListener("place_changed", () => {
          const place = instance!.getPlace();
          const addr = place.formatted_address ?? place.name ?? "";
          if (!addr) return;
          onChange(addr);
          onSelect?.(addr);
        });
      })
      .catch((err) => {
        console.warn("[buyr] Google Places unavailable:", err);
      });

    return () => {
      cancelled = true;
    };
    // Only attach once; handlers read latest props via closure over refs.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [apiKey]);

  return (
    <div className="relative flex-1">
      <Search
        size={16}
        className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 pointer-events-none"
      />
      <input
        ref={inputRef}
        type="text"
        aria-label="Property address"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        placeholder={placeholder}
        autoComplete="off"
        className="w-full h-12 bg-slate-900 border border-slate-700 hover:border-slate-600 focus:border-blue-500 rounded-xl pl-10 pr-4 text-white text-sm placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/30 disabled:opacity-50 transition-colors"
      />
    </div>
  );
}
