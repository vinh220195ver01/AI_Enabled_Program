import { test, expect } from "@playwright/test";

test("TC01 navigate from Playwright homepage to Installation docs", async ({
  page,
}) => {
  await page.goto("https://playwright.dev/");
  await expect(page).toHaveTitle(/Playwright/);
  await expect(
    page.getByRole("heading", { name: /Playwright/i }).first(),
  ).toBeVisible();

  await page.getByRole("link", { name: "Get started" }).click();
  await page.getByRole("link", { name: "Installation", exact: true }).click();

  await expect(page).toHaveURL("https://playwright.dev/docs/intro");
  await expect(
    page.getByRole("heading", { name: "Installation", exact: true }),
  ).toBeVisible();
  await expect(page.getByRole("heading", { name: "Introduction" })).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Installing Playwright" }),
  ).toBeVisible();
  await expect(page.getByText("npm init playwright@latest", { exact: true })).toBeVisible();
});
