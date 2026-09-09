"use client";

import { useRouter } from "next/navigation";

export default function Dashboard() {
  const router = useRouter();

  return (
    <main className="min-h-screen bg-slate-100 p-8">
      <div className="mx-auto max-w-6xl">

        <h1 className="text-3xl font-bold text-slate-900">
          Smart Event Management
        </h1>

        <p className="mt-2 text-slate-600">
          Welcome to your dashboard
        </p>

        <div className="mt-8 grid gap-6 md:grid-cols-3">

          {/* My Events */}
          <button
            onClick={() => router.push("/dashboard/events")}
            className="rounded-xl bg-white p-6 text-left shadow transition hover:-translate-y-1 hover:shadow-lg"
          >
            <h2 className="text-xl font-semibold text-slate-900">
              My Events
            </h2>

            <p className="mt-2 text-slate-500">
              View and manage your events.
            </p>
          </button>

          {/* Create Event */}
          <button
            onClick={() => router.push("/dashboard/create-event")}
            className="rounded-xl bg-white p-6 text-left shadow transition hover:-translate-y-1 hover:shadow-lg"
          >
            <h2 className="text-xl font-semibold text-slate-900">
              Create Event
            </h2>

            <p className="mt-2 text-slate-500">
              Create a new event.
            </p>
          </button>

          {/* Upcoming Events */}
          <button
            onClick={() => router.push("/dashboard/upcoming")}
            className="rounded-xl bg-white p-6 text-left shadow transition hover:-translate-y-1 hover:shadow-lg"
          >
            <h2 className="text-xl font-semibold text-slate-900">
              Upcoming Events
            </h2>

            <p className="mt-2 text-slate-500">
              Check your upcoming events.
            </p>
          </button>

        </div>
      </div>
    </main>
  );
}