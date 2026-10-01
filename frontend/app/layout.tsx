"use client";

import "./globals.css";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

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

  if (isPublicPage) {
    return (
      <html lang="en">
        <body className="bg-slate-100 text-slate-900 antialiased">{children}</body>
      </html>
    );
  }

  const currentDate = new Date().toLocaleDateString("en-US", {
    weekday: "long",
    day: "numeric",
    month: "short",
    year: "numeric",
  });

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
              <Link href="/dashboard" className="flex items-center gap-3 px-2 py-3 mb-6">
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
                  href="/dashboard"
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-xl transition ${
                    pathname === "/dashboard"
                      ? "bg-indigo-50 text-indigo-700 font-semibold shadow-xs"
                      : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                  }`}
                >
                  <span className="text-lg">📊</span>
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
                  <span className="text-lg">📅</span>
                  <span>Events</span>
                </Link>

                {/* 3. Create Event (Admin Only or Creators) */}
                {isAdmin && (
                  <Link
                    href="/create"
                    className={`flex items-center gap-3 px-3 py-2.5 rounded-xl transition ${
                      pathname === "/create"
                        ? "bg-indigo-50 text-indigo-700 font-semibold shadow-xs"
                        : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                    }`}
                  >
                    <span className="text-lg">➕</span>
                    <span>Create Event</span>
                  </Link>
                )}

                {/* 4. Attendees / Users (Admin Only) */}
                {isAdmin && (
                  <Link
                    href="/admin/users"
                    className={`flex items-center gap-3 px-3 py-2.5 rounded-xl transition ${
                      pathname === "/admin/users"
                        ? "bg-indigo-50 text-indigo-700 font-semibold shadow-xs"
                        : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                    }`}
                  >
                    <span className="text-lg">👥</span>
                    <span>Attendees / Users</span>
                  </Link>
                )}

                {/* 5. Venues */}
                <Link
                  href="/venues"
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-xl transition ${
                    pathname === "/venues"
                      ? "bg-indigo-50 text-indigo-700 font-semibold shadow-xs"
                      : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                  }`}
                >
                  <span className="text-lg">📍</span>
                  <span>Venues</span>
                </Link>

                {/* 6. AI Agent (Core Infosys Requirement!) */}
                <Link
                  href="/ai-assistant"
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-xl transition border border-indigo-100 ${
                    pathname === "/ai-assistant"
                      ? "bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-semibold shadow-sm"
                      : "bg-indigo-50/50 text-indigo-700 hover:bg-indigo-50"
                  }`}
                >
                  <span className="text-lg">🤖</span>
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
                  <span className="text-lg">👤</span>
                  <span>Profile</span>
                </Link>
              </nav>
            </div>

            {/* Sidebar Promo Card (Like Reference Image) */}
            <div className="rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 p-4 text-white text-center shadow-md">
              <span className="text-2xl mb-1 block">🤖</span>
              <h3 className="font-bold text-sm">AI Event Assistant</h3>
              <p className="text-[11px] text-indigo-100 mt-1">Book venues, create events & ask rules in plain English.</p>
              <Link
                href="/ai-assistant"
                className="mt-3 inline-block w-full py-1.5 px-3 bg-white text-indigo-700 font-bold text-xs rounded-lg hover:bg-indigo-50 transition shadow-sm"
              >
                Chat with Agent →
              </Link>
            </div>
          </aside>

          {/* ========================================================= */}
          {/* Main Layout Area                                           */}
          {/* ========================================================= */}
          <div className="flex-1 flex flex-col min-w-0">
            {/* Top Bar Header */}
            <header className="h-16 border-b border-slate-200 bg-white flex items-center justify-between px-6 sticky top-0 z-40 shadow-xs">
              {/* Search Bar */}
              <div className="flex items-center gap-2 bg-slate-100 rounded-xl px-3 py-1.5 w-72 md:w-96 border border-slate-200 focus-within:border-indigo-500 focus-within:bg-white transition">
                <span className="text-slate-400 text-sm">🔍</span>
                <input
                  type="text"
                  placeholder="Search events, attendees, venues..."
                  className="bg-transparent text-sm w-full outline-hidden text-slate-800 placeholder-slate-400"
                />
              </div>

              {/* Right User & Utility Controls */}
              <div className="flex items-center gap-4">
                {/* Date Display */}
                <div className="hidden lg:flex items-center gap-1.5 text-xs font-medium text-slate-500 bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-200">
                  <span>📅</span>
                  <span>{currentDate}</span>
                </div>

                {/* Notifications Icon */}
                <button
                  type="button"
                  title="Notifications"
                  className="relative p-2 text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded-xl transition"
                >
                  <span className="text-lg">🔔</span>
                  <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-red-500 ring-2 ring-white"></span>
                </button>

                {/* User Profile Avatar & Role */}
                <div className="flex items-center gap-3 pl-3 border-l border-slate-200">
                  <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-600 text-white font-bold text-sm shadow-xs">
                    {userName.charAt(0).toUpperCase()}
                  </div>
                  <div className="hidden sm:block text-left">
                    <p className="text-xs font-bold text-slate-800 leading-tight truncate max-w-[120px]">{userName}</p>
                    <p className="text-[10px] font-semibold text-indigo-600 uppercase tracking-wider">
                      {isAdmin ? "Administrator" : "Attendee"}
                    </p>
                  </div>
                  <button
                    onClick={handleLogout}
                    className="ml-2 px-2.5 py-1 text-xs font-semibold text-red-600 bg-red-50 hover:bg-red-100 rounded-lg transition"
                    title="Logout"
                  >
                    Logout
                  </button>
                </div>
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