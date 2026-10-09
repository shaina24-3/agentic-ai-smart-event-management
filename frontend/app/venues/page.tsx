"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { formatTime } from "../../lib/formatTime";

type Venue = {
  id: number;
  name: string;
  capacity: number;
  location: string;
};

type VenueEvent = {
  id: number;
  title: string;
  date: string;
  time?: string;
  venue_id: number;
};

export default function VenuesPage() {
  const [venues, setVenues] = useState<Venue[]>([]);
  const [events, setEvents] = useState<VenueEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadVenueData = async () => {
      const [venueResult, eventResult] = await Promise.all([
        fetch("http://127.0.0.1:8000/api/venues")
          .then((response) => (response.ok ? response.json() : []))
          .catch((error) => {
            console.error(error);
            return [];
          }),
        fetch("http://127.0.0.1:8000/api/events")
          .then((response) => (response.ok ? response.json() : []))
          .catch((error) => {
            console.error(error);
            return [];
          }),
      ]);

      setVenues(venueResult);
      setEvents(eventResult);
      setLoading(false);
    };

    void loadVenueData();
  }, []);

  const now = new Date();
  const today = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;

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
          <svg
            className="h-4 w-4"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
          >
            <path d="m12 3 1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8L12 3Z" />
            <path d="m19 14 .9 2.1L22 17l-2.1.9L19 20l-.9-2.1L16 17l2.1-.9L19 14Z" />
          </svg>
          <span>Check Live Dates with AI</span>
        </Link>
      </div>

      {loading ? (
        <p className="text-sm text-slate-400 py-12 text-center">Loading venues...</p>
      ) : venues.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {venues.map((v) => {
            const venueEvents = events
              .filter((event) => event.venue_id === v.id)
              .sort((first, second) =>
                first.date.localeCompare(second.date) ||
                (first.time || "").localeCompare(second.time || "")
              );

            return (
              <div
                key={v.id}
                className="flex flex-col rounded-lg border border-slate-200 bg-white p-4 shadow-xs transition hover:border-slate-300 sm:p-5"
              >
                <div className="flex items-center gap-2.5">
                  <svg
                    className="h-4 w-4 shrink-0 text-slate-500"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.8"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    aria-hidden="true"
                  >
                    <path d="M3 21h18M5 21V5l7-3 7 3v16" />
                    <path d="M9 9h1M14 9h1M9 13h1M14 13h1M10 21v-4h4v4" />
                  </svg>
                  <h3 className="min-w-0 truncate text-sm font-semibold text-slate-900">
                    {v.name}
                  </h3>
                </div>

                <dl className="mt-4 space-y-2 border-b border-slate-100 pb-4 text-xs">
                  <div className="flex items-start gap-2 text-slate-900">
                    <svg
                      className="mt-0.5 h-4 w-4 shrink-0 text-slate-400"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="1.8"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      aria-hidden="true"
                    >
                      <path d="M20 10c0 5-8 11-8 11S4 15 4 10a8 8 0 1 1 16 0Z" />
                      <circle cx="12" cy="10" r="2.5" />
                    </svg>
                    <div>
                      <dt className="text-[10px] font-medium uppercase text-slate-900">Address</dt>
                      <dd className="mt-0.5">{v.location}</dd>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 text-slate-900">
                    <svg
                      className="h-4 w-4 shrink-0 text-slate-400"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="1.8"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      aria-hidden="true"
                    >
                      <path d="M16 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                      <circle cx="10" cy="7" r="4" />
                      <path d="M20 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" />
                    </svg>
                    <div>
                      <dt className="text-[10px] font-medium uppercase text-slate-900">Capacity</dt>
                      <dd className="mt-0.5">{v.capacity} seats</dd>
                    </div>
                  </div>
                </dl>

                <div className="pt-3">
                  <h4 className="text-[10px] font-semibold uppercase text-slate-900">
                    Scheduled Events
                  </h4>
                  {venueEvents.length > 0 ? (
                    <ol className="mt-2 divide-y divide-slate-100">
                      {venueEvents.map((event, index) => {
                        const isCompleted = event.date < today;
                        return (
                          <li key={event.id} className="flex items-start justify-between gap-3 py-2 text-xs">
                            <div className="min-w-0">
                              <p className="break-words font-medium text-slate-900">
                                {index + 1}. {event.title}
                              </p>
                              <p className="mt-1 text-slate-900">
                                {event.date}{event.time ? ` · ${formatTime(event.time)}` : ""}
                              </p>
                            </div>
                            <span
                              className={`shrink-0 font-semibold ${
                                isCompleted ? "text-red-600" : "text-green-700"
                              }`}
                            >
                              {isCompleted ? "Completed" : "Upcoming"}
                            </span>
                          </li>
                        );
                      })}
                    </ol>
                  ) : (
                    <p className="mt-2 text-xs text-slate-500">No scheduled events</p>
                  )}
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

