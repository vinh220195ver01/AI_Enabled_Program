import { test, expect } from "@playwright/test";

test("TC02 search for assertions from Playwright homepage", async ({ page }) => {
  // Step 1: Open https://playwright.dev/  Expected Result: Playwright homepage is displayed successfully.
  await page.goto("https://playwright.dev/");
  await expect(page).toHaveTitle(/Playwright/i);

  // Step 2: Click the search icon/box (or press Ctrl+K / Cmd+K) in the navigation bar.  Expected Result: The search dialog/modal opens.
  await page.getByRole("button", { name: /search/i }).click();

  const searchInput = page.locator(
    'input[placeholder*="Search" i], .DocSearch-Input, input[aria-label*="Search" i]',
  );

  // Step 3: Type "assertions" into the search input.  Expected Result: Search results related to "assertions" are displayed in real time.
  await expect(searchInput).toBeVisible();
  await searchInput.fill("assertions");

  // Step 4: Verify the search results list contains relevant documentation links (e.g., "Assertions").  Expected Result: At least one relevant result is visible in the list.
  const result = page.locator(".DocSearch-Hit").filter({ hasText: /Assertions/i }).first();
  await expect(result).toBeVisible();

  // Step 5: Click the first matching result from the search results.  Expected Result: The corresponding documentation page is opened and the search dialog closes.
  await result.click();

  // Step 6: Verify the current URL contains "/docs/".  Expected Result: URL matches a valid Playwright documentation path.
  await expect(page).toHaveURL(/\/docs\//);

  // Step 7: Verify the page heading matches the topic searched (e.g., "Assertions").  Expected Result: The correct heading is visible on the opened page.
  await expect(page.getByRole("heading", { name: "Assertions", exact: true })).toBeVisible();

  // Step 8: Verify the searched keyword ("assertion") appears within the page content.  Expected Result: Keyword occurrence is found in the page body/content.
  await expect(page.locator("body")).toContainText(/assertion/i);
});
