/**
 * Tests for use-toast — pure reducer function
 *
 * PRD Reference: FRONTEND_GUIDELINES.md Section 4.3 (UI feedback)
 *
 * Tests the exported reducer() directly — no React rendering needed.
 */

import { describe, it, expect } from 'vitest';
import { reducer } from './use-toast';

// ============================================================================
// Helpers
// ============================================================================

function makeToast(id: string, overrides = {}) {
  return { id, open: true, ...overrides } as any;
}

function makeState(toasts: any[] = []) {
  return { toasts };
}

// ============================================================================
// ADD_TOAST
// ============================================================================

describe('use-toast reducer — ADD_TOAST', () => {
  it('adds toast to empty list', () => {
    const toast = makeToast('1');
    const result = reducer(makeState(), {
      type: 'ADD_TOAST',
      toast,
    });
    expect(result.toasts).toHaveLength(1);
    expect(result.toasts[0].id).toBe('1');
  });

  it('new toast is prepended', () => {
    const existing = makeToast('1');
    const newToast = makeToast('2');
    const result = reducer(makeState([existing]), {
      type: 'ADD_TOAST',
      toast: newToast,
    });
    expect(result.toasts[0].id).toBe('2');
  });

  it('respects TOAST_LIMIT of 1', () => {
    const existing = makeToast('1');
    const newToast = makeToast('2');
    const result = reducer(makeState([existing]), {
      type: 'ADD_TOAST',
      toast: newToast,
    });
    // TOAST_LIMIT is 1, so only the new toast remains
    expect(result.toasts).toHaveLength(1);
    expect(result.toasts[0].id).toBe('2');
  });
});

// ============================================================================
// UPDATE_TOAST
// ============================================================================

describe('use-toast reducer — UPDATE_TOAST', () => {
  it('updates existing toast by id', () => {
    const toast = makeToast('1', { title: 'Old' });
    const result = reducer(makeState([toast]), {
      type: 'UPDATE_TOAST',
      toast: { id: '1', title: 'New' },
    });
    expect(result.toasts[0].title).toBe('New');
  });

  it('does not modify other toasts', () => {
    const t1 = makeToast('1', { title: 'Keep' });
    const t2 = makeToast('2', { title: 'Change' });
    const result = reducer(makeState([t1, t2]), {
      type: 'UPDATE_TOAST',
      toast: { id: '2', title: 'Changed' },
    });
    expect(result.toasts[0].title).toBe('Keep');
    expect(result.toasts[1].title).toBe('Changed');
  });

  it('no-op for non-existent id', () => {
    const toast = makeToast('1', { title: 'Original' });
    const result = reducer(makeState([toast]), {
      type: 'UPDATE_TOAST',
      toast: { id: 'nope', title: 'New' },
    });
    expect(result.toasts[0].title).toBe('Original');
  });
});

// ============================================================================
// DISMISS_TOAST
// ============================================================================

describe('use-toast reducer — DISMISS_TOAST', () => {
  it('sets open=false for specific toast', () => {
    const toast = makeToast('1', { open: true });
    const result = reducer(makeState([toast]), {
      type: 'DISMISS_TOAST',
      toastId: '1',
    });
    expect(result.toasts[0].open).toBe(false);
  });

  it('sets open=false for all toasts when no id', () => {
    const t1 = makeToast('1', { open: true });
    const t2 = makeToast('2', { open: true });
    const result = reducer(makeState([t1, t2]), {
      type: 'DISMISS_TOAST',
    });
    expect(result.toasts.every((t: any) => t.open === false)).toBe(true);
  });

  it('does not affect other toasts when dismissing one', () => {
    const t1 = makeToast('1', { open: true });
    const t2 = makeToast('2', { open: true });
    const result = reducer(makeState([t1, t2]), {
      type: 'DISMISS_TOAST',
      toastId: '1',
    });
    expect(result.toasts[0].open).toBe(false);
    expect(result.toasts[1].open).toBe(true);
  });
});

// ============================================================================
// REMOVE_TOAST
// ============================================================================

describe('use-toast reducer — REMOVE_TOAST', () => {
  it('removes specific toast by id', () => {
    const t1 = makeToast('1');
    const t2 = makeToast('2');
    const result = reducer(makeState([t1, t2]), {
      type: 'REMOVE_TOAST',
      toastId: '1',
    });
    expect(result.toasts).toHaveLength(1);
    expect(result.toasts[0].id).toBe('2');
  });

  it('removes all toasts when no id', () => {
    const t1 = makeToast('1');
    const t2 = makeToast('2');
    const result = reducer(makeState([t1, t2]), {
      type: 'REMOVE_TOAST',
    });
    expect(result.toasts).toHaveLength(0);
  });

  it('no-op for non-existent id', () => {
    const toast = makeToast('1');
    const result = reducer(makeState([toast]), {
      type: 'REMOVE_TOAST',
      toastId: 'nope',
    });
    expect(result.toasts).toHaveLength(1);
  });
});
