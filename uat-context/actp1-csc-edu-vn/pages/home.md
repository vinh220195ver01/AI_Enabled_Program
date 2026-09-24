# Page: Home

- **URL:** <https://actp1.csc.edu.vn/>
- **Purpose:** Storefront landing page — hero banner, brand blurb, latest products grid, and a
  "Be inspired" secondary product grid.
- **Last verified:** 2026-09-24
- **WebMCP tools:** none observed

## Key elements

| Element | Locator | Notes |
|---|---|---|
| Primary nav — Home | `getByRole('link', { name: 'Home' })` | → `/` |
| Primary nav — Shop | `getByRole('link', { name: 'Shop' })` | → `/shop/`; has an "Open Submenu" dropdown button next to it |
| Primary nav — Blog | `getByRole('link', { name: 'Blog' })` | → `/blog/` (not explored) |
| Primary nav — My account | `getByRole('link', { name: 'My account' })` | → `/my-account/` |
| Header search toggle | `getByRole('link', { name: 'Search' })` | Reveals an inline search box overlay, see [flows/search.md](../flows/search.md) |
| Cart link | `getByRole('link', { name: /Cart \d+/ })` | → `/cart/`; badge count updates after add-to-cart |
| "SEE ALL PRODUCTS" (hero) | `getByRole('link', { name: 'SEE ALL PRODUCTS' })` | → `/shop/` |
| Latest products grid | product name links, e.g. `getByRole('link', { name: 'Bold Statement Graphic Tee Bold Statement Graphic Tee' })` | Accessible name repeats the title (image alt + text) |

## Forms

None on this page (header search box is covered separately in the Search flow).

## Notable states

- Sale items show both an original (struck-through) and current price, each duplicated as
  screen-reader-only text ("Original price was: $X.", "Current price is: $Y."). Tests matching on
  visible price text should scope to the `insertion`/`deletion` elements or use the plain `$X.XX`
  text, not the full accessible name.

## Stale / unverified

- The "Sunset Glow Utility Dress" link in both the Latest Products and Be Inspired grids points to
  `#dead-link` instead of a product page — appears to be an intentional demo-site defect, not
  something introduced by this session.
