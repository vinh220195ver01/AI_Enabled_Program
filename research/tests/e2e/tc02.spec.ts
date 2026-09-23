import { test, expect } from "@playwright/test";
import { PlaywrightPage } from "../pages/playwright.page";

test("TC02 - Verify Playwright Documentation Search", async ({ page }) => {
  const playwrightPage = new PlaywrightPage(page);

  await playwrightPage.openHomePage();
  // Step 1: Open https://playwright.dev/
  // Expected Result: Playwright homepage is displayed successfully.
  await expect(page).toHaveTitle(/Playwright/i);
  await expect(playwrightPage.homepageHeading).toBeVisible();

  // Step 2: Click the search icon/box (or press Ctrl+K / Cmd+K) in the navigation bar.
  // Expected Result: The search dialog/modal opens.
  await playwrightPage.openSearch();
  await expect(playwrightPage.searchInput).toBeVisible();

  // Step 3: Type "assertions" into the search input.
  // Expected Result: Search results related to "assertions" are displayed in real time.
  await playwrightPage.searchFor("assertions");
  await expect(playwrightPage.searchResult).toBeVisible();

  // Step 4: Verify the search results list contains relevant documentation links (e.g., "Assertions").
  // Expected Result: At least one relevant result is visible in the list.
  await expect(playwrightPage.searchResult).toContainText(/Assertions/i);

  // Step 5: Click the first matching result from the search results.
  // Expected Result: The corresponding documentation page is opened and the search dialog closes.
  await playwrightPage.openSearchResult();
  await expect(playwrightPage.searchInput).toBeHidden();

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
