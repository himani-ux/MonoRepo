import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  certsApi,
  type CertAuditorAccessCreatePayload,
  type CertAuditorAccessExpiryPayload,
} from '@/lib/api/certs';

export const certAuditorAccessKeys = {
  all: ['certs', 'auditor-access'] as const,
  grants: () => [...certAuditorAccessKeys.all, 'grants'] as const,
  grant: (id: string) => [...certAuditorAccessKeys.all, 'grant', id] as const,
  portal: (sessionToken: string) => [...certAuditorAccessKeys.all, 'portal', sessionToken] as const,
  portalVessels: (sessionToken: string) => [...certAuditorAccessKeys.portal(sessionToken), 'vessels'] as const,
  portalCerts: (sessionToken: string, imo: string) => [...certAuditorAccessKeys.portal(sessionToken), 'certs', imo] as const,
  portalCert: (sessionToken: string, certId: string) => [...certAuditorAccessKeys.portal(sessionToken), 'cert', certId] as const,
};

export function useAuditorAccessGrants(enabled = true) {
  return useQuery({
    queryKey: certAuditorAccessKeys.grants(),
    queryFn: () => certsApi.getAuditorAccessGrants(),
    enabled,
    staleTime: 60 * 1000,
  });
}

export function useAuditorAccessGrant(id: string | undefined) {
  return useQuery({
    queryKey: certAuditorAccessKeys.grant(id ?? ''),
    queryFn: () => certsApi.getAuditorAccessGrant(id!),
    enabled: Boolean(id),
    staleTime: 60 * 1000,
  });
}

export function useCreateAuditorAccessGrant() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CertAuditorAccessCreatePayload) => certsApi.createAuditorAccessGrant(payload),
    onSuccess: (grant) => {
      queryClient.invalidateQueries({ queryKey: certAuditorAccessKeys.grants() });
      queryClient.setQueryData(certAuditorAccessKeys.grant(grant.id), grant);
    },
  });
}

export function useUpdateAuditorAccessGrantExpiry(id: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CertAuditorAccessExpiryPayload) => certsApi.updateAuditorAccessGrantExpiry(id!, payload),
    onSuccess: (grant) => {
      queryClient.invalidateQueries({ queryKey: certAuditorAccessKeys.grants() });
      queryClient.setQueryData(certAuditorAccessKeys.grant(grant.id), grant);
    },
  });
}

export function useAuditorSignup(token: string | undefined) {
  return useQuery({
    queryKey: [...certAuditorAccessKeys.all, 'signup', token ?? ''],
    queryFn: () => certsApi.signupAuditor(token!),
    enabled: Boolean(token),
    retry: false,
    staleTime: Infinity,
  });
}

export function useAuditorVessels(sessionToken: string | undefined) {
  return useQuery({
    queryKey: certAuditorAccessKeys.portalVessels(sessionToken ?? ''),
    queryFn: () => certsApi.getAuditorVessels(sessionToken!),
    enabled: Boolean(sessionToken),
    retry: false,
    staleTime: 60 * 1000,
  });
}

export function useAuditorVesselCerts(sessionToken: string | undefined, imo: string | undefined) {
  return useQuery({
    queryKey: certAuditorAccessKeys.portalCerts(sessionToken ?? '', imo ?? ''),
    queryFn: () => certsApi.getAuditorVesselCerts(sessionToken!, imo!),
    enabled: Boolean(sessionToken && imo),
    retry: false,
    staleTime: 60 * 1000,
  });
}

export function useAuditorCert(sessionToken: string | undefined, certId: string | undefined) {
  return useQuery({
    queryKey: certAuditorAccessKeys.portalCert(sessionToken ?? '', certId ?? ''),
    queryFn: () => certsApi.getAuditorCert(sessionToken!, certId!),
    enabled: Boolean(sessionToken && certId),
    retry: false,
    staleTime: 60 * 1000,
  });
}

export function useGenerateAuditorPrint(sessionToken: string | undefined) {
  return useMutation({
    mutationFn: (payload: { trackedItemIds?: string[] }) => certsApi.generateAuditorPrint(sessionToken!, payload),
  });
}
