# Page: Cart

- **URL:** <https://actp1.csc.edu.vn/cart/>
- **Purpose:** Review cart contents, adjust quantity, apply coupon, remove items, proceed to
  checkout.
- **Last verified:** 2026-09-24
- **WebMCP tools:** none observed

## Key elements

| Element | Locator | Notes |
|---|---|---|
| Remove item link | `getByRole('link', { name: /Remove .* from cart/ })` | Per-row; URL carries a `remove_item` + `_wpnonce` query param — nonce is session-specific, don't hardcode |
| Line item quantity | `getByRole('spinbutton', { name: 'Product quantity' })` | Same pattern as product detail page; scope to the row if multiple items |
| Coupon code input | `getByRole('textbox', { name: 'Coupon:' })` | Placeholder "Coupon code" |
| Apply coupon button | `getByRole('button', { name: 'Apply coupon' })` | Not exercised this pass |
| Update cart button | `getByRole('button', { name: 'Update cart' })` | Disabled until a quantity is changed |
| Proceed to checkout | `getByRole('link', { name: 'Proceed to checkout' })` | → `/checkout/` |

## Forms

### Coupon

| Field | Type | Required | Validation |
|---|---|---|---|
| Coupon code | text | no | Not exercised — no valid coupon code known |

## Notable states

- Empty cart state was not captured this pass (cart had 1 item throughout exploration).
- Cart totals table shows Subtotal and Total rows; with a single item and no shipping/coupon, both
  equal the item price.

## Stale / unverified

- Empty-cart and multi-item states are undocumented.
