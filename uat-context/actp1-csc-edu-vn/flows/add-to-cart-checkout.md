# Flow: Add to cart & checkout

- **Goal:** Add a product to the cart as a guest and reach the checkout review step.
- **Starting page:** [pages/shop.md](../pages/shop.md) (or any product link on [Home](../pages/home.md))
- **Last verified:** 2026-09-24

## Steps

1. On [Shop](../pages/shop.md), click a product card link (e.g. "Bold Statement Graphic Tee").
2. On [Product detail](../pages/product-detail.md), optionally adjust the quantity spinbutton, then
   click "Add to cart". Page stays on the product detail URL; the header "Cart" badge count
   increments — this is the only confirmation signal observed.
3. Click the "Cart" link in the header to go to [Cart](../pages/cart.md).
4. On Cart, verify the line item, then click "Proceed to checkout".
5. On [Checkout](../pages/checkout.md), the order review table shows the item and total. Billing
   form must be filled to place an order — form submission was not exercised in this pass.

## Failure modes observed

None observed yet — invalid quantity, out-of-stock, and checkout validation errors are all
unverified. The "Sunset Glow Utility Dress" and "Sophisticated Striped Midi Dress" product links are
dead (`#dead-link`) and cannot be used as the flow's starting product.
