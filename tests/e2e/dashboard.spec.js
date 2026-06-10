const { test, expect } = require("@playwright/test");

test.describe("Doctor Dashboard Browser E2E Tests", () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the dashboard URL
    await page.goto("/");
  });

  test("loads main layout and displays sidebar headers", async ({ page }) => {
    // Confirm sidebar title exists
    await expect(page.locator("h1")).toContainText("AutiScreen");
    await expect(page.locator("aside")).toContainText("Doctor Dashboard · India");
    
    // Check navigation buttons are active
    const flaggedBtn = page.locator("button:has-text('Flagged')");
    const allBtn = page.locator("button:has-text('All Sessions')");
    
    await expect(flaggedBtn).toBeVisible();
    await expect(allBtn).toBeVisible();
  });

  test("can toggle views between Flagged and All Sessions", async ({ page }) => {
    const flaggedBtn = page.locator("button:has-text('Flagged')");
    const allBtn = page.locator("button:has-text('All Sessions')");

    // Click 'All Sessions'
    await allBtn.click();
    await expect(allBtn).toHaveClass(/text-blue-700/);

    // Click 'Flagged'
    await flaggedBtn.click();
    await expect(flaggedBtn).toHaveClass(/text-red-700/);
  });

  test("displays prompt message when no case is selected", async ({ page }) => {
    const mainPanel = page.locator("main");
    await expect(mainPanel).toContainText("Select a case to review");
  });

  test("can select a case and submit clinical notes and judgment", async ({ page }) => {
    // Note: This test assumes there is at least one seeded session in the list.
    // If list is empty, we assert the empty state message.
    const caseList = page.locator("aside >> text=No sessions yet.");
    const firstCase = page.locator("aside >> div >> p").first();

    if (await firstCase.isVisible()) {
      // Click first case
      await firstCase.click();

      // Confirm main details panel renders child information
      await expect(page.locator("main >> h2")).toBeVisible();
      await expect(page.locator("main >> text=Behavioral Scores")).toBeVisible();
      await expect(page.locator("main >> text=Questionnaire")).toBeVisible();

      // Make a judgment selection
      const monitoringBtn = page.locator("button:has-text('Needs Monitoring')");
      await monitoringBtn.click();

      // Input notes
      const notesField = page.locator("textarea");
      await notesField.fill("Observation: showing repetitive patterns in Task A.");

      // Click save
      const saveBtn = page.locator("button:has-text('Save Judgment')");
      await saveBtn.click();

      // Confirm checkmark/saved text renders on button
      await expect(page.locator("button:has-text('Saved')")).toBeVisible();
    } else {
      console.log("No cases found in DB. Skipping interaction assertions.");
      await expect(caseList).toBeVisible();
    }
  });
});
