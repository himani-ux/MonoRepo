import { renderHook } from "@testing-library/react";
import { act } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  useDraftAutosave,
  type SafetyDraftStorageAdapter,
} from "../../../src/hooks/safety/use-draft-autosave";
import { useSafetyIncidentDraftStore } from "../../../src/stores/safety/incident-draft-store";

describe("useDraftAutosave", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    useSafetyIncidentDraftStore.getState().reset();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("restores persisted values and saves every 30 seconds", async () => {
    const storage: SafetyDraftStorageAdapter<Record<string, unknown>> = {
      clear: vi.fn(async () => undefined),
      load: vi.fn(async () => ({
        phase: 3,
        recordId: "42:phase:3",
        updatedAt: "2026-04-27T12:00:00.000Z",
        values: { narrative: "restored" },
      })),
      save: vi.fn(async () => undefined),
    };
    const onRestore = vi.fn();

    renderHook(() =>
      useDraftAutosave({
        onRestore,
        phase: 3,
        recordId: "42",
        storage,
        values: { narrative: "current" },
      }),
    );

    await act(async () => {
      await Promise.resolve();
    });

    expect(storage.load).toHaveBeenCalledWith("42:phase:3");
    expect(onRestore).toHaveBeenCalledWith({ narrative: "restored" });

    await act(async () => {
      vi.advanceTimersByTime(30_000);
      await Promise.resolve();
    });

    expect(storage.save).toHaveBeenCalledTimes(1);
    expect(storage.save).toHaveBeenCalledWith(
      expect.objectContaining({
        phase: 3,
        recordId: "42:phase:3",
        values: { narrative: "current" },
      }),
    );
  });
});
