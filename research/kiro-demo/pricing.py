"""Tính giá đơn hàng: giảm giá theo số lượng, mã coupon và phí ship."""

COUPONS = {
    "SAVE10": 0.10,   # giảm 10%
    "VIP20": 0.20,    # giảm 20%
}


def quantity_discount_rate(quantity: int) -> float:
    """Giảm theo số lượng: >=10 giảm 5%, >=50 giảm 10%, >=100 giảm 15%."""
    if quantity < 0:
        raise ValueError("quantity must be >= 0")
    if quantity >= 100:
        return 0.15
    if quantity >= 50:
        return 0.10
    if quantity >= 10:
        return 0.05
    return 0.0


def shipping_fee(subtotal: float) -> float:
    """Miễn phí ship cho đơn từ 500.000; ngược lại 30.000."""
    if subtotal < 0:
        raise ValueError("subtotal must be >= 0")
    return 0.0 if subtotal >= 500_000 else 30_000.0


def calculate_total(unit_price: float, quantity: int, coupon: str | None = None) -> dict:
    """Trả về chi tiết đơn hàng.

    Quy tắc: giảm theo số lượng trước, sau đó áp coupon (nếu hợp lệ),
    cuối cùng cộng phí ship tính trên giá sau giảm.
    """
    if unit_price <= 0:
        raise ValueError("unit_price must be > 0")

    subtotal = unit_price * quantity
    after_qty = subtotal * (1 - quantity_discount_rate(quantity))

    coupon_rate = 0.0
    if coupon is not None:
        coupon_rate = COUPONS.get(coupon.upper())
        if coupon_rate is None:
            raise ValueError(f"invalid coupon: {coupon}")
    after_coupon = after_qty * (1 - coupon_rate)

    ship = shipping_fee(after_coupon)
    return {
        "subtotal": round(subtotal, 2),
        "after_discount": round(after_coupon, 2),
        "shipping": ship,
        "total": round(after_coupon + ship, 2),
    }
