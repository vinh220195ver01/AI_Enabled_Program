import { test, expect } from "@playwright/test";

test("TC03 verify dark/light theme toggle persists after reload", async ({ page }) => {
  // Step 1: Open https://playwright.dev/  Expected Result: Playwright homepage is displayed successfully.
  await page.goto("https://playwright.dev/");
  await expect(page).toHaveTitle(/Playwright/i);

  // Step 2: Identify the current theme mode (light or dark) via the page's color scheme/background.  Expected Result: Initial theme state is captured correctly.
  const toggle = page.getByRole("button", {
    name: /switch between dark and light mode/i,
  });
  await expect(toggle).toBeVisible();

  const getComputedTheme = async () =>
    page.evaluate(() => getComputedStyle(document.documentElement).colorScheme);

  const initialTheme = await getComputedTheme();

  // Step 3: Click the theme toggle icon in the navigation bar.  Expected Result: The theme switches (light to dark, or dark to light).
  let currentTheme = initialTheme;
  for (let i = 0; i < 3; i++) {
    await toggle.click();
    await page.waitForTimeout(300);
    currentTheme = await getComputedTheme();

    if (currentTheme !== initialTheme) {
      break;
    }
  }

  // Step 4: Verify the page background and text colors have changed accordingly.  Expected Result: Visual theme change is reflected on the page.
  await expect(currentTheme).not.toBe(initialTheme);

  // Step 5: Reload the page (F5).  Expected Result: Page reloads successfully.
  // Step 6: Verify the previously selected theme persists after reload.  Expected Result: Theme preference is retained (not reset to default).
  await page.reload();
  await expect.poll(getComputedTheme).toBe(currentTheme);

  // Step 7: Click the theme toggle icon again to revert.  Expected Result: The theme switches back to the original mode.
  await toggle.click();
  await page.waitForTimeout(300);
  await expect.poll(getComputedTheme).toBe(initialTheme);
});
