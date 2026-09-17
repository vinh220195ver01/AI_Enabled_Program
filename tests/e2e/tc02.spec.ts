import { test, expect } from "@playwright/test";
import { PlaywrightPage } from "../pages/playwright.page";

test("TC02 search for assertions from Playwright homepage", async ({ page }) => {
  const playwrightPage = new PlaywrightPage(page);

  // Step 1: Open https://playwright.dev/
  await playwrightPage.openHomePage();
  // Expected Result: Playwright homepage is displayed successfully.
  await expect(page).toHaveTitle(/Playwright/i);

  // Step 2: Click the search icon/box (or press Ctrl+K / Cmd+K) in the navigation bar.
  await playwrightPage.openSearch();
  // Expected Result: The search dialog/modal opens.
  await expect(playwrightPage.searchInput).toBeVisible();

  // Step 3: Type "assertions" into the search input.
  await playwrightPage.searchFor("assertions");
  // Expected Result: Search results related to "assertions" are displayed in real time.
  await expect(playwrightPage.searchResult).toBeVisible();

  // Step 4: Verify the search results list contains relevant documentation links (e.g., "Assertions").
  // Expected Result: At least one relevant result is visible in the list.
  await expect(playwrightPage.searchResult).toBeVisible();

  // Step 5: Click the first matching result from the search results.
  await playwrightPage.openSearchResult();
  // Expected Result: The corresponding documentation page is opened and the search dialog closes.
  await expect(page).toHaveURL(/\/docs\//);

  // Step 6: Verify the current URL contains "/docs/".
  // Expected Result: URL matches a valid Playwright documentation path.
  await expect(page).toHaveURL(/\/docs\//);

  // Step 7: Verify the page heading matches the topic searched (e.g., "Assertions").
  // Expected Result: The correct heading is visible on the opened page.
  await expect(playwrightPage.assertionsHeading).toBeVisible();

  // Step 8: Verify the searched keyword ("assertion") appears within the page content.
  // Expected Result: Keyword occurrence is found in the page body/content.
  await expect(playwrightPage.body).toContainText(/assertion/i);
});
