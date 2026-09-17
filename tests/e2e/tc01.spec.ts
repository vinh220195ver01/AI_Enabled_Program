import { test, expect } from "@playwright/test";

test("TC01 navigate from Playwright homepage to Installation docs", async ({
  page,
}) => {
  // Step 1: Open https://playwright.dev/  Expected Result: Playwright homepage is displayed successfully.
  await page.goto("https://playwright.dev/");
  await expect(page).toHaveTitle(/Playwright/);
  await expect(
    page.getByRole("heading", { name: /Playwright/i }).first(),
  ).toBeVisible();

  // Step 2: Verify the page contains the Playwright branding/title.  Expected Result: Playwright branding/title is visible.
  // Step 3: Click the Get started navigation link.  Expected Result: The Getting Started documentation page/section is opened.
  await page.getByRole("link", { name: "Get started" }).click();

  // Step 4: Click the Installation documentation link.  Expected Result: The Installation documentation page is opened.
  await page.getByRole("link", { name: "Installation", exact: true }).click();

  // Step 5: Verify the current URL is https://playwright.dev/docs/intro.  Expected Result: URL matches the expected Installation documentation URL.
  await expect(page).toHaveURL("https://playwright.dev/docs/intro");

  // Step 6: Verify the page heading is Installation.  Expected Result: An Installation heading is visible.
  await expect(
    page.getByRole("heading", { name: "Installation", exact: true }),
  ).toBeVisible();

  // Step 7: Verify the page contains the Introduction section.  Expected Result: The Introduction section is visible.
  await expect(page.getByRole("heading", { name: "Introduction" })).toBeVisible();

  // Step 8: Verify the page contains information about installing Playwright.  Expected Result: Installation instructions are displayed.
  await expect(
    page.getByRole("heading", { name: "Installing Playwright" }),
  ).toBeVisible();

  // Step 9: Verify the page contains the npm init playwright@latest installation command.  Expected Result: The npm installation command is displayed.
  await expect(page.getByText("npm init playwright@latest", { exact: true })).toBeVisible();
});
