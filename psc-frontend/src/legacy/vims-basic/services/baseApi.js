import { fetchBaseQuery } from "@reduxjs/toolkit/query/react";
import { useAuthStore } from "@/stores/auth-store";

const baseQuery = fetchBaseQuery({
  baseUrl: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api",
  prepareHeaders: (headers) => {
    const token = useAuthStore.getState().tokens?.access;
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }
    return headers;
  },
});

export const baseQueryWithReauth = async (args, api, extraOptions) => {
  let result = await baseQuery(args, api, extraOptions);

  if (result?.error?.status === 401) {
    const authStore = useAuthStore.getState();
    const refreshToken = authStore.tokens?.refresh;

    if (!refreshToken) {
      await authStore.logout();
      return result;
    }

    const refreshedTokens = await authStore.refreshTokens();

    if (refreshedTokens?.access) {
      result = await baseQuery(args, api, extraOptions);
    } else {
      await authStore.logout();
    }
  }

  return result;
};
