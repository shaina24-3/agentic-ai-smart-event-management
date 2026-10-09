"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { formatTime } from "../../lib/formatTime";

type AdminStats = {
  total_events: number;
  total_attendees: number;
  total_venues: number;
  agent_queries: number;
  total_users: number;
};

type DashboardEvent = {
  id: number;
  title: string;
  date: string;
  time?: string;
  capacity: number;
};

const emptyStats: AdminStats = {
  total_events: 0,
  total_attendees: 0,
  total_venues: 0,
  agent_queries: 0,
  total_users: 0,
};

export default function AdminDashboardPage() {
  const router = useRouter();
  const [adminName, setAdminName] = useState("Admin");
  const [stats, setStats] = useState<AdminStats>(emptyStats);
  const [events, setEvents] = useState<DashboardEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    const token = localStorage.getItem("access_token");
    if (!token) {
      router.push("/");
      return () => {
        active = false;
      };
    }

    fetch("http://127.0.0.1:8000/api/auth/me", {
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    })
      .then(async (response) => {
        if (response.status === 401) {
          router.push("/");
          return null;
        }
        if (!response.ok) throw new Error("Unable to verify account.");
        return response.json();
      })
      .then(async (user) => {
        if (!user) return;
        if (String(user.role || "").toUpperCase() !== "ADMIN") {
          router.push("/dashboard");
          return;
        }
        if (active) setAdminName(user.name || "Admin");

        const [statsResponse, eventsResponse] = await Promise.all([
          fetch("http://127.0.0.1:8000/api/admin/dashboard-stats", {
            headers: { Authorization: `Bearer ${token}` },
            cache: "no-store",
          }),
          fetch("http://127.0.0.1:8000/api/events", { cache: "no-store" }),
        ]);
        if (!statsResponse.ok) throw new Error("Unable to load dashboard analytics.");
        const statsData: AdminStats = await statsResponse.json();
        const eventData: DashboardEvent[] = eventsResponse.ok ? await eventsResponse.json() : [];
        if (active) {
          setStats(statsData);
          setEvents(eventData);
        }
      })
      .catch((error) => {
        console.error("Admin dashboard error:", error);
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [router]);

  const metrics = [
    { label: "Total Events", value: stats.total_events },
    { label: "Venues", value: stats.total_venues },
    { label: "Users", value: stats.total_users },
  ];
  const now = new Date();
  const today = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
  const upcomingEvents = events
    .filter((event) => event.date >= today)
    .sort((first, second) => first.date.localeCompare(second.date))
    .slice(0, 3);

  return (
    <main className="mx-auto min-h-full max-w-7xl space-y-8">
      <section
        style={{ backgroundColor: "#6d28d9" }}
        className="flex flex-col gap-6 rounded-2xl bg-purple-700 px-6 py-8 text-white shadow-sm sm:flex-row sm:items-center sm:justify-between md:px-8"
      >
        <div>
          <p className="text-sm font-medium text-slate-300">Administration</p>
          <h1 className="mt-2 text-2xl font-semibold md:text-3xl">
            Welcome, {adminName}
          </h1>
          <p className="mt-2 text-sm text-slate-300">
            Manage events, registrations, and attendees.
          </p>
        </div>
        <button
          type="button"
          onClick={() => router.push("/ai-assistant")}
          className="w-fit rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-500"
        >
          Open Your AI Agent
        </button>
      </section>

      <section aria-label="Admin analytics" className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        {metrics.map((metric) => (
          <div key={metric.label} className="rounded-xl border border-slate-200 bg-white p-5">
            <h2 className="text-sm font-medium text-slate-500">{metric.label}</h2>
            <p className="mt-3 text-3xl font-semibold text-slate-900">
              {loading ? "-" : metric.value}
            </p>
          </div>
        ))}
      </section>

      <section className="rounded-xl border border-slate-200 bg-white p-6">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold text-slate-900">Upcoming Events</h2>
          <button
            type="button"
            onClick={() => router.push("/events")}
            className="text-sm font-semibold text-blue-600 hover:text-blue-800"
          >
            View all
          </button>
        </div>

        {upcomingEvents.length > 0 ? (
          <div className="mt-5 grid gap-4 md:grid-cols-3">
            {upcomingEvents.map((event) => (
              <div key={event.id} className="rounded-lg border border-slate-200 p-4">
                <h3 className="font-semibold text-slate-900">{event.title}</h3>
                <p className="mt-2 text-sm text-slate-500">
                  {event.date}{event.time ? ` • ${formatTime(event.time)}` : ""}
                </p>
                <p className="mt-1 text-sm text-slate-500">Capacity: {event.capacity}</p>
              </div>
            ))}
          </div>
        ) : (
          <p className="mt-4 text-slate-500">No upcoming events.</p>
        )}
      </section>
    </main>
  );
}