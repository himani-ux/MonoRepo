import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

const baseQuery = fetchBaseQuery({
  baseUrl: "http://localhost:8000/api/orb/api",
});

export const orbApi = createApi({
  reducerPath: "orbApi",
  baseQuery,
  tagTypes: ["Operations", "Codes", "Vessels", "Tanks", "LatestEntry"],
  endpoints: (builder) => ({
    // â”€â”€ VESSELS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    fetchVessels: builder.query({
      query: () => "/vessels/",
      transformResponse: (response) => {
        return Array.isArray(response) ? response : response.results || [];
      },
    }),

    // â”€â”€ CODES â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    fetchCodes: builder.query({
      query: () => "/codes/",
      transformResponse: (response) => {
        return Array.isArray(response) ? response : response.results || [];
      },
      providesTags: ["Codes"],
    }),

    // â”€â”€ TANKS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    fetchTanksForOrb: builder.query({
      query: ({ vesselId, orbCode }) =>
        `/tanks-for-orb/?vessel_id=${vesselId}&orb_code=${orbCode}`,
      transformResponse: (response) => {
        return Array.isArray(response) ? response : [];
      },
      providesTags: ["Tanks"],
    }),

    // â”€â”€ OPERATIONS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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

    // â”€â”€ LATEST ENTRY DATE â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    fetchLatestEntryDate: builder.query({
      query: ({ vesselId }) => `/latest-entry-date/?vessel_id=${vesselId}`,
      transformResponse: (response) => response.latest_date || null,
      providesTags: ["LatestEntry"],
    }),

    // â”€â”€ CREATE OPERATION â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    createOperation: builder.mutation({
      query: (payload) => ({
        url: "/operations/",
        method: "POST",
        body: payload,
      }),
      invalidatesTags: ["Operations"],
    }),

    // â”€â”€ UPDATE OPERATION (PATCH) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    updateOperation: builder.mutation({
      query: ({ id, payload }) => ({
        url: `/operations/${id}/update-group/`,
        method: "PATCH",
        body: payload,
      }),
      invalidatesTags: ["Operations"],
    }),

    // â”€â”€ DELETE OPERATION (Soft Delete) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    deleteOperation: builder.mutation({
      query: (id) => ({
        url: `/operations/${id}/`,
        method: "PATCH",
        body: { is_deleted: true },
      }),
      invalidatesTags: ["Operations"],
    }),

    // â”€â”€ APPROVE OPERATION â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    approveOperation: builder.mutation({
      query: ({ id, approvedBy }) => ({
        url: `/operations/${id}/approve/`,
        method: "PATCH",
        body: { approved_by: approvedBy },
      }),
      invalidatesTags: ["Operations"],
    }),

    // â”€â”€ REJECT OPERATION â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    rejectOperation: builder.mutation({
      query: ({ id, rejectedBy }) => ({
        url: `/operations/${id}/reject/`,
        method: "PATCH",
        body: { rejected_by: rejectedBy },
      }),
      invalidatesTags: ["Operations"],
    }),

    // â”€â”€ UPDATE PRINT STATUS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    updatePrintStatus: builder.mutation({
      query: (payload) => ({
        url: "/update-print-status/",
        method: "POST",
        body: payload,
      }),
    }),

    // â”€â”€ SAVE PDF METADATA â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    savePDFMetadata: builder.mutation({
      query: (payload) => ({
        url: "/save-pdf-metadata/",
        method: "POST",
        body: payload,
      }),
    }),

    // â”€â”€ GET INTERNAL IP â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    getInternalIP: builder.query({
      query: () => "/get-internal-ip/",
      transformResponse: (response) => response.internal_ip || "Unknown IP",
    }),

    // â”€â”€ GET LAST PAGE NUMBER â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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
