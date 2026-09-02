export default function Dashboard() {
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
          
          <div className="rounded-xl bg-white p-6 shadow">
            <h2 className="text-xl font-semibold">My Events</h2>
            <p className="mt-2 text-slate-500">
              View and manage your events.
            </p>
          </div>

          <div className="rounded-xl bg-white p-6 shadow">
            <h2 className="text-xl font-semibold">Create Event</h2>
            <p className="mt-2 text-slate-500">
              Create a new event.
            </p>
          </div>

          <div className="rounded-xl bg-white p-6 shadow">
            <h2 className="text-xl font-semibold">Upcoming Events</h2>
            <p className="mt-2 text-slate-500">
              Check your upcoming events.
            </p>
          </div>

        </div>
      </div>
    </main>
  );
}