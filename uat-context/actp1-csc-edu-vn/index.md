# ACTP Clothes Shop — UAT Context

- **Base URL:** <https://actp1.csc.edu.vn/>
- **What it is:** A WooCommerce/WordPress (Neve theme) demo clothing store used for QA/automation
  training. Banner states it is reset weekly (Saturday 01:00 AM) and no real orders are fulfilled.
- **Auth required for testing:** No login is required to browse, add to cart, or reach checkout as
  a guest. Login/registration exist for account-specific flows (order history, "Create an account?"
  at checkout). No test credentials are documented yet — none were available during this pass.
- **Last verified:** 2026-09-24

## Pages

| Page | File | Notes |
|---|---|---|
| Home | [pages/home.md](pages/home.md) | Landing page, hero banner, latest products, footer nav |
| Shop | [pages/shop.md](pages/shop.md) | Product listing with categories, sorting, pagination |
| Product detail | [pages/product-detail.md](pages/product-detail.md) | Single product, add-to-cart form |
| Cart | [pages/cart.md](pages/cart.md) | Cart table, coupon field, proceed to checkout |
| Checkout | [pages/checkout.md](pages/checkout.md) | Billing form, order review, Cash on Delivery only |
| My account | [pages/my-account.md](pages/my-account.md) | Login form + Register form on one page |

## Flows

| Flow | File | Notes |
|---|---|---|
| Add to cart & checkout | [flows/add-to-cart-checkout.md](flows/add-to-cart-checkout.md) | Guest checkout, product → cart → checkout |
| Search | [flows/search.md](flows/search.md) | Header search icon toggles an inline search box |

## Known gaps / stale entries

- Login/Register submission was not exercised (no test account credentials available) — forms are
  documented structurally only; success/error states after submit are unverified.
- Payment is Cash on Delivery only in this pass; no other gateways were observed on checkout.
- Blog and category pages (Blouse, Dresses, Tshirt, Uncategorized) were not explored — only linked
  from nav/footer.
- Several product links are intentionally broken (`#dead-link`) — this appears to be a deliberate
  demo-site quirk, not a bug to fix. Flagged per-page below.
