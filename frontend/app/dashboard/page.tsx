"use client";

import { useEffect, useEffectEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { formatTime } from "../../lib/formatTime";
import { API_BASE_URL } from "@/lib/api";

type Event = {
  id: number;
  title: string;
  description?: string;
  date: string;
  time?: string;
  venue_id?: number;
  capacity: number;
};

type Registration = {
  id: number;
  event_id: number;
  status: string;
  event?: Event;
};

export default function Dashboard() {
  const router = useRouter();

  const [events, setEvents] = useState<Event[]>([]);
  const [registrations, setRegistrations] = useState<Registration[]>([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");

  const [userEmail, setUserEmail] = useState("");
  const [userName, setUserName] = useState("");
  const [isAdmin, setIsAdmin] = useState(false);

  const loadDashboard = useEffectEvent(async () => {
    const token = localStorage.getItem("access_token");

    if (!token) {
      router.push("/");
      return;
    }

    try {
      // Get the actual logged-in user from backend
      const userResponse = await fetch(
        `${API_BASE_URL}/api/auth/me`,
        {
          method: "GET",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          cache: "no-store",
        }
      );

      if (!userResponse.ok) {
        localStorage.removeItem("access_token");
        localStorage.removeItem("userEmail");
        localStorage.removeItem("userName");
        localStorage.removeItem("rememberMe");

        router.push("/");
        return;
      }

      const userData = await userResponse.json();

      console.log("CURRENT USER FROM BACKEND:", userData);
      console.log("CURRENT USER ROLE:", userData.role);

      const role = String(userData.role || "").toUpperCase();

      setUserEmail(userData.email || "");
      setUserName(userData.name || "");
      setIsAdmin(role === "ADMIN");

      // Load events
      const eventsResponse = await fetch(
        `${API_BASE_URL}/api/events`,
        {
          cache: "no-store",
        }
      );

      if (eventsResponse.ok) {
        const eventsData = await eventsResponse.json();
        setEvents(eventsData);
      }

      // Load current user's registrations
      const registrationResponse = await fetch(
        `${API_BASE_URL}/api/registrations/me`,
        {
          method: "GET",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          cache: "no-store",
        }
      );

      if (registrationResponse.ok) {
        const registrationData = await registrationResponse.json();
        setRegistrations(registrationData);
      }
    } catch (error) {
      console.error("Dashboard error:", error);
      setMessage("Cannot connect to the backend.");
    } finally {
      setLoading(false);
    }
  });

  useEffect(() => {
    // The loader updates dashboard state after external requests complete.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void loadDashboard();
  }, []);

  const handleRegister = async (eventId: number) => {
    const token = localStorage.getItem("access_token");

    if (!token) {
      router.push("/");
      return;
    }

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/events/${eventId}/register`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      const data = await response.json();

      if (!response.ok) {
        setMessage(
          typeof data.detail === "string"
            ? data.detail
            : "Registration failed."
        );
        return;
      }

      setRegistrations((previous) => {
        if (previous.some(
          (registration) =>
            registration.event_id === eventId &&
            registration.status === "CONFIRMED"
        )) {
          return previous;
        }

        return [
          ...previous,
          {
            id: Date.now(),
            event_id: eventId,
            status: "CONFIRMED",
          },
        ];
      });
      setMessage("Successfully registered for the event!");

      try {
        const registrationResponse = await fetch(
          `${API_BASE_URL}/api/registrations/me`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
              "Content-Type": "application/json",
            },
            cache: "no-store",
          }
        );

        if (registrationResponse.ok) {
          setRegistrations(await registrationResponse.json());
        }
      } catch (refreshError) {
        console.error("Registration succeeded, but registrations could not be refreshed.", refreshError);
      }
    } catch (error) {
      console.error(error);
      setMessage("Cannot connect to the backend.");
    }
  };

  const handleCancel = async (eventId: number) => {
    const token = localStorage.getItem("access_token");

    if (!token) {
      router.push("/");
      return;
    }

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/events/${eventId}/register`,
        {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      const data = await response.json();

      if (!response.ok) {
        setMessage(
          typeof data.detail === "string"
            ? data.detail
            : "Cancellation failed."
        );
        return;
      }

      setRegistrations((previous) =>
        previous.map((registration) =>
          registration.event_id === eventId && registration.status === "CONFIRMED"
            ? { ...registration, status: "CANCELLED" }
            : registration
        )
      );
      setMessage("Registration cancelled successfully!");

      try {
        const registrationResponse = await fetch(
          `${API_BASE_URL}/api/registrations/me`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
              "Content-Type": "application/json",
            },
            cache: "no-store",
          }
        );

        if (registrationResponse.ok) {
          setRegistrations(await registrationResponse.json());
        }
      } catch (refreshError) {
        console.error("Cancellation succeeded, but registrations could not be refreshed.", refreshError);
      }
    } catch (error) {
      console.error(error);
      setMessage("Cannot connect to the backend.");
    }
  };

  const isRegistered = (eventId: number) => {
    return registrations.some(
      (registration) =>
        registration.event_id === eventId &&
        registration.status === "CONFIRMED"
    );
  };

  const today = new Date().toISOString().split("T")[0];

  const upcomingEvents = events
    .filter((event) => event.date >= today)
    .sort((a, b) => a.date.localeCompare(b.date))
    .slice(0, 3);

  const registeredEvents = registrations.filter(
    (registration) => registration.status === "CONFIRMED"
  );

  return (
    <main className="min-h-screen bg-slate-100 px-4 py-8 md:px-6">
      <div className="mx-auto max-w-7xl">

        <section
          style={{ backgroundColor: "#6d28d9" }}
          className="flex flex-col gap-6 rounded-2xl bg-purple-700 px-6 py-8 text-white shadow-sm sm:flex-row sm:items-center sm:justify-between md:px-8"
        >
          <div>
            {isAdmin && (
              <p className="text-sm font-medium text-slate-300">Administration</p>
            )}
            <h1 className="mt-2 text-2xl font-semibold md:text-3xl">
              {isAdmin
                ? "Admin Control Panel"
                : `Welcome, ${userName || (userEmail ? userEmail.split("@")[0] : "User")}`}
            </h1>
            <p className="mt-2 text-sm text-slate-300">
              {isAdmin
                ? "Manage events, registrations, and attendees."
                : "Manage your events and registrations in one place."}
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

        {/* Message */}
        {message && (
          <div className="mt-6 rounded-lg border border-blue-200 bg-blue-50 p-4 text-blue-700">
            {message}
          </div>
        )}

        {/* Loading */}
        {loading ? (
          <div className="mt-8 rounded-xl bg-white p-8 text-center shadow">
            <p className="text-slate-600">
              Loading dashboard...
            </p>
          </div>
        ) : (
          <>
            {/* Dashboard Cards */}
            <div className="mt-8 grid gap-6 md:grid-cols-3">

              {/* Total Events */}
              <button
                onClick={() => router.push("/events")}
                className="rounded-xl bg-white p-6 text-left shadow transition hover:shadow-lg"
              >
                <h2 className="text-xl font-semibold text-slate-900">
                  Total Events
                </h2>

                <p className="mt-4 text-4xl font-bold text-blue-600">
                  {events.length}
                </p>

                <p className="mt-2 text-slate-500">
                  View all available events.
                </p>
              </button>

              {/* Registered Events */}
              <button
                onClick={() =>
                  document
                    .getElementById("registered-events")
                    ?.scrollIntoView({
                      behavior: "smooth",
                    })
                }
                className="rounded-xl bg-white p-6 text-left shadow transition hover:shadow-lg"
              >
                <h2 className="text-xl font-semibold text-slate-900">
                  My Registered Events
                </h2>

                <p className="mt-4 text-4xl font-bold text-green-600">
                  {registeredEvents.length}
                </p>

                <p className="mt-2 text-slate-500">
                  Events you have registered for.
                </p>
              </button>

              {/* Admin-only card */}
              {isAdmin && (
                <button
                  onClick={() => router.push("/create")}
                  className="rounded-xl bg-white p-6 text-left shadow transition hover:shadow-lg"
                >
                  <h2 className="text-xl font-semibold text-slate-900">
                    Create Event
                  </h2>

                  <p className="mt-4 text-4xl font-bold text-blue-600">
                    +
                  </p>

                  <p className="mt-2 text-slate-500">
                    Create a new event.
                  </p>
                </button>
              )}

            </div>

            {/* Upcoming Events */}
            <section
              id="upcoming-events"
              className="mt-8 rounded-xl bg-white p-6 shadow"
            >
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold text-slate-900">
                  Upcoming Events
                </h2>

                <button
                  onClick={() => router.push("/events")}
                  className="text-sm font-semibold text-blue-600 hover:text-blue-800"
                >
                  View all
                </button>
              </div>

              {upcomingEvents.length > 0 ? (
                <div className="mt-5 grid gap-4 md:grid-cols-3">
                  {upcomingEvents.map((event) => {
                    const registered = isRegistered(event.id);

                    return (
                      <div
                        key={event.id}
                        className="rounded-lg border border-slate-200 p-4"
                      >
                        <h3 className="font-semibold text-slate-900">
                          {event.title}
                        </h3>

                        <p className="mt-2 text-sm text-slate-500">
                          {event.date}
                          {event.time ? ` • ${formatTime(event.time)}` : ""}
                        </p>

                        <p className="mt-1 text-sm text-slate-500">
                          Capacity: {event.capacity}
                        </p>

                        <div className="mt-4">
                          {registered ? (
                            <button
                              onClick={() => handleCancel(event.id)}
                              className="w-full rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-700"
                            >
                              Cancel Registration
                            </button>
                          ) : (
                            <button
                              onClick={() => handleRegister(event.id)}
                              className="w-full rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700"
                            >
                              Register
                            </button>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <p className="mt-4 text-slate-500">
                  No upcoming events.
                </p>
              )}
            </section>

            {/* Registered Events */}
            {!isAdmin && (
              <section
                id="registered-events"
                className="mt-8 rounded-xl bg-white p-6 shadow"
              >
                <h2 className="text-xl font-semibold text-slate-900">
                  My Registered Events
                </h2>

                {registeredEvents.length > 0 ? (
                  <div className="mt-5 space-y-4">
                    {registeredEvents.map((registration) => {
                      const event = events.find(
                        (item) =>
                          item.id === registration.event_id
                      );

                      return (
                        <div
                          key={registration.id}
                          className="flex flex-col justify-between gap-4 rounded-lg border border-slate-200 p-4 md:flex-row md:items-center"
                        >
                          <div>
                            <h3 className="font-semibold text-slate-900">
                              {event?.title ||
                                `Event #${registration.event_id}`}
                            </h3>

                            {event && (
                              <p className="mt-1 text-sm text-slate-500">
                                {event.date}
                                {event.time
                                  ? ` • ${formatTime(event.time)}`
                                  : ""}
                              </p>
                            )}

                            <p className="mt-1 text-sm font-medium text-green-600">
                              Registration Confirmed
                            </p>
                          </div>

                          <button
                            onClick={() =>
                              handleCancel(registration.event_id)
                            }
                            className="rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-700"
                          >
                            Cancel Registration
                          </button>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <p className="mt-4 text-slate-500">
                    You have not registered for any events yet.
                  </p>
                )}
              </section>
            )}
          </>
        )}
      </div>
    </main>
  );
}