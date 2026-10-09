"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { API_BASE_URL } from "@/lib/api";

const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const emailValidationMessage = "Please enter a valid email address format (e.g., xyz@gmail.com)";

export default function LoginPage() {
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(false);
  const [emailError, setEmailError] = useState("");
  const [passwordError, setPasswordError] = useState("");
  const [showForgotPassword, setShowForgotPassword] = useState(false);
  const [forgotPasswordEmail, setForgotPasswordEmail] = useState("");
  const [forgotPasswordError, setForgotPasswordError] = useState("");

  const validateEmail = (value: string) => {
    if (!value.trim() || !emailRegex.test(value.trim())) {
      return false;
    }
    return true;
  };

  const handleLogin = async (
    e: React.FormEvent<HTMLFormElement>
  ) => {
    e.preventDefault();

    const isEmailValid = validateEmail(email);
    if (!isEmailValid) {
      setEmailError(emailValidationMessage);
      return;
    }
    setEmailError("");

    if (!password.trim()) {
      setPasswordError("Please enter your password.");
      return;
    }
    setPasswordError("");

    try {
      localStorage.removeItem("access_token");
      localStorage.removeItem("userName");
      localStorage.removeItem("userEmail");
      localStorage.removeItem("userRole");
      localStorage.removeItem("rememberMe");

      const response = await fetch(
        `${API_BASE_URL}/api/auth/login`,
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

      localStorage.setItem("access_token", token);

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
        alert("Could not verify logged-in user.");
        return;
      }

      const userData = await userResponse.json();

      localStorage.setItem("userEmail", userData.email || email.trim());
      localStorage.setItem("userName", userData.name || email.trim());
      localStorage.setItem("userRole", String(userData.role || "").toUpperCase());

      if (rememberMe) {
        localStorage.setItem("rememberMe", "true");
      }

      alert("Login successful!");

      router.push(String(userData.role || "").toUpperCase() === "ADMIN" ? "/admin" : "/dashboard");
    } catch (error) {
      console.error(error);
      alert("Cannot connect to the backend.");
    }
  };

  const handleForgotPassword = () => {
    setShowForgotPassword((prev) => !prev);
    setForgotPasswordError("");
    setForgotPasswordEmail("");
  };

  const handleForgotPasswordSubmit = () => {
    if (!forgotPasswordEmail.trim() || !emailRegex.test(forgotPasswordEmail.trim())) {
      setForgotPasswordError(emailValidationMessage);
      return;
    }

    setForgotPasswordError("");
    setShowForgotPassword(false);
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
              onChange={(e) => {
                const value = e.target.value;
                setEmail(value);
                setEmailError(value && !emailRegex.test(value.trim()) ? emailValidationMessage : "");
              }}
              placeholder="Enter your email"
              className="w-full rounded-lg border border-slate-300 px-4 py-3 text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
            />
            {emailError ? (
              <p className="mt-1 text-sm text-red-600">{emailError}</p>
            ) : null}
          </div>

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
            {passwordError ? (
              <p className="mt-1 text-sm text-red-600">{passwordError}</p>
            ) : null}
          </div>

          <div className="flex items-center justify-between">
            <label className="flex items-center gap-2 text-sm text-slate-600">
              <input
                type="checkbox"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
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

          {showForgotPassword ? (
            <div className="space-y-2 rounded-lg border border-slate-200 bg-slate-50 p-3">
              <input
                type="email"
                value={forgotPasswordEmail}
                onChange={(e) => {
                  const value = e.target.value;
                  setForgotPasswordEmail(value);
                  setForgotPasswordError(value && !emailRegex.test(value.trim()) ? emailValidationMessage : "");
                }}
                placeholder="Please enter your email to recover your password (e.g., xyz@gmail.com)"
                className="w-full rounded-lg border border-slate-300 bg-white px-4 py-3 text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
              />
              {forgotPasswordError ? (
                <p className="text-sm text-red-600">{forgotPasswordError}</p>
              ) : null}
              <button
                type="button"
                onClick={handleForgotPasswordSubmit}
                className="w-full rounded-lg bg-slate-200 py-2 text-sm font-medium text-slate-800 transition hover:bg-slate-300"
              >
                Recover Password
              </button>
            </div>
          ) : null}

          <button
            type="submit"
            className="w-full rounded-lg bg-blue-600 py-3 font-semibold text-white transition hover:bg-blue-700"
          >
            Login
          </button>

        </form>

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