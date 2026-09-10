"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function Home() {
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(false);

  const handleLogin = (
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

    // Frontend-only login for now.
    // This will be replaced with the FastAPI authentication API later.
    localStorage.setItem(
      "userEmail",
      email.trim()
    );

    if (rememberMe) {
      localStorage.setItem(
        "rememberMe",
        "true"
      );
    } else {
      localStorage.removeItem("rememberMe");
    }

    router.push("/dashboard");
  };

  const handleForgotPassword = () => {
    alert(
      "Password reset will be connected to the API later."
    );
  };

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-100 px-4 py-8">

      <div className="w-full max-w-md">

        {/* Logo and Heading */}
        <div className="mb-8 text-center">

          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-blue-600 text-2xl font-bold text-white shadow-lg">
            SE
          </div>

          <h1 className="text-3xl font-bold text-slate-900">
            Smart Event Management
          </h1>

          <p className="mt-2 text-slate-500">
            Manage your events smarter and easier
          </p>

        </div>

        {/* Login Card */}
        <div className="rounded-2xl bg-white p-8 shadow-xl">

          <h2 className="text-2xl font-semibold text-slate-900">
            Welcome Back
          </h2>

          <p className="mt-2 text-sm text-slate-500">
            Sign in to continue to your account
          </p>

          {/* Login Form */}
          <form
            onSubmit={handleLogin}
            className="mt-6 space-y-5"
          >

            {/* Email */}
            <div>
              <label
                htmlFor="email"
                className="mb-2 block text-sm font-medium text-slate-700"
              >
                Email Address
              </label>

              <input
                id="email"
                type="email"
                placeholder="Enter your email"
                value={email}
                onChange={(e) =>
                  setEmail(e.target.value)
                }
                className="w-full rounded-lg border border-slate-300 px-4 py-3 text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
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
                placeholder="Enter your password"
                value={password}
                onChange={(e) =>
                  setPassword(e.target.value)
                }
                className="w-full rounded-lg border border-slate-300 px-4 py-3 text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
              />
            </div>

            {/* Remember Me / Forgot Password */}
            <div className="flex items-center justify-between text-sm">

              <label className="flex cursor-pointer items-center gap-2 text-slate-600">

                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) =>
                    setRememberMe(e.target.checked)
                  }
                  className="h-4 w-4 rounded border-slate-300"
                />

                Remember me

              </label>

              <button
                type="button"
                onClick={handleForgotPassword}
                className="font-medium text-blue-600 hover:text-blue-800"
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
          <p className="mt-6 text-center text-sm text-slate-500">

            Don&apos;t have an account?{" "}

            <button
              type="button"
              onClick={() =>
                router.push("/register")
              }
              className="font-semibold text-blue-600 hover:text-blue-800"
            >
              Create Account
            </button>

          </p>

        </div>
      </div>
    </main>
  );
}