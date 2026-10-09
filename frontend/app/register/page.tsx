"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { API_BASE_URL } from "@/lib/api";

const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z\d]).{8,}$/;
const emailValidationMessage = "Please enter a valid email address format (e.g., xyz@gmail.com)";
const passwordValidationMessage = "Password must be at least 8 characters long and include an uppercase letter, a lowercase letter, a number, and a special character.";

export default function Register() {
  const router = useRouter();

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [emailError, setEmailError] = useState("");
  const [passwordError, setPasswordError] = useState("");
  const [confirmPasswordError, setConfirmPasswordError] = useState("");

  const validateEmail = (value: string) => emailRegex.test(value.trim());

  const handleSubmit = async (
    e: React.FormEvent<HTMLFormElement>
  ) => {
    e.preventDefault();

    if (!name.trim()) {
      alert("Please fill in your full name.");
      return;
    }

    if (!validateEmail(email)) {
      setEmailError(emailValidationMessage);
      return;
    }
    setEmailError("");

    if (!passwordRegex.test(password)) {
      setPasswordError(passwordValidationMessage);
      return;
    }
    setPasswordError("");

    if (!confirmPassword.trim()) {
      setConfirmPasswordError("Please confirm your password.");
      return;
    }
    if (password !== confirmPassword) {
      setConfirmPasswordError("Passwords do not match.");
      return;
    }
    setConfirmPasswordError("");

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/auth/register`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            name: name.trim(),
            email: email.trim(),
            password: password,
            role: "USER",
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        alert(data.detail || "Registration failed.");
        return;
      }

      localStorage.setItem("userName", name.trim());
      localStorage.setItem("userEmail", email.trim());

      alert("Account created successfully!");

      router.push("/");
    } catch (error) {
      console.error(error);
      alert("Cannot connect to the backend.");
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-100 px-4 py-8">
      <div className="w-full max-w-lg">

        <div className="rounded-2xl bg-white p-8 shadow-xl">

          <h1 className="text-3xl font-bold text-slate-900">
            Create Account
          </h1>

          <p className="mt-2 text-slate-500">
            Register for Smart Event Management.
          </p>

          <form
            onSubmit={handleSubmit}
            className="mt-6 space-y-5"
          >

            <div>
              <label
                htmlFor="name"
                className="mb-2 block text-sm font-medium text-slate-700"
              >
                Full Name
              </label>

              <input
                id="name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Enter your full name"
                className="w-full rounded-lg border border-slate-300 px-4 py-3 text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
              />
            </div>

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
                value={email}
                onChange={(e) => {
                  const value = e.target.value;
                  setEmail(value);
                  setEmailError(value && !validateEmail(value) ? emailValidationMessage : "");
                }}
                placeholder="Enter your email"
                className="w-full rounded-lg border border-slate-300 px-4 py-3 text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
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
                onChange={(e) => {
                  const value = e.target.value;
                  setPassword(value);
                  setPasswordError(value && !passwordRegex.test(value) ? passwordValidationMessage : "");
                }}
                placeholder="Enter your password"
                className="w-full rounded-lg border border-slate-300 px-4 py-3 text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
              />
              {passwordError ? (
                <p className="mt-1 text-sm text-red-600">{passwordError}</p>
              ) : null}
            </div>

            <div>
              <label
                htmlFor="confirmPassword"
                className="mb-2 block text-sm font-medium text-slate-700"
              >
                Confirm Password
              </label>

              <input
                id="confirmPassword"
                type="password"
                value={confirmPassword}
                onChange={(e) => {
                  const value = e.target.value;
                  setConfirmPassword(value);
                  setConfirmPasswordError(value && password !== value ? "Passwords do not match." : "");
                }}
                placeholder="Confirm your password"
                className="w-full rounded-lg border border-slate-300 px-4 py-3 text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
              />
              {confirmPasswordError ? (
                <p className="mt-1 text-sm text-red-600">{confirmPasswordError}</p>
              ) : null}
            </div>

            <button
              type="submit"
              className="w-full rounded-lg bg-blue-600 py-3 font-semibold text-white transition hover:bg-blue-700"
            >
              Create Account
            </button>

          </form>

          <button
            type="button"
            onClick={() => router.push("/")}
            className="mt-5 w-full text-sm font-semibold text-blue-600 hover:text-blue-800"
          >
            Already have an account? Login
          </button>

        </div>
      </div>
    </main>
  );
}