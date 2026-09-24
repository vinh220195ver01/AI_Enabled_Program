# Page: Product detail

- **URL:** e.g. <https://actp1.csc.edu.vn/shop/bold-statement-graphic-tee/> (pattern: `/shop/<product-slug>/`)
- **Purpose:** Single product page — gallery, price, add-to-cart form, description tabs, related
  products. Structure verified on "Bold Statement Graphic Tee"; other products follow the same
  WooCommerce single-product layout.
- **Last verified:** 2026-09-24
- **WebMCP tools:** none observed

## Key elements

| Element | Locator | Notes |
|---|---|---|
| Quantity input | `getByRole('spinbutton', { name: 'Product quantity' })` | Defaults to `1` |
| Add to cart button | `getByRole('button', { name: 'Add to cart' })` | Redirects to same page; cart badge count updates, no navigation |
| Description tab | `getByRole('tab', { name: 'Description' })` (via link) | Selected by default |
| Reviews tab | `getByRole('tab', { name: /Reviews/ })` | Shows review count, e.g. "Reviews (0)" — not explored |
| Breadcrumb | e.g. `Home \ Shop \ Clothing \ Tshirt \ <Product name>` | Reflects the product's category path |
| Related products links | product name links in "Related products" section | Same card pattern as shop listing |

## Forms

### Add to cart

| Field | Type | Required | Validation |
|---|---|---|---|
| Quantity | spinbutton (number) | yes (defaults to 1) | Not tested for min/max/invalid input this pass |

## Notable states

- After clicking "Add to cart", no visible on-page confirmation banner was observed in the
  snapshot — the header cart count (`Cart <n>`) is the reliable signal that the action succeeded.

## Stale / unverified

- Only one product page was explored. Products with variations (size/color) were not found on this
  one — if a variable product exists elsewhere in the catalog, its add-to-cart form (variation
  dropdowns) is undocumented.
