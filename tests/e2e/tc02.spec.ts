import { test, expect } from "@playwright/test";

test("TC02 search for assertions from Playwright homepage", async ({ page }) => {
  await page.goto("https://playwright.dev/");
  await expect(page).toHaveTitle(/Playwright/i);

  await page.getByRole("button", { name: /search/i }).click();

  const searchInput = page.locator(
    'input[placeholder*="Search" i], .DocSearch-Input, input[aria-label*="Search" i]',
  );
  await expect(searchInput).toBeVisible();

  await searchInput.fill("assertions");

  const result = page.locator(".DocSearch-Hit").filter({ hasText: /Assertions/i }).first();
  await expect(result).toBeVisible();

  await result.click();

  await expect(page).toHaveURL(/\/docs\//);
  await expect(page.getByRole("heading", { name: "Assertions", exact: true })).toBeVisible();
  await expect(page.locator("body")).toContainText(/assertion/i);
});
