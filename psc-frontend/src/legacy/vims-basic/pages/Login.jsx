// src/pages/Login.jsx
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/hooks/use-auth";

const Login = () => {
  const navigate = useNavigate();
  const { login, isLoading } = useAuth();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    try {
      await login({
        username: username.trim(),
        password: password.trim(),
      });

      // Navigate to home after successful login
      navigate("/vims-home", { replace: true });
    } catch (err) {
      setError(err?.response?.data?.message || err?.data?.detail || "Invalid credentials");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="w-full max-w-md bg-white p-6 rounded shadow">
        <h2 className="text-2xl font-semibold text-center mb-2">
          VIMS Login
        </h2>
        <p className="text-sm text-gray-500 text-center mb-6">
          Enter your credentials to continue
        </p>

        {error && (
          <div className="text-sm text-red-600 bg-red-50 p-2 rounded mb-4">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Username */}
          <div>
            <label className="block text-sm text-gray-600 mb-1">
              Username
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              className="w-full border rounded px-3 py-2 focus:outline-none focus:ring focus:ring-blue-300"
              placeholder="Enter your username"
            />
          </div>

          {/* Password */}
          <div>
            <label className="block text-sm text-gray-600 mb-1">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full border rounded px-3 py-2 focus:outline-none focus:ring focus:ring-blue-300"
              placeholder="••••••••"
            />
          </div >

          {/* Submit */}
         <div className="flex justify-center">
  <button
    type="submit"
    disabled={isLoading}
    className="cursor-pointer bg-blue-600 text-white py-2 px-8 rounded hover:bg-blue-700 disabled:opacity-50"
  >
    {isLoading ? "Logging in..." : "Login"}
  </button>
</div>
        </form>
      </div>
    </div>
  );
};

export default Login;
