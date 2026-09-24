# Page: Shop

- **URL:** <https://actp1.csc.edu.vn/shop/>
- **Purpose:** Full product catalog listing with sidebar category filters, search box, sort order,
  and pagination.
- **Last verified:** 2026-09-24
- **WebMCP tools:** none observed

## Key elements

| Element | Locator | Notes |
|---|---|---|
| Sidebar search box | `getByRole('searchbox', { name: 'Search' })` | Separate instance from header search overlay |
| Category filter links | `getByRole('link', { name: 'Clothing' })` etc. | Sidebar lists: Blouse, Clothing, Dresses, Tshirt, Uncategorized |
| Sort dropdown | `getByRole('combobox', { name: 'Shop order' })` | Options: Default sorting, popularity, average rating, latest, price low→high, price high→low (site copy has typos: "Defult", "popularty", "avrage") |
| Pagination | `getByRole('navigation', { name: 'Product Pagination' })` | Page 1 of 2, "→" next link |
| Product card link | e.g. `getByRole('link', { name: /Bold Statement Graphic Tee/ })` | Accessible name includes "Sale!" prefix and price text when on sale |

## Forms

### Sidebar search

| Field | Type | Required | Validation |
|---|---|---|---|
| Search box | text | no | Not exercised this pass — see [flows/search.md](../flows/search.md) for the header equivalent |

## Notable states

- Breadcrumb shows `Home \ Shop`. Result count text reads "Showwing 1–8 of 9 results" (typo present
  in live site copy — match on partial text, not exact string, if asserting on it).
- 9 total products across 2 pages (8 on page 1).

## Stale / unverified

- "Classic Striped Knit Blouse" card links to `/shop/midnight-bloom-crochet-dress/` (wrong product —
  URL/title mismatch on the live site, not a test bug).
- "Sophisticated Striped Midi Dress" card links to `#dead-link`.
- Page 2 of results was not explored in this pass.
