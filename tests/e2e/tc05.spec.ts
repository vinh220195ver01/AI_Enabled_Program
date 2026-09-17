import { test, expect } from "@playwright/test";
import { GitHubRepositoryPage } from "../pages/github-repository.page";
import { PlaywrightPage } from "../pages/playwright.page";

test("TC05 verify external GitHub repository link", async ({ page }) => {
  const playwrightPage = new PlaywrightPage(page);

  // Step 1: Open https://playwright.dev/
  await playwrightPage.openHomePage();
  // Expected Result: Playwright homepage is displayed successfully.
  await expect(page).toHaveTitle(/Playwright/);

  // Step 2: Locate the GitHub icon/link in the navigation bar.
  // Expected Result: GitHub link is visible in the navigation bar.
  await expect(playwrightPage.githubRepositoryLink).toBeVisible();

  // Step 3: Click the GitHub icon/link.
  const githubTab = await playwrightPage.openGitHubRepository();
  const githubRepositoryPage = new GitHubRepositoryPage(githubTab);
  // Expected Result: A new browser tab opens (external navigation).
  await expect(githubTab).toHaveURL("https://github.com/microsoft/playwright");

  // Step 4: Verify the new tab's URL matches "https://github.com/microsoft/playwright".
  // Expected Result: URL matches the expected GitHub repository address.
  await expect(githubTab).toHaveURL("https://github.com/microsoft/playwright");

  // Step 5: Verify the new tab's page title contains "playwright".
  // Expected Result: Correct GitHub repository page is loaded.
  await expect(githubTab).toHaveTitle(/playwright/i);

  // Step 6: Verify the repository page displays the star count element.
  // Expected Result: Star count/button is visible on the GitHub page.
  await expect(githubRepositoryPage.starCount).toBeVisible();

  // Step 7: Close the new tab and switch back to the original Playwright homepage tab.
  await githubRepositoryPage.close();
  // Expected Result: Original homepage tab is active and unaffected.
  await expect(playwrightPage.homepageHeading).toBeVisible();
});