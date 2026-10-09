"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { formatDateTime } from "../../lib/formatTime";
import { API_BASE_URL } from "@/lib/api";

type PersonalRegistration = {
  id: number;
  event_id: number;
  event_title: string;
  event_date: string | null;
  registration_date: string | null;
  status: "CONFIRMED" | "CANCELLED";
};

async function addEventDates(
  registrations: Omit<PersonalRegistration, "event_date">[]
): Promise<PersonalRegistration[]> {
  const eventIds = Array.from(new Set(registrations.map((registration) => registration.event_id)));
  const eventDateEntries = await Promise.all(
    eventIds.map(async (eventId) => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/events/${eventId}`, {
          cache: "no-store",
        });
        if (!response.ok) return [eventId, null] as const;
        const event: { date: string } = await response.json();
        return [eventId, event.date] as const;
      } catch {
        return [eventId, null] as const;
      }
    })
  );
  const datesByEventId = new Map(eventDateEntries);

  return registrations.map((registration) => ({
    ...registration,
    event_date: datesByEventId.get(registration.event_id) ?? null,
  }));
}

export default function UserRegistrationsPage() {
  const router = useRouter();
  const [registrations, setRegistrations] = useState<PersonalRegistration[]>([]);
  const [loading, setLoading] = useState(true);
  const [updatingId, setUpdatingId] = useState<number | null>(null);
  const [message, setMessage] = useState("");

  useEffect(() => {
    let active = true;

    const loadRegistrations = async () => {
      const token = localStorage.getItem("access_token");
      if (!token) {
        router.push("/");
        return;
      }

      try {
        const response = await fetch(`${API_BASE_URL}/api/user/registrations`, {
          headers: { Authorization: `Bearer ${token}` },
          cache: "no-store",
        });
        if (response.status === 401) {
          router.push("/");
          return;
        }
        if (!response.ok) {
          const result = await response.json();
          if (active) setMessage(result.detail || "Could not load your registrations.");
          return;
        }

        const data: Omit<PersonalRegistration, "event_date">[] = await response.json();
        const registrationsWithDates = await addEventDates(data);
        if (active) {
          setRegistrations(registrationsWithDates);
          setMessage("");
        }
      } catch {
        if (active) setMessage("Could not connect to the backend.");
      } finally {
        if (active) setLoading(false);
      }
    };

    void loadRegistrations();
    return () => {
      active = false;
    };
  }, [router]);

  const refreshRegistrations = async () => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      router.push("/");
      return;
    }

    const response = await fetch(`${API_BASE_URL}/api/user/registrations`, {
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    });
    if (!response.ok) {
      throw new Error("Could not refresh your registrations.");
    }
    const data: Omit<PersonalRegistration, "event_date">[] = await response.json();
    setRegistrations(await addEventDates(data));
  };

  const cancelRegistration = async (registration: PersonalRegistration) => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      router.push("/");
      return;
    }

    setUpdatingId(registration.id);
    setMessage("");
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/events/${registration.event_id}/register`,
        {
          method: "DELETE",
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      const result = await response.json();
      if (!response.ok) {
        setMessage(result.detail || "Could not cancel this registration.");
        return;
      }

      await refreshRegistrations();
      setMessage("Registration cancelled.");
    } catch {
      setMessage("Could not connect to the backend.");
    } finally {
      setUpdatingId(null);
    }
  };

  const today = new Date();
  const todayDate = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`;

  return (
    <main className="mx-auto max-w-6xl space-y-5">
      <header>
        <h1 className="text-2xl font-semibold text-slate-900">My Registrations</h1>
        <p className="mt-1 text-sm text-slate-500">
          View and manage your event registrations.
        </p>
      </header>

      {message && (
        <p role="status" className="text-sm text-slate-600">
          {message}
        </p>
      )}

      <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
        <table className="w-full min-w-[700px] text-left text-sm">
          <thead className="border-b border-slate-200 bg-slate-50 text-xs font-semibold uppercase text-slate-500">
            <tr>
              <th scope="col" className="px-4 py-3">Event Title</th>
              <th scope="col" className="px-4 py-3">Registration Date</th>
              <th scope="col" className="px-4 py-3">Status</th>
              <th scope="col" className="px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 text-slate-700">
            {loading ? (
              <tr>
                <td colSpan={4} className="px-4 py-10 text-center text-slate-500">
                  Loading registrations...
                </td>
              </tr>
            ) : registrations.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-4 py-10 text-center text-slate-500">
                  You have no registrations.
                </td>
              </tr>
            ) : (
              registrations.map((registration) => (
                <tr key={registration.id} className="hover:bg-slate-50">
                  <td className="px-4 py-3">{registration.event_title}</td>
                  <td className="whitespace-nowrap px-4 py-3">
                    {formatDateTime(registration.registration_date)}
                  </td>
                  <td className="px-4 py-3">{registration.status}</td>
                  <td className="px-4 py-3">
                    {registration.status === "CANCELLED" ? (
                      <span className="text-slate-500">Cancelled</span>
                    ) : registration.event_date && registration.event_date < todayDate ? (
                      <span className="text-slate-500">Event Completed</span>
                    ) : registration.event_date ? (
                      <button
                        type="button"
                        onClick={() => void cancelRegistration(registration)}
                        disabled={updatingId !== null}
                        className="whitespace-nowrap font-medium text-red-600 hover:text-red-800 disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        {updatingId === registration.id
                          ? "Cancelling..."
                          : "Cancel Registration"}
                      </button>
                    ) : (
                      <span className="text-slate-500">Event date unavailable</span>
                    )}
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