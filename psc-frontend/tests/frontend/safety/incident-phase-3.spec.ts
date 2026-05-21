import { test } from "@playwright/test";

test.describe("Safety incident Phase 3", () => {
  test("renders the Phase 3 tab shell and keeps the evidence widgets visible", async () => {
    test.skip(
      true,
      "The handover workspace does not include the runnable VIMS React app or Playwright web server wiring.",
    );
  });
});
