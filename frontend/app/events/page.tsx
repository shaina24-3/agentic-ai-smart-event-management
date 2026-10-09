"use client";

import { useEffect, useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { formatTime } from "../../lib/formatTime";

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

type VenueOption = {
  id: number;
  name: string;
  location: string;
};

type EditEventForm = {
  title: string;
  description: string;
  date: string;
  time: string;
  venue_id: string;
  capacity: string;
};

function toTimeInput(value: string): string {
  const match = value.trim().match(/^(\d{1,2}):(\d{2})(?::\d{2})?\s*(AM|PM)?$/i);
  if (!match) return "";

  let hour = Number(match[1]);
  const marker = match[3]?.toUpperCase();
  if (marker) {
    if (hour < 1 || hour > 12) return "";
    hour = marker === "AM"
      ? (hour === 12 ? 0 : hour)
      : (hour === 12 ? 12 : hour + 12);
  }
  if (hour > 23 || Number(match[2]) > 59) return "";
  return `${String(hour).padStart(2, "0")}:${match[2]}`;
}

export default function MyEvents() {
  const router = useRouter();

  const [events, setEvents] = useState<Event[]>([]);
  const [search, setSearch] = useState("");
  const [isAdmin, setIsAdmin] = useState(false);
  const [loading, setLoading] = useState(true);
  const [venues, setVenues] = useState<VenueOption[]>([]);
  const [editingEvent, setEditingEvent] = useState<Event | null>(null);
  const [editForm, setEditForm] = useState<EditEventForm>({
    title: "",
    description: "",
    date: "",
    time: "",
    venue_id: "",
    capacity: "",
  });
  const [savingEvent, setSavingEvent] = useState(false);

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

        const adminUser = userData.role === "ADMIN";
        setIsAdmin(adminUser);

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

        if (adminUser) {
          const venueResponse = await fetch("http://127.0.0.1:8000/api/venues", {
            cache: "no-store",
          });
          if (venueResponse.ok) {
            setVenues(await venueResponse.json());
          }
        }
      } catch (error) {
        console.error(error);
        alert("Cannot connect to the backend.");
      } finally {
        setLoading(false);
      }
    };

    loadEvents();
  }, [router]);

  const deleteEvent = async (id: number) => {
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

    const token = localStorage.getItem("access_token");
    if (!token) {
      router.push("/");
      return;
    }

    try {
      const response = await fetch(`http://127.0.0.1:8000/api/events/${id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      const result = await response.json().catch(() => ({}));
      if (!response.ok) {
        alert(result.detail || "Failed to delete event.");
        return;
      }

      setEvents((currentEvents) => currentEvents.filter((event) => event.id !== id));
      alert("Event deleted successfully!");
    } catch (error) {
      console.error(error);
      alert("Could not connect to the backend.");
    }
  };

  const openEditEvent = (event: Event) => {
    setEditingEvent(event);
    setEditForm({
      title: event.title,
      description: event.description || "",
      date: event.date,
      time: toTimeInput(event.time),
      venue_id: String(event.venue_id || ""),
      capacity: String(event.capacity),
    });
  };

  const updateEditForm = (field: keyof EditEventForm, value: string) => {
    setEditForm((currentForm) => ({ ...currentForm, [field]: value }));
  };

  const saveEvent = async (formEvent: FormEvent<HTMLFormElement>) => {
    formEvent.preventDefault();
    if (!isAdmin || !editingEvent) return;
    if (Object.values(editForm).some((value) => !value.trim())) {
      alert("Please complete all event fields.");
      return;
    }
    if (!Number.isInteger(Number(editForm.capacity)) || Number(editForm.capacity) < 1) {
      alert("Capacity must be a positive whole number.");
      return;
    }

    const token = localStorage.getItem("access_token");
    if (!token) {
      router.push("/");
      return;
    }

    const updatedFields = {
      title: editForm.title.trim(),
      description: editForm.description.trim(),
      date: editForm.date,
      time: editForm.time,
      venue_id: Number(editForm.venue_id),
      capacity: Number(editForm.capacity),
    };

    setSavingEvent(true);
    try {
      const response = await fetch(`http://127.0.0.1:8000/api/events/${editingEvent.id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(updatedFields),
      });
      const responseData = await response.json().catch(() => ({}));

      const refreshResponse = await fetch("http://127.0.0.1:8000/api/events", {
        cache: "no-store",
      });
      if (refreshResponse.ok) {
        const refreshedEvents: Event[] = await refreshResponse.json();
        setEvents(refreshedEvents);
        const savedEvent = refreshedEvents.find((event) => event.id === editingEvent.id);
        const persisted = savedEvent &&
          savedEvent.title === updatedFields.title &&
          savedEvent.description === updatedFields.description &&
          savedEvent.date === updatedFields.date &&
          savedEvent.time === updatedFields.time &&
          Number(savedEvent.venue_id) === updatedFields.venue_id &&
          Number(savedEvent.capacity) === updatedFields.capacity;

        if (persisted) {
          setEditingEvent(null);
          alert("Event updated successfully!");
          return;
        }
      }

      if (!response.ok) {
        alert(responseData.detail || "Failed to update event.");
        return;
      }

      const selectedVenue = venues.find((venue) => venue.id === updatedFields.venue_id);
      setEvents((currentEvents) => currentEvents.map((event) =>
        event.id === editingEvent.id
          ? { ...event, ...updatedFields, venue: selectedVenue?.name, venue_name: selectedVenue?.name }
          : event
      ));
      setEditingEvent(null);
      alert("Event updated successfully!");
    } catch (error) {
      console.error(error);
      alert("Could not connect to the backend.");
    } finally {
      setSavingEvent(false);
    }
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

        {isAdmin && editingEvent && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4">
            <section
              role="dialog"
              aria-modal="true"
              aria-labelledby="edit-event-title"
              className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-xl bg-white p-6 shadow-xl"
            >
              <h2 id="edit-event-title" className="text-xl font-semibold text-slate-900">
                Edit Event
              </h2>
              <form onSubmit={saveEvent} className="mt-5 grid gap-4 sm:grid-cols-2">
                <div className="sm:col-span-2">
                  <label htmlFor="edit-event-name" className="mb-1.5 block text-sm font-medium text-slate-700">
                    Event Title
                  </label>
                  <input
                    id="edit-event-name"
                    required
                    value={editForm.title}
                    onChange={(event) => updateEditForm("title", event.target.value)}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm text-slate-900 focus:border-blue-500 focus:outline-none"
                  />
                </div>
                <div className="sm:col-span-2">
                  <label htmlFor="edit-event-description" className="mb-1.5 block text-sm font-medium text-slate-700">
                    Description
                  </label>
                  <textarea
                    id="edit-event-description"
                    rows={3}
                    value={editForm.description}
                    onChange={(event) => updateEditForm("description", event.target.value)}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm text-slate-900 focus:border-blue-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label htmlFor="edit-event-date" className="mb-1.5 block text-sm font-medium text-slate-700">
                    Date
                  </label>
                  <input
                    id="edit-event-date"
                    type="date"
                    required
                    value={editForm.date}
                    onChange={(event) => updateEditForm("date", event.target.value)}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm text-slate-900 focus:border-blue-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label htmlFor="edit-event-time" className="mb-1.5 block text-sm font-medium text-slate-700">
                    Time
                  </label>
                  <input
                    id="edit-event-time"
                    type="time"
                    required
                    value={editForm.time}
                    onChange={(event) => updateEditForm("time", event.target.value)}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm text-slate-900 focus:border-blue-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label htmlFor="edit-event-venue" className="mb-1.5 block text-sm font-medium text-slate-700">
                    Venue
                  </label>
                  <select
                    id="edit-event-venue"
                    required
                    value={editForm.venue_id}
                    onChange={(event) => updateEditForm("venue_id", event.target.value)}
                    className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-900 focus:border-blue-500 focus:outline-none"
                  >
                    <option value="" disabled>Select a venue</option>
                    {venues.map((venue) => (
                      <option key={venue.id} value={venue.id}>
                        {venue.name} · {venue.location}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label htmlFor="edit-event-capacity" className="mb-1.5 block text-sm font-medium text-slate-700">
                    Capacity
                  </label>
                  <input
                    id="edit-event-capacity"
                    type="number"
                    min="1"
                    required
                    value={editForm.capacity}
                    onChange={(event) => updateEditForm("capacity", event.target.value)}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm text-slate-900 focus:border-blue-500 focus:outline-none"
                  />
                </div>
                <div className="flex justify-end gap-3 pt-2 sm:col-span-2">
                  <button
                    type="button"
                    onClick={() => setEditingEvent(null)}
                    disabled={savingEvent}
                    className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={savingEvent}
                    className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
                  >
                    {savingEvent ? "Saving..." : "Save Changes"}
                  </button>
                </div>
              </form>
            </section>
          </div>
        )}

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
                  <p className="mt-3 text-slate-900">
                  {event.description}
                </p>

                {/* Event Information */}
                <div className="mt-5 space-y-2 text-sm text-slate-900">

                  <p>
                    <strong>Date:</strong>{" "}
                    {event.date}
                  </p>

                  <p>
                    <strong>Time:</strong>{" "}
                    {formatTime(event.time)}
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

                  {/* EDIT - ADMIN ONLY */}
                  {isAdmin && (
                    <button
                      type="button"
                      onClick={() => openEditEvent(event)}
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