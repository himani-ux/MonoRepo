import { describe, expect, it, vi } from 'vitest';

const queryMocks = vi.hoisted(() => ({
  invalidateQueries: vi.fn(),
  useMutation: vi.fn(),
  useQuery: vi.fn(),
}));

vi.mock('@tanstack/react-query', () => ({
  useMutation: (options: unknown) => queryMocks.useMutation(options),
  useQuery: (options: unknown) => queryMocks.useQuery(options),
  useQueryClient: () => ({ invalidateQueries: queryMocks.invalidateQueries }),
}));

import {
  auditScanValidationKeys,
  useAuditScanValidationAction,
  useAuditScanValidationQueue,
} from './use-audit-scan-validation';

describe('use-audit-scan-validation hooks', () => {
  it('configures the scan-validation queue query', () => {
    queryMocks.useQuery.mockReturnValue({ data: undefined });

    useAuditScanValidationQueue();

    expect(queryMocks.useQuery).toHaveBeenCalledWith(
      expect.objectContaining({
        queryKey: auditScanValidationKeys.queue(),
      })
    );
  });

  it('invalidates the queue after validation action success', () => {
    queryMocks.useMutation.mockReturnValue({ mutateAsync: vi.fn() });

    useAuditScanValidationAction();
    const actionOptions = queryMocks.useMutation.mock.calls[0][0];
    actionOptions.onSuccess();

    expect(queryMocks.invalidateQueries).toHaveBeenCalledWith({
      queryKey: auditScanValidationKeys.queue(),
    });
  });
});
