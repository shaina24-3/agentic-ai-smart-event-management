"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

export default function Profile() {
  const router = useRouter();

  const [name, setName] = useState("User");
  const [email, setEmail] = useState("user@example.com");

  useEffect(() => {
    const savedName = localStorage.getItem("userName");
    const savedEmail = localStorage.getItem("userEmail");

    setName(savedName || "User");
    setEmail(savedEmail || "user@example.com");
  }, []);

  const handleSave = () => {
    if (!name.trim() || !email.trim()) {
      alert("Please fill in all fields.");
      return;
    }

    if (!email.includes("@")) {
      alert("Please enter a valid email address.");
      return;
    }

    localStorage.setItem("userName", name.trim());
    localStorage.setItem("userEmail", email.trim());

    alert("Profile updated successfully!");
  };

  const firstLetter = name.trim()
    ? name.trim().charAt(0).toUpperCase()
    : "U";

  return (
    <main className="min-h-screen bg-slate-100 px-4 py-8 md:px-6">
      <div className="mx-auto max-w-4xl">

        {/* Back Button */}
        <button
          type="button"
          onClick={() => router.push("/dashboard")}
          className="mb-5 text-sm font-medium text-blue-600 hover:text-blue-800"
        >
          ← Back to Dashboard
        </button>

        {/* Page Heading */}
        <h1 className="text-3xl font-bold text-slate-900">
          Profile
        </h1>

        <p className="mt-2 text-slate-600">
          View and manage your account information.
        </p>

        {/* Profile Card */}
        <div className="mt-8 rounded-2xl bg-white p-8 shadow-lg">

          {/* Profile Header */}
          <div className="flex items-center gap-5 border-b border-slate-200 pb-6">

            <div className="flex h-20 w-20 items-center justify-center rounded-full bg-blue-600 text-2xl font-bold text-white">
              {firstLetter}
            </div>

            <div>
              <h2 className="text-2xl font-semibold text-slate-900">
                {name}
              </h2>

              <p className="mt-1 text-slate-500">
                Smart Event Management User
              </p>
            </div>

          </div>

          {/* Profile Form */}
          <div className="mt-6 space-y-5">

            {/* Name */}
            <div>
              <label
                htmlFor="name"
                className="mb-2 block text-sm font-medium text-slate-700"
              >
                Name
              </label>

              <input
                id="name"
                type="text"
                value={name}
                onChange={(e) =>
                  setName(e.target.value)
                }
                placeholder="Enter your name"
                className="w-full rounded-lg border border-slate-300 px-4 py-3 text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
              />
            </div>

            {/* Email */}
            <div>
              <label
                htmlFor="email"
                className="mb-2 block text-sm font-medium text-slate-700"
              >
                Email
              </label>

              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) =>
                  setEmail(e.target.value)
                }
                placeholder="Enter your email"
                className="w-full rounded-lg border border-slate-300 px-4 py-3 text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
              />
            </div>

            {/* Role */}
            <div>
              <label
                htmlFor="role"
                className="mb-2 block text-sm font-medium text-slate-700"
              >
                Role
              </label>

              <input
                id="role"
                type="text"
                value="User"
                disabled
                className="w-full rounded-lg border border-slate-300 bg-slate-50 px-4 py-3 text-slate-500"
              />
            </div>

            {/* Save Button */}
            <button
              type="button"
              onClick={handleSave}
              className="w-full rounded-lg bg-blue-600 py-3 font-semibold text-white transition hover:bg-blue-700"
            >
              Save Profile
            </button>

          </div>
        </div>
      </div>
    </main>
  );
}