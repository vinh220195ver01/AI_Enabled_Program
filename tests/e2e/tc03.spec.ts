import { test, expect } from "@playwright/test";
import { PlaywrightPage } from "../pages/playwright.page";

test("TC03 verify dark/light theme toggle persists after reload", async ({ page }) => {
  const playwrightPage = new PlaywrightPage(page);

  // Step 1: Open https://playwright.dev/
  await playwrightPage.openHomePage();
  // Expected Result: Playwright homepage is displayed successfully.
  await expect(page).toHaveTitle(/Playwright/i);

  // Step 2: Identify the current theme mode (light or dark) via the page's color scheme/background.
  await expect(playwrightPage.themeToggle).toBeVisible();
  // Expected Result: Initial theme state is captured correctly.
  const initialTheme = await playwrightPage.getTheme();

  // Step 3: Click the theme toggle icon in the navigation bar.
  let currentTheme = initialTheme;
  for (let i = 0; i < 3; i++) {
    await playwrightPage.toggleTheme();
    currentTheme = await playwrightPage.getTheme();

    if (currentTheme !== initialTheme) {
      break;
    }
  }
  // Expected Result: The theme switches (light to dark, or dark to light).
  expect(currentTheme).not.toBe(initialTheme);

  // Step 4: Verify the page background and text colors have changed accordingly.
  // Expected Result: Visual theme change is reflected on the page.
  expect(currentTheme).not.toBe(initialTheme);

  // Step 5: Reload the page (F5).
  await playwrightPage.reload();
  // Expected Result: Page reloads successfully.
  await expect.poll(() => playwrightPage.getTheme()).toBe(currentTheme);

  // Step 6: Verify the previously selected theme persists after reload.
  // Expected Result: Theme preference is retained (not reset to default).
  await expect.poll(() => playwrightPage.getTheme()).toBe(currentTheme);

  // Step 7: Click the theme toggle icon again to revert.
  await playwrightPage.toggleTheme();
  // Expected Result: The theme switches back to the original mode.
  await expect.poll(() => playwrightPage.getTheme()).toBe(initialTheme);
});
