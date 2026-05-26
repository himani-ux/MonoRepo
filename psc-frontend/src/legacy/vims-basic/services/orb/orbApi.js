import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

const baseQuery = fetchBaseQuery({
  baseUrl: "/api/orb/api",
});

export const orbApi = createApi({
  reducerPath: "orbApi",
  baseQuery,
  tagTypes: ["Operations", "Codes", "Vessels", "Tanks", "LatestEntry"],
  endpoints: (builder) => ({
    // ── VESSELS ──────────────────────────────────────────────────────────────
    fetchVessels: builder.query({
      query: () => "/vessels/",
      transformResponse: (response) => {
        return Array.isArray(response) ? response : response.results || [];
      },
    }),

    // ── CODES ────────────────────────────────────────────────────────────────
    fetchCodes: builder.query({
      query: () => "/codes/",
      transformResponse: (response) => {
        return Array.isArray(response) ? response : response.results || [];
      },
      providesTags: ["Codes"],
    }),

    // ── TANKS ────────────────────────────────────────────────────────────────
    fetchTanksForOrb: builder.query({
      query: ({ vesselId, orbCode }) =>
        `/tanks-for-orb/?vessel_id=${vesselId}&orb_code=${orbCode}`,
      transformResponse: (response) => {
        return Array.isArray(response) ? response : [];
      },
      providesTags: ["Tanks"],
    }),

    // ── OPERATIONS ───────────────────────────────────────────────────────────
    fetchOperations: builder.query({
      query: ({ vesselId, status, isDeleted = false }) => {
        let url = `/operations/?vessel_id=${vesselId}&is_deleted=${isDeleted}`;
        if (status) {
          url += `&status=${status}`;
        }
        return url;
      },
      transformResponse: (response) => {
        return Array.isArray(response) ? response : response.results || [];
      },
      providesTags: ["Operations"],
    }),

    // ── LATEST ENTRY DATE ────────────────────────────────────────────────────
    fetchLatestEntryDate: builder.query({
      query: ({ vesselId }) => `/latest-entry-date/?vessel_id=${vesselId}`,
      transformResponse: (response) => response.latest_date || null,
      providesTags: ["LatestEntry"],
    }),

    // ── CREATE OPERATION ─────────────────────────────────────────────────────
    createOperation: builder.mutation({
      query: (payload) => ({
        url: "/operations/",
        method: "POST",
        body: payload,
      }),
      invalidatesTags: ["Operations"],
    }),

    // ── UPDATE OPERATION (PATCH) ─────────────────────────────────────────────
    updateOperation: builder.mutation({
      query: ({ id, payload }) => ({
        url: `/operations/${id}/update-group/`,
        method: "PATCH",
        body: payload,
      }),
      invalidatesTags: ["Operations"],
    }),

    // ── DELETE OPERATION (Soft Delete) ───────────────────────────────────────
    deleteOperation: builder.mutation({
      query: (id) => ({
        url: `/operations/${id}/`,
        method: "PATCH",
        body: { is_deleted: true },
      }),
      invalidatesTags: ["Operations"],
    }),

    // ── APPROVE OPERATION ────────────────────────────────────────────────────
    approveOperation: builder.mutation({
      query: ({ id, approvedBy }) => ({
        url: `/operations/${id}/approve/`,
        method: "PATCH",
        body: { approved_by: approvedBy },
      }),
      invalidatesTags: ["Operations"],
    }),

    // ── REJECT OPERATION ─────────────────────────────────────────────────────
    rejectOperation: builder.mutation({
      query: ({ id, rejectedBy }) => ({
        url: `/operations/${id}/reject/`,
        method: "PATCH",
        body: { rejected_by: rejectedBy },
      }),
      invalidatesTags: ["Operations"],
    }),

    // ── UPDATE PRINT STATUS ──────────────────────────────────────────────────
    updatePrintStatus: builder.mutation({
      query: (payload) => ({
        url: "/update-print-status/",
        method: "POST",
        body: payload,
      }),
    }),

    // ── SAVE PDF METADATA ────────────────────────────────────────────────────
    savePDFMetadata: builder.mutation({
      query: (payload) => ({
        url: "/save-pdf-metadata/",
        method: "POST",
        body: payload,
      }),
    }),

    // ── GET INTERNAL IP ──────────────────────────────────────────────────────
    getInternalIP: builder.query({
      query: () => "/get-internal-ip/",
      transformResponse: (response) => response.internal_ip || "Unknown IP",
    }),

    // ── GET LAST PAGE NUMBER ─────────────────────────────────────────────────
    getLastPageNumber: builder.query({
      query: ({ vesselId }) => `/get_last_page_number/?vessel_id=${vesselId}`,
      transformResponse: (response) => response.last_page || 0,
    }),
  }),
});

export const {
  useFetchVesselsQuery,
  useFetchCodesQuery,
  useFetchTanksForOrbQuery,
  useFetchOperationsQuery,
  useFetchLatestEntryDateQuery,
  useCreateOperationMutation,
  useUpdateOperationMutation,
  useDeleteOperationMutation,
  useApproveOperationMutation,
  useRejectOperationMutation,
  useUpdatePrintStatusMutation,
  useSavePDFMetadataMutation,
  useGetInternalIPQuery,
  useGetLastPageNumberQuery,
} = orbApi;
