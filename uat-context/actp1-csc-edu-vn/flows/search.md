# Flow: Search

- **Goal:** Find a product via the header search widget.
- **Starting page:** [pages/home.md](../pages/home.md) (search icon is present in the header on every page)
- **Last verified:** 2026-09-24

## Steps

1. On any page, click the header "Search" link (`getByRole('link', { name: 'Search' })`) — it is not
   a real navigation link (`href="#"`), it's a toggle.
2. An inline overlay expands next to it containing:
   - `getByRole('searchbox', { name: 'Search' })` with placeholder text "Search for..."
   - `getByRole('button', { name: 'Search' })` to submit
   - A "Close" button to collapse it back
3. Submitting was not exercised this pass — result page URL/structure is undocumented.

Note: [Shop](../pages/shop.md) has its own separate sidebar search box (same accessible name,
different DOM location) — scope locators to the header or the sidebar depending on which one a test
targets.

## Failure modes observed

None — empty query, no-results, and result-page layout are all unverified.
