import { test, expect } from "@playwright/test";

test("TC03 verify dark/light theme toggle persists after reload", async ({ page }) => {
  await page.goto("https://playwright.dev/");
  await expect(page).toHaveTitle(/Playwright/i);

  const toggle = page.getByRole("button", {
    name: /switch between dark and light mode/i,
  });

  await expect(toggle).toBeVisible();

  const getComputedTheme = async () =>
    page.evaluate(() => getComputedStyle(document.documentElement).colorScheme);

  const initialTheme = await getComputedTheme();
  let currentTheme = initialTheme;

  for (let i = 0; i < 3; i++) {
    await toggle.click();
    await page.waitForTimeout(300);
    currentTheme = await getComputedTheme();

    if (currentTheme !== initialTheme) {
      break;
    }
  }

  await expect(currentTheme).not.toBe(initialTheme);

  await page.reload();
  await expect.poll(getComputedTheme).toBe(currentTheme);

  await toggle.click();
  await page.waitForTimeout(300);
  await expect.poll(getComputedTheme).toBe(initialTheme);
});
