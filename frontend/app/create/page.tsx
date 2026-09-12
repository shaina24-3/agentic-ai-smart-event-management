"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

type FormData = {
  title: string;
  description: string;
  date: string;
  time: string;
  venue: string;
  capacity: string;
};

export default function CreateEvent() {
  const router = useRouter();

  const [form, setForm] = useState<FormData>({
    title: "",
    description: "",
    date: "",
    time: "",
    venue: "",
    capacity: "",
  });

  const updateField = (
    field: keyof FormData,
    value: string
  ) => {
    setForm((previousForm) => ({
      ...previousForm,
      [field]: value,
    }));
  };

  const handleSubmit = (
    e: React.FormEvent<HTMLFormElement>
  ) => {
    e.preventDefault();

    if (
      !form.title.trim() ||
      !form.description.trim() ||
      !form.date.trim() ||
      !form.time.trim() ||
      !form.venue.trim() ||
      !form.capacity.trim()
    ) {
      alert("Please fill in all fields.");
      return;
    }

    if (Number(form.capacity) <= 0) {
      alert("Capacity must be greater than 0.");
      return;
    }

    const savedEvents = localStorage.getItem("events");

    const existingEvents = savedEvents
      ? JSON.parse(savedEvents)
      : [];

    const newEvent = {
      id: Date.now(),
      title: form.title.trim(),
      description: form.description.trim(),
      date: form.date,
      time: form.time,
      venue: form.venue.trim(),
      capacity: Number(form.capacity),
    };

    const updatedEvents = [
      ...existingEvents,
      newEvent,
    ];

    localStorage.setItem(
      "events",
      JSON.stringify(updatedEvents)
    );

    alert("Event created successfully!");

    router.push("/events");
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

            <input
              id="venue"
              type="text"
              placeholder="Enter venue"
              value={form.venue}
              onChange={(e) =>
                updateField("venue", e.target.value)
              }
              className="w-full rounded-lg border border-slate-300 px-4 py-3 text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
            />
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
              onClick={() => router.push("/dashboard")}
              className="w-1/2 rounded-lg border border-slate-300 py-3 font-semibold text-slate-700 transition hover:bg-slate-100"
            >
              Cancel
            </button>

            {/* Create Event */}
            <button
              type="submit"
              className="w-1/2 rounded-lg bg-blue-600 py-3 font-semibold text-white transition hover:bg-blue-700"
            >
              Create Event
            </button>

          </div>

        </form>
      </div>
    </main>
  );
}