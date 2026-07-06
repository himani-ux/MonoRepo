import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { SessionReauthModal } from './session-reauth-modal';

describe('SessionReauthModal', () => {
  const onSubmit = vi.fn();
  const onLogout = vi.fn();

  beforeEach(() => {
    onSubmit.mockReset();
    onLogout.mockReset();
    onSubmit.mockResolvedValue(undefined);
  });

  it('test_feat_cert_rbac_012_renders_pms_style_overlay_with_prefilled_identifier', () => {
    render(
      <SessionReauthModal
        open
        identifier={{ label: 'Crew ID', value: 'CREW-9' }}
        isSubmitting={false}
        error={null}
        onSubmit={onSubmit}
        onLogout={onLogout}
      />
    );

    expect(screen.getByRole('dialog', { name: 'Session expired' })).toBeInTheDocument();
    expect(screen.getByLabelText('Crew ID')).toHaveValue('CREW-9');
    expect(screen.getByLabelText('Password')).toHaveValue('');
    expect(screen.getByText('Your work stays open after re-authentication.')).toBeInTheDocument();
  });

  it('test_feat_cert_rbac_012_submits_password_without_editing_prefilled_identifier', async () => {
    render(
      <SessionReauthModal
        open
        identifier={{ label: 'Employee ID', value: 'EMP-44' }}
        isSubmitting={false}
        error={null}
        onSubmit={onSubmit}
        onLogout={onLogout}
      />
    );

    fireEvent.change(screen.getByLabelText('Password'), {
      target: { value: 'secret-password' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Resume session' }));

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith('secret-password');
    });
  });
});
