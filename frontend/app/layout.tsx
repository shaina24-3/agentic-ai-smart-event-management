"use client";

import "./globals.css";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

type NavigationIconName =
  | "dashboard"
  | "events"
  | "create"
  | "users"
  | "venues"
  | "agent"
  | "profile";

function NavigationIcon({ name }: { name: NavigationIconName }) {
  const commonProps = {
    className: "h-5 w-5 shrink-0",
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.8,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    "aria-hidden": true as const,
  };

  switch (name) {
    case "dashboard":
      return (
        <svg {...commonProps}>
          <rect x="3" y="3" width="7" height="7" rx="1" />
          <rect x="14" y="3" width="7" height="7" rx="1" />
          <rect x="3" y="14" width="7" height="7" rx="1" />
          <rect x="14" y="14" width="7" height="7" rx="1" />
        </svg>
      );
    case "events":
      return (
        <svg {...commonProps}>
          <rect x="3" y="5" width="18" height="16" rx="2" />
          <path d="M16 3v4M8 3v4M3 11h18M8 15h3M8 18h7" />
        </svg>
      );
    case "create":
      return (
        <svg {...commonProps}>
          <rect x="3" y="3" width="18" height="18" rx="3" />
          <path d="M12 8v8M8 12h8" />
        </svg>
      );
    case "users":
      return (
        <svg {...commonProps}>
          <path d="M16 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
          <circle cx="10" cy="7" r="4" />
          <path d="M20 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" />
        </svg>
      );
    case "venues":
      return (
        <svg {...commonProps}>
          <path d="M3 21h18M5 21V5l7-3 7 3v16M9 9h1M14 9h1M9 13h1M14 13h1M10 21v-4h4v4" />
        </svg>
      );
    case "agent":
      return (
        <svg {...commonProps}>
          <circle cx="6" cy="6" r="2.5" />
          <circle cx="18" cy="6" r="2.5" />
          <circle cx="12" cy="18" r="2.5" />
          <path d="M8.5 6h7M7.5 8l3 7.5M16.5 8l-3 7.5" />
        </svg>
      );
    case "profile":
      return (
        <svg {...commonProps}>
          <circle cx="12" cy="8" r="4" />
          <path d="M5 21v-1a7 7 0 0 1 14 0v1" />
        </svg>
      );
  }
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const pathname = usePathname();
  const router = useRouter();

  const [userName, setUserName] = useState("User");
  const [userRole, setUserRole] = useState("USER");
  const [userEmail, setUserEmail] = useState("");

  useEffect(() => {
    const savedName = localStorage.getItem("userName");
    const savedRole = localStorage.getItem("userRole");
    const savedEmail = localStorage.getItem("userEmail");

    if (savedName) setUserName(savedName);
    if (savedRole) setUserRole(savedRole.toUpperCase());
    if (savedEmail) setUserEmail(savedEmail);

    // Also fetch profile from backend if token exists
    const token = localStorage.getItem("access_token");
    if (token) {
      fetch("http://127.0.0.1:8000/api/auth/me", {
        headers: { Authorization: `Bearer ${token}` }
      })
        .then((res) => (res.ok ? res.json() : null))
        .then((data) => {
          if (data) {
            setUserName(data.name || "User");
            setUserRole((data.role || "USER").toUpperCase());
            setUserEmail(data.email || "");
            localStorage.setItem("userName", data.name || "User");
            localStorage.setItem("userRole", data.role || "USER");
            localStorage.setItem("userEmail", data.email || "");
          }
        })
        .catch(() => {});
    }
  }, [pathname]);

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("ai-assistant-chat-messages");
    localStorage.removeItem("userName");
    localStorage.removeItem("userEmail");
    localStorage.removeItem("userRole");
    localStorage.removeItem("rememberMe");
    router.push("/");
  };

  const publicPages = ["/", "/register"];
  const isPublicPage = publicPages.includes(pathname);
  const isAdmin = userRole === "ADMIN";
  const dashboardPath = isAdmin ? "/admin" : "/dashboard";

  if (isPublicPage) {
    return (
      <html lang="en">
        <body className="bg-slate-100 text-slate-900 antialiased">{children}</body>
      </html>
    );
  }

  return (
    <html lang="en">
      <body className="bg-slate-50 text-slate-900 antialiased font-sans">
        <div className="flex min-h-screen">
          {/* ========================================================= */}
          {/* Left Sidebar (Matches Reference Design)                    */}
          {/* ========================================================= */}
          <aside className="w-64 border-r border-slate-200 bg-white flex flex-col justify-between p-4 sticky top-0 h-screen select-none shrink-0 shadow-sm">
            <div>
              {/* App Brand / Logo */}
              <Link href={dashboardPath} className="flex items-center gap-3 px-2 py-3 mb-6">
                <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-tr from-indigo-600 to-purple-600 text-white shadow-md font-bold text-xl">
                  📅
                </div>
                <div>
                  <h1 className="font-bold text-lg leading-tight text-slate-900">SmartEvent</h1>
                  <p className="text-[11px] text-slate-400 font-medium tracking-tight">Plan • Manage • Create</p>
                </div>
              </Link>

              {/* Navigation Links */}
              <nav className="space-y-1 text-sm font-medium">
                {/* 1. Dashboard */}
                <Link
                  href={dashboardPath}
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-xl transition ${
                    pathname === dashboardPath
                      ? "bg-indigo-50 text-indigo-700 font-semibold shadow-xs"
                      : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                  }`}
                >
                  <NavigationIcon name="dashboard" />
                  <span>Dashboard</span>
                </Link>

                {/* 2. Events */}
                <Link
                  href="/events"
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-xl transition ${
                    pathname === "/events" || pathname.startsWith("/events/")
                      ? "bg-indigo-50 text-indigo-700 font-semibold shadow-xs"
                      : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                  }`}
                >
                  <NavigationIcon name="events" />
                  <span>Events</span>
                </Link>

                {!isAdmin && (
                  <Link
                    href="/registrations"
                    className={`flex items-center gap-3 px-3 py-2.5 rounded-xl transition ${
                      pathname === "/registrations"
                        ? "bg-indigo-50 text-indigo-700 font-semibold shadow-xs"
                        : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                    }`}
                  >
                    <svg
                      className="h-5 w-5 shrink-0"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="1.8"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      aria-hidden="true"
                    >
                      <rect x="5" y="4" width="14" height="17" rx="2" />
                      <path d="M9 4.5h6M9 10h6M9 14h6M9 18h3" />
                    </svg>
                    <span>My Registrations</span>
                  </Link>
                )}

                {/* 3. Venues */}
                <Link
                  href="/venues"
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-xl transition ${
                    pathname === "/venues"
                      ? "bg-indigo-50 text-indigo-700 font-semibold shadow-xs"
                      : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                  }`}
                >
                  <NavigationIcon name="venues" />
                  <span>Venues</span>
                </Link>

                {/* 4. Registrations (Admin Only) */}
                {isAdmin && (
                  <Link
                    href="/admin/registrations"
                    className={`flex items-center gap-3 px-3 py-2.5 rounded-xl transition ${
                      pathname === "/admin/registrations"
                        ? "bg-indigo-50 text-indigo-700 font-semibold shadow-xs"
                        : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                    }`}
                  >
                    <svg
                      className="h-5 w-5 shrink-0"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="1.8"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      aria-hidden="true"
                    >
                      <rect x="5" y="4" width="14" height="17" rx="2" />
                      <path d="M9 4.5h6M9 10h6M9 14h6M9 18h3" />
                    </svg>
                    <span>Registrations</span>
                  </Link>
                )}

                {/* 5. Attendees / Users (Admin Only) */}
                {isAdmin && (
                  <Link
                    href="/admin/users"
                    className={`flex items-center gap-3 px-3 py-2.5 rounded-xl transition ${
                      pathname === "/admin/users"
                        ? "bg-indigo-50 text-indigo-700 font-semibold shadow-xs"
                        : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                    }`}
                  >
                    <NavigationIcon name="users" />
                    <span>Attendees / Users</span>
                  </Link>
                )}

                {/* 6. AI Agent (Core Infosys Requirement!) */}
                <Link
                  href="/ai-assistant"
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-xl transition border border-indigo-100 ${
                    pathname === "/ai-assistant"
                      ? "bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-semibold shadow-sm"
                      : "bg-indigo-50/50 text-indigo-700 hover:bg-indigo-50"
                  }`}
                >
                  <NavigationIcon name="agent" />
                  <span>AI Agent</span>
                  <span className="ml-auto text-[10px] bg-indigo-200 text-indigo-900 font-bold px-1.5 py-0.5 rounded-full uppercase">Llama</span>
                </Link>

                {/* 7. Profile */}
                <Link
                  href="/profile"
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-xl transition ${
                    pathname === "/profile"
                      ? "bg-indigo-50 text-indigo-700 font-semibold shadow-xs"
                      : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                  }`}
                >
                  <NavigationIcon name="profile" />
                  <span>Profile</span>
                </Link>
              </nav>
            </div>

          </aside>

          {/* ========================================================= */}
          {/* Main Layout Area                                           */}
          {/* ========================================================= */}
          <div className="flex-1 flex flex-col min-w-0">
            {/* Top Bar Header */}
            <header className="sticky top-0 z-40 flex h-16 items-center justify-end border-b border-slate-200 bg-white px-6 shadow-xs">
              <div className="ml-auto flex min-w-0 items-center justify-end gap-2 sm:gap-4">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-indigo-600 text-sm font-semibold text-white">
                  {userName.trim().charAt(0).toUpperCase() || "U"}
                </div>
                <p className="max-w-[24vw] truncate text-sm font-semibold text-slate-800 sm:max-w-[140px]">
                  {userName}
                </p>
                <p className="max-w-[34vw] truncate text-xs font-medium text-slate-600 sm:max-w-[220px]">
                  {userEmail}
                </p>
                <button
                  onClick={handleLogout}
                  className="shrink-0 rounded-lg bg-red-50 px-2.5 py-1 text-xs font-semibold text-red-600 transition hover:bg-red-100"
                  title="Logout"
                >
                  Logout
                </button>
              </div>
            </header>

            {/* Page Content Body */}
            <main className="flex-1 p-6 md:p-8 overflow-y-auto">
              {children}
            </main>
          </div>
        </div>
      </body>
    </html>
  );
}