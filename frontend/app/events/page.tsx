"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

type Event = {
  id: number;
  title: string;
  description: string;
  date: string;
  time: string;
  venue?: string;
  venue_name?: string;
  capacity: number;
};

export default function MyEvents() {
  const router = useRouter();

  const [events, setEvents] = useState<Event[]>([]);
  const [search, setSearch] = useState("");
  const [isAdmin, setIsAdmin] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadEvents = async () => {
      const token = localStorage.getItem("access_token");

      if (!token) {
        router.push("/");
        return;
      }

      try {
        // Check logged-in user's role
        const userResponse = await fetch(
          "http://127.0.0.1:8000/api/auth/me",
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );

        if (!userResponse.ok) {
          localStorage.removeItem("access_token");
          localStorage.removeItem("userEmail");
          localStorage.removeItem("userName");
          router.push("/");
          return;
        }

        const userData = await userResponse.json();

        console.log("EVENTS PAGE USER:", userData);

        setIsAdmin(userData.role === "ADMIN");

        // Load events
        const response = await fetch(
          "http://127.0.0.1:8000/api/events"
        );

        const data = await response.json();

        if (!response.ok) {
          alert(data.detail || "Failed to load events.");
          return;
        }

        setEvents(data);
      } catch (error) {
        console.error(error);
        alert("Cannot connect to the backend.");
      } finally {
        setLoading(false);
      }
    };

    loadEvents();
  }, [router]);

  const deleteEvent = (id: number) => {
    if (!isAdmin) {
      alert("Only administrators can delete events.");
      return;
    }

    const confirmed = confirm(
      "Are you sure you want to delete this event?"
    );

    if (!confirmed) {
      return;
    }

    const updatedEvents = events.filter(
      (event) => event.id !== id
    );

    setEvents(updatedEvents);

    localStorage.setItem(
      "events",
      JSON.stringify(updatedEvents)
    );

    alert("Event deleted successfully!");
  };

  const filteredEvents = events.filter((event) => {
    const searchText = search.toLowerCase();
    const venueName = (event.venue_name || event.venue || "").toLowerCase();

    return (
      event.title?.toLowerCase().includes(searchText) ||
      event.description?.toLowerCase().includes(searchText) ||
      venueName.includes(searchText)
    );
  });

  const venueDisplay = (event: Event) =>
    event.venue_name || event.venue || "Unknown venue";

  if (loading) {
    return (
      <main className="min-h-screen bg-slate-100 flex items-center justify-center">
        <p className="text-slate-600">
          Loading events...
        </p>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-slate-100 px-4 py-8 md:px-6">
      <div className="mx-auto max-w-7xl">

        {/* Back to Dashboard */}
        <button
          type="button"
          onClick={() => router.push("/dashboard")}
          className="mb-5 text-sm font-medium text-blue-600 hover:text-blue-800"
        >
          ← Back to Dashboard
        </button>

        {/* Page Header */}
        <div className="flex flex-col justify-between gap-4 md:flex-row md:items-center">

          <div>
            <h1 className="text-3xl font-bold text-slate-900">
              Events
            </h1>

            <p className="mt-2 text-slate-600">
              {isAdmin
                ? "View and manage all events."
                : "View and register for available events."}
            </p>
          </div>

          {/* CREATE EVENT - ADMIN ONLY */}
          {isAdmin && (
            <button
              type="button"
              onClick={() => router.push("/create")}
              className="rounded-lg bg-blue-600 px-5 py-3 font-semibold text-white transition hover:bg-blue-700"
            >
              + Create Event
            </button>
          )}

        </div>

        {/* Search */}
        <div className="mt-8">
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search events by title, description, or venue..."
            className="w-full rounded-xl border border-slate-300 bg-white px-5 py-4 text-slate-900 shadow-sm outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
          />
        </div>

        {/* No Events */}
        {events.length === 0 ? (
          <div className="mt-8 rounded-xl bg-white p-8 text-center shadow">

            <h2 className="text-xl font-semibold text-slate-900">
              No Events Yet
            </h2>

            <p className="mt-2 text-slate-500">
              {isAdmin
                ? "You have not created any events yet."
                : "There are no available events yet."}
            </p>

            {/* CREATE EVENT - ADMIN ONLY */}
            {isAdmin && (
              <button
                type="button"
                onClick={() => router.push("/create")}
                className="mt-5 rounded-lg bg-blue-600 px-5 py-3 font-medium text-white transition hover:bg-blue-700"
              >
                Create Your First Event
              </button>
            )}

          </div>
        ) : filteredEvents.length === 0 ? (

          /* No Search Results */
          <div className="mt-8 rounded-xl bg-white p-8 text-center shadow">

            <h2 className="text-xl font-semibold text-slate-900">
              No Matching Events
            </h2>

            <p className="mt-2 text-slate-500">
              No events match your search.
            </p>

            <button
              type="button"
              onClick={() => setSearch("")}
              className="mt-5 rounded-lg border border-slate-300 px-5 py-3 font-medium text-slate-700 transition hover:bg-slate-100"
            >
              Clear Search
            </button>

          </div>
        ) : (

          /* Event Cards */
          <div className="mt-8 grid gap-6 md:grid-cols-2">

            {filteredEvents.map((event) => (
              <div
                key={event.id}
                className="rounded-xl bg-white p-6 shadow transition hover:shadow-lg"
              >

                {/* Event Title */}
                <h2 className="text-2xl font-semibold text-slate-900">
                  {event.title}
                </h2>

                {/* Description */}
                <p className="mt-3 text-slate-600">
                  {event.description}
                </p>

                {/* Event Information */}
                <div className="mt-5 space-y-2 text-sm text-slate-700">

                  <p>
                    <strong>Date:</strong>{" "}
                    {event.date}
                  </p>

                  <p>
                    <strong>Time:</strong>{" "}
                    {event.time}
                  </p>

                  <p>
                    <strong>Venue:</strong>{" "}
                    {venueDisplay(event)}
                  </p>

                  <p>
                    <strong>Capacity:</strong>{" "}
                    {event.capacity} participants
                  </p>

                </div>

                {/* Action Buttons */}
                <div className="mt-5 flex flex-wrap gap-3">

                  {/* VIEW - EVERYONE */}
                  <button
                    type="button"
                    onClick={() =>
                      router.push(
                        `/events/view/${event.id}`
                      )
                    }
                    className="rounded-lg bg-slate-700 px-4 py-2 font-medium text-white transition hover:bg-slate-800"
                  >
                    View Event
                  </button>

                  {/* EDIT - ADMIN ONLY */}
                  {isAdmin && (
                    <button
                      type="button"
                      onClick={() =>
                        router.push(
                          `/events/edit/${event.id}`
                        )
                      }
                      className="rounded-lg bg-blue-600 px-4 py-2 font-medium text-white transition hover:bg-blue-700"
                    >
                      Edit Event
                    </button>
                  )}

                  {/* DELETE - ADMIN ONLY */}
                  {isAdmin && (
                    <button
                      type="button"
                      onClick={() =>
                        deleteEvent(event.id)
                      }
                      className="rounded-lg bg-red-500 px-4 py-2 font-medium text-white transition hover:bg-red-600"
                    >
                      Delete Event
                    </button>
                  )}

                </div>

              </div>
            ))}

          </div>
        )}

      </div>
    </main>
  );
}