"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

type FormData = {
  title: string;
  description: string;
  date: string;
  time: string;
  venue_id: string;
  capacity: string;
};

type Venue = {
  id: number;
  name: string;
  capacity: number;
  location: string;
};

export default function CreateEvent() {
  const router = useRouter();

  const [form, setForm] = useState<FormData>({
    title: "",
    description: "",
    date: "",
    time: "",
    venue_id: "",
    capacity: "",
  });

  const [venues, setVenues] = useState<Venue[]>([]);
  const [loadingVenues, setLoadingVenues] = useState(true);

  // Load venues from backend
  useEffect(() => {
    const loadVenues = async () => {
      setLoadingVenues(true);

      try {
        const url =
          form.date && form.time
            ? `http://127.0.0.1:8000/api/venues/available?date=${encodeURIComponent(form.date)}&time=${encodeURIComponent(form.time)}`
            : "http://127.0.0.1:8000/api/venues";

        const response = await fetch(url);

        const data = await response.json();

        if (!response.ok) {
          alert(
            typeof data.detail === "string"
              ? data.detail
              : "Failed to load venues."
          );
          return;
        }

        setVenues(data);

        if (
          form.venue_id &&
          !data.some(
            (venue: Venue) => venue.id === Number(form.venue_id)
          )
        ) {
          setForm((previousForm) => ({
            ...previousForm,
            venue_id: "",
          }));
        }
      } catch (error) {
        console.error(error);
        alert("Cannot connect to the backend.");
      } finally {
        setLoadingVenues(false);
      }
    };

    loadVenues();
  }, [form.date, form.time, form.venue_id]);

  const updateField = (
    field: keyof FormData,
    value: string
  ) => {
    setForm((previousForm) => ({
      ...previousForm,
      [field]: value,
    }));
  };

  const handleSubmit = async (
    e: React.FormEvent<HTMLFormElement>
  ) => {
    e.preventDefault();

    if (
      !form.title.trim() ||
      !form.description.trim() ||
      !form.date.trim() ||
      !form.time.trim() ||
      !form.venue_id.trim() ||
      !form.capacity.trim()
    ) {
      alert("Please fill in all fields.");
      return;
    }

    if (Number(form.capacity) <= 0) {
      alert("Capacity must be greater than 0.");
      return;
    }

    const token = localStorage.getItem("access_token");

    if (!token) {
      alert("Please login first.");
      router.push("/");
      return;
    }

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/api/events",
        {
          method: "POST",

          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },

          body: JSON.stringify({
            title: form.title.trim(),
            description: form.description.trim(),
            date: form.date,
            time: form.time,
            venue_id: Number(form.venue_id),
            capacity: Number(form.capacity),
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        if (Array.isArray(data.detail)) {
          const messages = data.detail
            .map((error: any) => {
              return error.msg || "Validation error";
            })
            .join("\n");

          alert(messages);
        } else {
          alert(
            data.detail || "Failed to create event."
          );
        }

        return;
      }

      alert("Event created successfully!");

      router.push("/events");
    } catch (error) {
      console.error(error);
      alert("Cannot connect to the backend.");
    }
  };

  return (
    <main className="min-h-screen bg-slate-100 px-4 py-8 md:px-6">
      <div className="mx-auto max-w-3xl">

        {/* Back to Dashboard */}
        <button
          type="button"
          onClick={() => router.push("/dashboard")}
          className="mb-5 text-sm font-medium text-blue-600 hover:text-blue-800"
        >
          ← Back to Dashboard
        </button>

        {/* Page Heading */}
        <h1 className="text-3xl font-bold text-slate-900">
          Create Event
        </h1>

        <p className="mt-2 text-slate-600">
          Create a new event by entering the details below.
        </p>

        {/* Event Form */}
        <form
          onSubmit={handleSubmit}
          className="mt-8 space-y-6 rounded-2xl bg-white p-8 shadow-lg"
        >

          {/* Event Title */}
          <div>
            <label
              htmlFor="title"
              className="mb-2 block text-sm font-medium text-slate-700"
            >
              Event Title
            </label>

            <input
              id="title"
              type="text"
              placeholder="Enter event title"
              value={form.title}
              onChange={(e) =>
                updateField("title", e.target.value)
              }
              className="w-full rounded-lg border border-slate-300 px-4 py-3 text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
            />
          </div>

          {/* Description */}
          <div>
            <label
              htmlFor="description"
              className="mb-2 block text-sm font-medium text-slate-700"
            >
              Description
            </label>

            <textarea
              id="description"
              rows={4}
              placeholder="Enter event description"
              value={form.description}
              onChange={(e) =>
                updateField(
                  "description",
                  e.target.value
                )
              }
              className="w-full rounded-lg border border-slate-300 px-4 py-3 text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
            />
          </div>

          {/* Date and Time */}
          <div className="grid gap-6 md:grid-cols-2">

            {/* Event Date */}
            <div>
              <label
                htmlFor="date"
                className="mb-2 block text-sm font-medium text-slate-700"
              >
                Event Date
              </label>

              <input
                id="date"
                type="date"
                value={form.date}
                onChange={(e) =>
                  updateField("date", e.target.value)
                }
                className="w-full rounded-lg border border-slate-300 px-4 py-3 text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
              />
            </div>

            {/* Event Time */}
            <div>
              <label
                htmlFor="time"
                className="mb-2 block text-sm font-medium text-slate-700"
              >
                Event Time
              </label>

              <input
                id="time"
                type="time"
                value={form.time}
                onChange={(e) =>
                  updateField("time", e.target.value)
                }
                className="w-full rounded-lg border border-slate-300 px-4 py-3 text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
              />
            </div>

          </div>

          {/* Venue */}
          <div>
            <label
              htmlFor="venue"
              className="mb-2 block text-sm font-medium text-slate-700"
            >
              Venue
            </label>

            <select
              id="venue"
              value={form.venue_id}
              onChange={(e) =>
                updateField(
                  "venue_id",
                  e.target.value
                )
              }
              disabled={loadingVenues}
              className="w-full rounded-lg border border-slate-300 bg-white px-4 py-3 text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
            >
              <option value="">
                {loadingVenues
                  ? "Loading venues..."
                  : "Select a venue"}
              </option>

              {venues.map((venue) => (
                <option
                  key={venue.id}
                  value={venue.id}
                >
                  {venue.name} - {venue.location}
                </option>
              ))}
            </select>

            {!loadingVenues && venues.length === 0 && (
              <p className="mt-2 text-sm text-red-500">
                No venues available.
              </p>
            )}
          </div>

          {/* Capacity */}
          <div>
            <label
              htmlFor="capacity"
              className="mb-2 block text-sm font-medium text-slate-700"
            >
              Capacity
            </label>

            <input
              id="capacity"
              type="number"
              min="1"
              placeholder="Enter maximum participants"
              value={form.capacity}
              onChange={(e) =>
                updateField(
                  "capacity",
                  e.target.value
                )
              }
              className="w-full rounded-lg border border-slate-300 px-4 py-3 text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
            />
          </div>

          {/* Buttons */}
          <div className="flex gap-4 pt-4">

            {/* Cancel */}
            <button
              type="button"
              onClick={() =>
                router.push("/dashboard")
              }
              className="w-1/2 rounded-lg border border-slate-300 py-3 font-semibold text-slate-700 transition hover:bg-slate-100"
            >
              Cancel
            </button>

            {/* Create Event */}
            <button
              type="submit"
              disabled={loadingVenues}
              className="w-1/2 rounded-lg bg-blue-600 py-3 font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Create Event
            </button>

          </div>

        </form>
      </div>
    </main>
  );
}