import { test, expect, Page } from "@playwright/test";
import path from "path";

// Helper: log in via Supabase (requires TEST_EMAIL / TEST_PASSWORD env vars)
async function login(page: Page) {
  const email = process.env.TEST_EMAIL ?? "";
  const password = process.env.TEST_PASSWORD ?? "";

  if (!email || !password) {
    test.skip(true, "TEST_EMAIL and TEST_PASSWORD env vars required for catalog tests");
    return;
  }

  await page.goto("/login");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: "Sign in" }).click();
  await page.waitForURL(/\/catalog/, { timeout: 10000 });
}

test.describe("Catalog", () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test("catalog page loads with grid or empty state", async ({ page }) => {
    await expect(page.getByText("My Wardrobe")).toBeVisible();
    const grid = page.getByTestId("catalog-grid");
    const empty = page.getByText(/wardrobe is empty/i);
    await expect(grid.or(empty)).toBeVisible();
  });

  test("search input filters the grid", async ({ page }) => {
    const searchInput = page.getByTestId("search-input");
    await expect(searchInput).toBeVisible();
    await searchInput.fill("zzz_no_match_xyz");
    await page.waitForTimeout(600);
    await expect(page.getByText(/No items match/i).or(page.getByText(/wardrobe is empty/i))).toBeVisible();
  });

  test("add item page renders upload form", async ({ page }) => {
    await page.goto("/catalog/add");
    await expect(page.getByTestId("upload-form")).toBeVisible();
    await expect(page.getByTestId("name-input")).toBeVisible();
    await expect(page.getByRole("button", { name: /Add to wardrobe/i })).toBeVisible();
  });

  test("upload form requires name and category before submit", async ({ page }) => {
    await page.goto("/catalog/add");
    await page.getByRole("button", { name: /Add to wardrobe/i }).click();
    // Should show error toast (photo required)
    await expect(page.locator("[data-sonner-toast]")).toBeVisible({ timeout: 3000 });
  });
});
