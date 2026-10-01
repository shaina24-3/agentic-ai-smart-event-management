"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

type UserItem = {
  id: number;
  name: string;
  email: string;
  role: string;
  created_at?: string;
};

export default function AdminUsersPage() {
  const router = useRouter();
  const [users, setUsers] = useState<UserItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      router.push("/");
      return;
    }

    try {
      const res = await fetch("http://127.0.0.1:8000/api/admin/users", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.status === 403) {
        alert("Admin permissions required to view user accounts.");
        router.push("/dashboard");
        return;
      }
      if (res.ok) {
        const data = await res.json();
        setUsers(data);
      }
    } catch (err) {
      console.error(err);
      setMessage("Could not load users from backend.");
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteUser = async (userId: number, uName: string) => {
    const token = localStorage.getItem("access_token");
    if (!token || !confirm(`Are you sure you want to remove user '${uName}'?`)) return;

    try {
      const res = await fetch(`http://127.0.0.1:8000/api/admin/users/${userId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      if (!res.ok) {
        setMessage(data.detail || "Error deleting user.");
        return;
      }
      setMessage(`User '${uName}' removed.`);
      await loadUsers();
    } catch (err) {
      setMessage("Failed to delete user.");
    }
  };

  const filteredUsers = users.filter(
    (u) =>
      u.name.toLowerCase().includes(search.toLowerCase()) ||
      u.email.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">👥 Attendees & User Management</h1>
          <p className="text-sm text-slate-500 mt-1">
            Admin console to manage registered participant and organizer accounts.
          </p>
        </div>

        <div className="flex items-center gap-2 bg-white border border-slate-200 rounded-xl px-3 py-1.5 w-64">
          <span>🔍</span>
          <input
            type="text"
            placeholder="Search by name or email..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full text-xs outline-hidden text-slate-800"
          />
        </div>
      </div>

      {message && (
        <div className="p-3 rounded-xl bg-indigo-50 border border-indigo-200 text-xs font-semibold text-indigo-800">
          {message}
        </div>
      )}

      {loading ? (
        <p className="text-sm text-slate-400 py-12 text-center">Loading user records...</p>
      ) : (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 uppercase tracking-wider font-semibold">
                <tr>
                  <th className="py-3.5 px-4">User</th>
                  <th className="py-3.5 px-4">Email Address</th>
                  <th className="py-3.5 px-4">Role</th>
                  <th className="py-3.5 px-4">Joined Date</th>
                  <th className="py-3.5 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredUsers.map((u) => (
                  <tr key={u.id} className="hover:bg-slate-50/70 transition">
                    <td className="py-3 px-4 font-bold text-slate-900 flex items-center gap-2.5">
                      <div className="h-7 w-7 rounded-full bg-indigo-600 text-white flex items-center justify-center font-bold text-xs">
                        {u.name.charAt(0).toUpperCase()}
                      </div>
                      <span>{u.name}</span>
                    </td>
                    <td className="py-3 px-4 text-slate-600">{u.email}</td>
                    <td className="py-3 px-4">
                      <span
                        className={`px-2 py-0.5 rounded-full font-bold text-[10px] ${
                          u.role === "ADMIN"
                            ? "bg-purple-100 text-purple-700"
                            : "bg-slate-100 text-slate-700"
                        }`}
                      >
                        {u.role}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-400">{u.created_at ? u.created_at.slice(0, 10) : "Active"}</td>
                    <td className="py-3 px-4 text-right">
                      {u.role !== "ADMIN" ? (
                        <button
                          onClick={() => handleDeleteUser(u.id, u.name)}
                          className="px-2.5 py-1 text-[11px] font-semibold text-rose-600 hover:text-rose-800 bg-rose-50 hover:bg-rose-100 rounded-lg transition"
                        >
                          Remove User
                        </button>
                      ) : (
                        <span className="text-[10px] font-semibold text-slate-400">Protected</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

