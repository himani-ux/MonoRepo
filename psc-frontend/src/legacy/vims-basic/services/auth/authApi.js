import { createApi } from "@reduxjs/toolkit/query/react";
import {baseQueryWithReauth} from "../baseApi";

export const authApi = createApi({
  reducerPath: "authApi",
  baseQuery: baseQueryWithReauth,
  endpoints: (builder) => ({
    login: builder.mutation({
      query: (credentials) => ({
        url: "/auth/login/",
        method: "POST",
        body: credentials,
      }),
      transformResponse: (response) => {
        const payload = response?.data ?? response ?? {};
        return {
          accessToken: payload.access,
          refreshToken: payload.refresh,
          user: payload.user,
        };
      },
    }),
  }),
});

export const { useLoginMutation } = authApi;
