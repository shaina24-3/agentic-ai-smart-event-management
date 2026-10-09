"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { formatDateTime } from "../../../lib/formatTime";

type RegistrationRecord = {
  id: number;
  user_email: string;
  event_title: string;
  registration_date: string | null;
  status: "CONFIRMED" | "CANCELLED";
};

type EventRecord = {
  id: number;
  title: string;
  capacity: number;
};

type EventRegistrationStatus = {
  status: "CONFIRMED" | "CANCELLED";
};

type EventCapacitySummary = {
  event_id: number;
  event_title: string;
  confirmed_bookings: number;
  leftover_capacity: number;
};

async function fetchEventCapacitySummaries(token: string): Promise<EventCapacitySummary[]> {
  const eventsResponse = await fetch("http://127.0.0.1:8000/api/events");
  if (!eventsResponse.ok) {
    throw new Error("Could not load events.");
  }

  const events: EventRecord[] = await eventsResponse.json();
  return Promise.all(
    events.map(async (event) => {
      const registrationsResponse = await fetch(
        `http://127.0.0.1:8000/api/events/${event.id}/registrations`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (!registrationsResponse.ok) {
        throw new Error("Could not load event registrations.");
      }

      const eventRegistrations: EventRegistrationStatus[] = await registrationsResponse.json();
      const confirmedBookings = eventRegistrations.filter(
        (registration) => registration.status === "CONFIRMED"
      ).length;

      return {
        event_id: event.id,
        event_title: event.title,
        confirmed_bookings: confirmedBookings,
        leftover_capacity: Math.max(event.capacity - confirmedBookings, 0),
      };
    })
  );
}

export default function AdminRegistrationsPage() {
  const router = useRouter();
  const [registrations, setRegistrations] = useState<RegistrationRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [updatingId, setUpdatingId] = useState<number | null>(null);
  const [message, setMessage] = useState("");
  const [eventSummaries, setEventSummaries] = useState<EventCapacitySummary[]>([]);
  const [loadingSummaries, setLoadingSummaries] = useState(true);
  const [summaryMessage, setSummaryMessage] = useState("");

  const loadRegistrations = useCallback(async () => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      router.push("/");
      return;
    }

    try {
      const response = await fetch("http://127.0.0.1:8000/api/admin/registrations", {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.status === 403) {
        router.push("/dashboard");
        return;
      }
      if (!response.ok) {
        const result = await response.json();
        setMessage(result.detail || "Could not load registrations.");
        return;
      }

      setRegistrations(await response.json());
      setMessage("");
      setLoadingSummaries(true);
      try {
        setEventSummaries(await fetchEventCapacitySummaries(token));
        setSummaryMessage("");
      } catch {
        setSummaryMessage("Could not load event capacity summary.");
      } finally {
        setLoadingSummaries(false);
      }
    } catch {
      setMessage("Could not connect to the backend.");
    } finally {
      setLoading(false);
    }
  }, [router]);

  useEffect(() => {
    let active = true;

    const initializeRegistrations = async () => {
      const token = localStorage.getItem("access_token");
      if (!token) {
        router.push("/");
        return;
      }

      try {
        const response = await fetch("http://127.0.0.1:8000/api/admin/registrations", {
          headers: { Authorization: `Bearer ${token}` },
        });

        if (response.status === 403) {
          router.push("/dashboard");
          return;
        }
        if (!response.ok) {
          const result = await response.json();
          if (active) setMessage(result.detail || "Could not load registrations.");
          return;
        }

        const data = await response.json();
        if (active) {
          setRegistrations(data);
          setMessage("");
        }
        try {
          const summaries = await fetchEventCapacitySummaries(token);
          if (active) {
            setEventSummaries(summaries);
            setSummaryMessage("");
          }
        } catch {
          if (active) setSummaryMessage("Could not load event capacity summary.");
        } finally {
          if (active) setLoadingSummaries(false);
        }
      } catch {
        if (active) setMessage("Could not connect to the backend.");
      } finally {
        if (active) setLoading(false);
      }
    };

    void initializeRegistrations();
    return () => {
      active = false;
    };
  }, [router]);

  const updateRegistration = async (registration: RegistrationRecord) => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      router.push("/");
      return;
    }

    const action = registration.status === "CONFIRMED" ? "cancel" : "restore";
    setUpdatingId(registration.id);
    setMessage("");

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/api/admin/registrations/${registration.id}/${action}`,
        {
          method: "PUT",
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      const result = await response.json();

      if (!response.ok) {
        setMessage(result.detail || "Could not update this registration.");
        return;
      }

      setMessage(
        action === "cancel" ? "Registration cancelled." : "Registration restored."
      );
      await loadRegistrations();
    } catch {
      setMessage("Could not connect to the backend.");
    } finally {
      setUpdatingId(null);
    }
  };

  return (
    <main className="mx-auto max-w-6xl space-y-5">
      <header>
        <h1 className="text-2xl font-semibold text-slate-900">Registrations</h1>
        <p className="mt-1 text-sm text-slate-500">
          Review and manage event registrations.
        </p>
      </header>

      {message && (
        <p role="status" className="text-sm text-slate-600">
          {message}
        </p>
      )}

      <section className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
        <h2 className="border-b border-slate-200 px-4 py-3 text-sm font-semibold text-slate-900">
          Event Capacity &amp; Bookings Summary
        </h2>
        {summaryMessage && (
          <p role="status" className="px-4 py-3 text-sm text-slate-600">
            {summaryMessage}
          </p>
        )}
        <table className="w-full min-w-[560px] text-left text-sm">
          <thead className="border-b border-slate-200 bg-slate-50 text-xs font-semibold uppercase text-slate-500">
            <tr>
              <th scope="col" className="px-4 py-3">Event Title</th>
              <th scope="col" className="px-4 py-3">Registered Users</th>
              <th scope="col" className="px-4 py-3">Leftover Capacity</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 text-slate-700">
            {loadingSummaries ? (
              <tr>
                <td colSpan={3} className="px-4 py-8 text-center text-slate-500">
                  Loading event summary...
                </td>
              </tr>
            ) : eventSummaries.length === 0 ? (
              <tr>
                <td colSpan={3} className="px-4 py-8 text-center text-slate-500">
                  No events found.
                </td>
              </tr>
            ) : (
              eventSummaries.map((summary) => (
                <tr key={summary.event_id} className="hover:bg-slate-50">
                  <td className="px-4 py-3">{summary.event_title}</td>
                  <td className="px-4 py-3">{summary.confirmed_bookings}</td>
                  <td className="px-4 py-3">{summary.leftover_capacity}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </section>

      <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
        <table className="w-full min-w-[760px] text-left text-sm">
          <thead className="border-b border-slate-200 bg-slate-50 text-xs font-semibold uppercase text-slate-500">
            <tr>
              <th scope="col" className="px-4 py-3">Registration ID</th>
              <th scope="col" className="px-4 py-3">User/Email</th>
              <th scope="col" className="px-4 py-3">Event Title</th>
              <th scope="col" className="px-4 py-3">Date</th>
              <th scope="col" className="px-4 py-3">Status</th>
              <th scope="col" className="px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 text-slate-700">
            {loading ? (
              <tr>
                <td colSpan={6} className="px-4 py-10 text-center text-slate-500">
                  Loading registrations...
                </td>
              </tr>
            ) : registrations.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-10 text-center text-slate-500">
                  No registrations found.
                </td>
              </tr>
            ) : (
              registrations.map((registration) => (
                <tr key={registration.id} className="hover:bg-slate-50">
                  <td className="whitespace-nowrap px-4 py-3">{registration.id}</td>
                  <td className="px-4 py-3">{registration.user_email}</td>
                  <td className="px-4 py-3">{registration.event_title}</td>
                  <td className="whitespace-nowrap px-4 py-3">
                    {formatDateTime(registration.registration_date)}
                  </td>
                  <td className="px-4 py-3">{registration.status}</td>
                  <td className="px-4 py-3">
                    <button
                      type="button"
                      onClick={() => void updateRegistration(registration)}
                      disabled={updatingId !== null}
                      className={`whitespace-nowrap font-medium disabled:cursor-not-allowed disabled:opacity-50 ${
                        registration.status === "CONFIRMED"
                          ? "text-red-600 hover:text-red-800"
                          : "text-green-700 hover:text-green-900"
                      }`}
                    >
                      {updatingId === registration.id
                        ? "Updating..."
                        : registration.status === "CONFIRMED"
                          ? "Cancel Registration"
                          : "Restore Registration"}
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </main>
  );
}