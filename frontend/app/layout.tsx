"use client";

import "./globals.css";

import { usePathname, useRouter } from "next/navigation";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const pathname = usePathname();
  const router = useRouter();

  const publicPath =
    pathname === "/" ||
    pathname.startsWith("/register");

  const handleLogout = () => {
    const confirmed = window.confirm(
      "Are you sure you want to logout?"
    );

    if (!confirmed) {
      return;
    }

    // Remove local user session information
    localStorage.removeItem("userName");
    localStorage.removeItem("userEmail");

    router.push("/");
  };

  return (
    <html lang="en">
      <body className="bg-slate-100 text-slate-900">

        {/* Navigation Bar */}
        {!publicPath && (
          <nav className="sticky top-0 z-50 border-b border-slate-200 bg-white shadow-sm">

            <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-4 py-4 md:px-6">

              {/* Logo */}
              <button
                type="button"
                onClick={() => router.push("/dashboard")}
                className="text-lg font-bold text-blue-600 transition hover:text-blue-700"
              >
                Smart Event Management
              </button>

              {/* Navigation Links */}
              <div className="flex flex-wrap items-center gap-2 text-sm">

                <button
                  type="button"
                  onClick={() =>
                    router.push("/dashboard")
                  }
                  className="rounded-lg px-3 py-2 font-medium text-slate-700 transition hover:bg-slate-100"
                >
                  Dashboard
                </button>

                <button
                  type="button"
                  onClick={() =>
                    router.push("/events")
                  }
                  className="rounded-lg px-3 py-2 font-medium text-slate-700 transition hover:bg-slate-100"
                >
                  My Events
                </button>

                <button
                  type="button"
                  onClick={() =>
                    router.push("/create")
                  }
                  className="rounded-lg px-3 py-2 font-medium text-slate-700 transition hover:bg-slate-100"
                >
                  Create
                </button>

                <button
                  type="button"
                  onClick={() =>
                    router.push("/upcoming")
                  }
                  className="rounded-lg px-3 py-2 font-medium text-slate-700 transition hover:bg-slate-100"
                >
                  Upcoming
                </button>

                <button
                  type="button"
                  onClick={() =>
                    router.push("/profile")
                  }
                  className="rounded-lg px-3 py-2 font-medium text-slate-700 transition hover:bg-slate-100"
                >
                  Profile
                </button>

                {/* Logout */}
                <button
                  type="button"
                  onClick={handleLogout}
                  className="rounded-lg bg-red-500 px-3 py-2 font-medium text-white transition hover:bg-red-600"
                >
                  Logout
                </button>

              </div>
            </div>
          </nav>
        )}

        {/* Page Content */}
        {children}

      </body>
    </html>
  );
}