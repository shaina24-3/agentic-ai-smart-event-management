"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

export default function Profile() {
  const router = useRouter();

  const [name, setName] = useState("User");
  const [email, setEmail] = useState("user@example.com");
  const [role, setRole] = useState("USER");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmNewPassword, setConfirmNewPassword] = useState("");
  const [passwordMessage, setPasswordMessage] = useState("");

  useEffect(() => {
    const savedName = localStorage.getItem("userName");
    const savedEmail = localStorage.getItem("userEmail");
    const token = localStorage.getItem("access_token");

    setName(savedName || "User");
    setEmail(savedEmail || "user@example.com");

    if (token) {
      fetch("http://127.0.0.1:8000/api/auth/me", {
        headers: { Authorization: `Bearer ${token}` },
        cache: "no-store",
      })
        .then((response) => (response.ok ? response.json() : null))
        .then((user) => {
          if (user) setRole(String(user.role || "USER").toUpperCase());
        })
        .catch(() => {});
    }
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

    localStorage.setItem(
      "userName",
      name.trim()
    );

    localStorage.setItem(
      "userEmail",
      email.trim()
    );

    alert("Profile updated successfully!");
  };

  const handleLogout = () => {
    // Remove current user's session
    localStorage.removeItem("access_token");
    localStorage.removeItem("ai-assistant-chat-messages");
    localStorage.removeItem("userName");
    localStorage.removeItem("userEmail");
    localStorage.removeItem("rememberMe");

    // Return to login
    router.push("/");
  };

  const handlePasswordUpdate = async () => {
    setPasswordMessage("");
    if (!currentPassword || !newPassword || !confirmNewPassword) {
      setPasswordMessage("Complete all three password fields.");
      return;
    }
    if (newPassword !== confirmNewPassword) {
      setPasswordMessage("New password and confirmation do not match.");
      return;
    }
    if (newPassword.length < 8) {
      setPasswordMessage("New password must be at least 8 characters.");
      return;
    }

    const token = localStorage.getItem("access_token");
    if (!token) {
      router.push("/");
      return;
    }

    try {
      const response = await fetch("http://127.0.0.1:8000/api/auth/change-password", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
        }),
      });
      const result = await response.json();
      if (!response.ok) {
        setPasswordMessage(result.detail || "Could not update password.");
        return;
      }

      setCurrentPassword("");
      setNewPassword("");
      setConfirmNewPassword("");
      setPasswordMessage("Password updated successfully.");
    } catch {
      setPasswordMessage("Could not connect to the backend.");
    }
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
                {role === "ADMIN" ? "Administrator" : "User"}
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

              <span className="mb-2 block text-sm font-medium text-slate-700">
                Role
              </span>
              <p id="role" className="w-full rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-slate-700">
                {role === "ADMIN" ? "Admin" : "User"}
              </p>

            </div>

            {/* Save Button */}
            <button
              type="button"
              onClick={handleSave}
              className="w-full rounded-lg bg-blue-600 py-3 font-semibold text-white transition hover:bg-blue-700"
            >
              Save Profile
            </button>

            {/* Logout Button */}
            <button
              type="button"
              onClick={handleLogout}
              className="w-full rounded-lg bg-red-600 py-3 font-semibold text-white transition hover:bg-red-700"
            >
              Logout
            </button>

          </div>

        </div>

        <section className="mt-6 rounded-2xl border border-slate-200 bg-white p-8 shadow-lg">
          <h2 className="text-xl font-semibold text-slate-900">Change Password</h2>
          <div className="mt-5 grid gap-5">
            <div>
              <label htmlFor="current-password" className="mb-2 block text-sm font-medium text-slate-700">
                Current Password
              </label>
              <input
                id="current-password"
                type="password"
                autoComplete="current-password"
                value={currentPassword}
                onChange={(event) => setCurrentPassword(event.target.value)}
                className="w-full rounded-lg border border-slate-300 px-4 py-3 text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
              />
            </div>
            <div>
              <label htmlFor="new-password" className="mb-2 block text-sm font-medium text-slate-700">
                New Password
              </label>
              <input
                id="new-password"
                type="password"
                autoComplete="new-password"
                value={newPassword}
                onChange={(event) => setNewPassword(event.target.value)}
                className="w-full rounded-lg border border-slate-300 px-4 py-3 text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
              />
            </div>
            <div>
              <label htmlFor="confirm-new-password" className="mb-2 block text-sm font-medium text-slate-700">
                Confirm New Password
              </label>
              <input
                id="confirm-new-password"
                type="password"
                autoComplete="new-password"
                value={confirmNewPassword}
                onChange={(event) => setConfirmNewPassword(event.target.value)}
                className="w-full rounded-lg border border-slate-300 px-4 py-3 text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
              />
            </div>
            {passwordMessage && (
              <p role="status" className="text-sm text-slate-700">
                {passwordMessage}
              </p>
            )}
            <button
              type="button"
              onClick={() => void handlePasswordUpdate()}
              className="w-full rounded-lg bg-blue-600 py-3 font-semibold text-white transition hover:bg-blue-700"
            >
              Update Password
            </button>
          </div>
        </section>

      </div>

    </main>
  );
}