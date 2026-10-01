"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(false);

  const handleLogin = async (
    e: React.FormEvent<HTMLFormElement>
  ) => {
    e.preventDefault();

    if (!email.trim() || !password.trim()) {
      alert("Please enter your email and password.");
      return;
    }

    if (!email.includes("@")) {
      alert("Please enter a valid email address.");
      return;
    }

    try {
      // Clear previous session BEFORE login
      localStorage.removeItem("access_token");
      localStorage.removeItem("userName");
      localStorage.removeItem("userEmail");
      localStorage.removeItem("userRole");
      localStorage.removeItem("rememberMe");

      // Login
      const response = await fetch(
        "http://127.0.0.1:8000/api/auth/login",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            name: "Login User",
            email: email.trim(),
            password: password,
            role: "USER",
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        alert(data.detail || "Login failed.");
        return;
      }

      const token = data.access_token;

      if (!token) {
        alert("Login failed: access token was not received.");
        return;
      }

      // Store ONLY the new token
      localStorage.setItem("access_token", token);

      // Ask backend who actually logged in
      const userResponse = await fetch(
        "http://127.0.0.1:8000/api/auth/me",
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
        alert("Could not verify logged-in user.");
        return;
      }

      const userData = await userResponse.json();

      console.log("LOGIN USER:", userData);
      console.log("LOGIN ROLE:", userData.role);

      // Store actual backend user information
      localStorage.setItem(
        "userEmail",
        userData.email || email.trim()
      );

      localStorage.setItem(
        "userName",
        userData.name || email.trim()
      );

      localStorage.setItem(
        "userRole",
        String(userData.role || "").toUpperCase()
      );

      if (rememberMe) {
        localStorage.setItem("rememberMe", "true");
      }

      alert("Login successful!");

      router.push("/dashboard");
    } catch (error) {
      console.error(error);
      alert("Cannot connect to the backend.");
    }
  };

  const handleForgotPassword = () => {
    alert(
      "Password reset will be connected to the API later."
    );
  };

  return (
    <main className="min-h-screen bg-slate-100 flex items-center justify-center px-4">
      <div className="w-full max-w-md rounded-2xl bg-white p-8 shadow-lg">

        <h1 className="text-3xl font-bold text-center text-slate-900">
          Smart Event Management
        </h1>

        <p className="mt-2 text-center text-slate-600">
          Login to your account
        </p>

        <form
          onSubmit={handleLogin}
          className="mt-8 space-y-5"
        >

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
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter your email"
              className="w-full rounded-lg border border-slate-300 px-4 py-3 text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
            />
          </div>

          {/* Password */}
          <div>
            <label
              htmlFor="password"
              className="mb-2 block text-sm font-medium text-slate-700"
            >
              Password
            </label>

            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              className="w-full rounded-lg border border-slate-300 px-4 py-3 text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
            />
          </div>

          {/* Remember Me */}
          <div className="flex items-center justify-between">

            <label className="flex items-center gap-2 text-sm text-slate-600">
              <input
                type="checkbox"
                checked={rememberMe}
                onChange={(e) =>
                  setRememberMe(e.target.checked)
                }
                className="h-4 w-4"
              />

              Remember me
            </label>

            <button
              type="button"
              onClick={handleForgotPassword}
              className="text-sm font-medium text-blue-600 hover:text-blue-800"
            >
              Forgot Password?
            </button>

          </div>

          {/* Login Button */}
          <button
            type="submit"
            className="w-full rounded-lg bg-blue-600 py-3 font-semibold text-white transition hover:bg-blue-700"
          >
            Login
          </button>

        </form>

        {/* Register */}
        <p className="mt-6 text-center text-sm text-slate-600">
          Don't have an account?{" "}

          <button
            type="button"
            onClick={() => router.push("/register")}
            className="font-semibold text-blue-600 hover:text-blue-800"
          >
            Create Account
          </button>
        </p>

      </div>
    </main>
  );
}