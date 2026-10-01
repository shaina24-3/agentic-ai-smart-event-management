"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

type Venue = {
  id: number;
  name: string;
  capacity: number;
  location: string;
};

export default function VenuesPage() {
  const [venues, setVenues] = useState<Venue[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("http://127.0.0.1:8000/api/venues")
      .then((res) => (res.ok ? res.json() : []))
      .then((data) => setVenues(data))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Campus Venues & Facilities</h1>
          <p className="text-sm text-slate-500 mt-1">
            Browse available halls, auditoriums, seating capacities, and locations.
          </p>
        </div>

        <Link
          href="/ai-assistant?prompt=What+are+the+venues+available"
          className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-semibold text-xs rounded-xl shadow-xs hover:opacity-90 transition"
        >
          <span>🤖</span>
          <span>Check Live Dates with AI</span>
        </Link>
      </div>

      {loading ? (
        <p className="text-sm text-slate-400 py-12 text-center">Loading venues...</p>
      ) : venues.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {venues.map((v, idx) => {
            const icons = ["🏛️", "🏢", "🎪", "🏬"];
            const icon = icons[idx % icons.length];

            return (
              <div
                key={v.id}
                className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs flex flex-col justify-between hover:shadow-md transition"
              >
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-2xl p-2.5 bg-indigo-50 rounded-xl block w-fit">
                      {icon}
                    </span>
                    <span className="text-[11px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full">
                      🟢 Certified Active
                    </span>
                  </div>

                  <h3 className="font-bold text-base text-slate-900 mt-3">{v.name}</h3>
                  <p className="text-xs text-slate-500 mt-1 flex items-center gap-1.5">
                    <span>📍</span>
                    <span>{v.location}</span>
                  </p>
                </div>

                <div className="mt-5 pt-4 border-t border-slate-100 flex items-center justify-between">
                  <div>
                    <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">
                      Max Capacity
                    </span>
                    <span className="text-base font-extrabold text-indigo-700">
                      {v.capacity} seats
                    </span>
                  </div>

                  <Link
                    href={`/ai-assistant?prompt=Create+an+event+at+venue+${v.id}`}
                    className="px-3 py-1.5 text-xs font-semibold text-indigo-600 bg-indigo-50 hover:bg-indigo-100 rounded-lg transition"
                  >
                    Book Venue →
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <p className="text-sm text-slate-400 py-12 text-center">No venues found in database.</p>
      )}
    </div>
  );
}

