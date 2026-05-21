import { test } from "@playwright/test";

test.describe("Safety incident Phase 2", () => {
  test("renders the phase 2 route, validates required fields, and exposes the office submit CTA", async () => {
    test.skip(
      true,
      "The handover workspace does not include the runnable VIMS React app or Playwright web server wiring.",
    );
  });
});
