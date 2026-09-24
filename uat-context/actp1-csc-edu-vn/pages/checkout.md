# Page: Checkout

- **URL:** <https://actp1.csc.edu.vn/checkout/>
- **Purpose:** Guest (or logged-in) checkout — billing details form, order review table, payment
  method, and order placement.
- **Last verified:** 2026-09-24
- **WebMCP tools:** none observed

## Key elements

| Element | Locator | Notes |
|---|---|---|
| "Click here to login" | `getByRole('link', { name: 'Click here to login' })` | Toggles a login form inline for returning customers; not exercised |
| "Click here to enter your code" | `getByRole('link', { name: 'Click here to enter your code' })` | Toggles coupon field inline; not exercised |
| Create an account checkbox | `getByRole('checkbox', { name: 'Create an account?' })` | Unchecked by default |
| Place order button | `getByRole('button', { name: 'Place order' })` | Not clicked this pass — site banner states no orders are fulfilled, but this was not verified end-to-end |

## Forms

### Billing details

| Field | Type | Required | Validation |
|---|---|---|---|
| First name | text | yes | not tested |
| Last name | text | yes | not tested |
| Company name | text | no | — |
| Country / Region | combobox (searchable) | yes | defaults to "United States (US)" |
| Street address | text | yes | placeholder "House number and street name" |
| Apartment/suite (optional) | text | no | — |
| Town / City | text | yes | not tested |
| State | combobox (searchable) | yes | defaults to "California" |
| ZIP Code | text | yes | not tested |
| Phone | text | yes | not tested |
| Email address | text | yes | not tested |

### Additional information

| Field | Type | Required | Validation |
|---|---|---|---|
| Order notes | textarea | no | placeholder "Notes about your order, e.g. special notes for delivery." |

## Notable states

- Only one payment method is offered: **Cash on Delivery (COD)** — no card/gateway fields to test.
- Order review table lists product name, quantity (`× 1`), and subtotal; Cart totals repeat
  Subtotal/Total.
- Country and State fields render as a visually-hidden native `<select>` plus an enhanced
  `combobox`/`textbox` pair (WooCommerce's select2-style widget) — interacting via
  `fill`/`type` may not work the same as a plain select; verify with `select` or by choosing from
  the dropdown list when writing tests.

## Stale / unverified

- Form submission (valid and invalid) was not exercised — no success/error states documented.
- "Click here to login" and "Click here to enter your code" inline toggles were not opened.
