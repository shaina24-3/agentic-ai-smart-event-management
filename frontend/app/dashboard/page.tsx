"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

type Event = { id: number; title: string; date: string; time: string; venue: string; capacity: number };

export default function Dashboard() {
  const router = useRouter();
  const [count, setCount] = useState(0);
  const [upcoming, setUpcoming] = useState<Event[]>([]);

  useEffect(() => {
    const load = () => {
      const data: Event[] = JSON.parse(localStorage.getItem("events") || "[]");
      const today = new Date().toISOString().split("T")[0];
      setCount(data.length);
      setUpcoming(data.filter((e) => e.date >= today).sort((a,b) => a.date.localeCompare(b.date)).slice(0, 3));
    };
    load();
    window.addEventListener("focus", load);
    return () => window.removeEventListener("focus", load);
  }, []);

  return (
    <main className="min-h-screen bg-slate-100 px-4 py-8 md:px-6">
      <div className="mx-auto max-w-7xl">
        <h1 className="text-3xl font-bold">Welcome to your dashboard</h1>
        <p className="mt-2 text-slate-600">Manage your events easily from one place.</p>
        <div className="mt-8 grid gap-6 md:grid-cols-3">
          <button onClick={() => router.push("/events")} className="rounded-xl bg-white p-6 text-left shadow hover:shadow-lg">
            <h2 className="text-xl font-semibold">My Events</h2><p className="mt-4 text-4xl font-bold text-blue-600">{count}</p><p className="mt-2 text-slate-500">View and manage your events.</p>
          </button>
          <button onClick={() => router.push("/create")} className="rounded-xl bg-white p-6 text-left shadow hover:shadow-lg">
            <h2 className="text-xl font-semibold">Create Event</h2><p className="mt-4 text-4xl font-bold text-blue-600">+</p><p className="mt-2 text-slate-500">Create a new event.</p>
          </button>
          <button onClick={() => router.push("/upcoming")} className="rounded-xl bg-white p-6 text-left shadow hover:shadow-lg">
            <h2 className="text-xl font-semibold">Upcoming Events</h2><p className="mt-4 text-4xl font-bold text-blue-600">→</p><p className="mt-2 text-slate-500">Check upcoming events.</p>
          </button>
        </div>
        <section className="mt-8 rounded-xl bg-white p-6 shadow">
          <div className="flex items-center justify-between"><h2 className="text-xl font-semibold">Upcoming Events</h2><button onClick={() => router.push("/upcoming")} className="text-sm font-semibold text-blue-600">View all</button></div>
          {upcoming.length ? <div className="mt-5 grid gap-4 md:grid-cols-3">{upcoming.map(e => <div key={e.id} className="rounded-lg border p-4"><h3 className="font-semibold">{e.title}</h3><p className="mt-2 text-sm text-slate-500">{e.date} • {e.time}</p><p className="text-sm text-slate-500">{e.venue}</p></div>)}</div> : <p className="mt-4 text-slate-500">No upcoming events.</p>}
        </section>
      </div>
    </main>
  );
}