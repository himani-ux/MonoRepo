/**
 * Tests for error-state reusable views used by list/detail pages.
 *
 * PRD Reference: Docs/PRD.md Section 2.1 - FEAT-INS-011
 */

import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import {
  ErrorState,
  NetworkErrorState,
  NotFoundErrorState,
} from './error-state';

describe('ErrorState', () => {
  it('test_feat_ins_011_generic_error_state_renders_retry_button_when_handler_provided', () => {
    const onRetry = vi.fn();
    render(
      <ErrorState
        title="Load failed"
        message="Please retry."
        onRetry={onRetry}
        retryLabel="Retry now"
      />
    );

    fireEvent.click(screen.getByRole('button', { name: 'Retry now' }));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it('test_feat_ins_011_network_error_variant_uses_connection_copy', () => {
    render(<NetworkErrorState />);
    expect(screen.getByText('Unable to connect')).toBeInTheDocument();
    expect(screen.getByText('Check your internet connection and try again.')).toBeInTheDocument();
  });

  it('test_feat_ins_011_not_found_variant_renders_entity_name_and_back_action', () => {
    const onGoBack = vi.fn();
    render(<NotFoundErrorState entityName="Inspection" onGoBack={onGoBack} />);

    expect(screen.getByText('Inspection not found')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Go Back' }));
    expect(onGoBack).toHaveBeenCalledTimes(1);
  });
});

