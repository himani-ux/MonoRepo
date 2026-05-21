import { test } from "@playwright/test";

test.describe("Safety incident Phase 1", () => {
  test("renders create route, validates the form, and exposes the Phase 2 CTA", async () => {
    test.skip(
      true,
      "The handover workspace does not include the runnable VIMS React app or Playwright web server wiring.",
    );
  });
});
