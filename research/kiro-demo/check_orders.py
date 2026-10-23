"""Kiểm tra chất lượng dữ liệu file data/orders.csv (data quality check)."""
import csv
from datetime import datetime

REQUIRED = ["order_id", "customer_id", "unit_price", "quantity", "order_date", "status"]
VALID_STATUS = {"NEW", "PAID", "SHIPPED", "CANCELLED"}


def load_orders(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def validate_orders(rows: list[dict]) -> list[str]:
    """Trả về danh sách lỗi (rỗng nếu dữ liệu sạch)."""
    errors, seen_ids = [], set()
    for i, r in enumerate(rows, start=2):  # dòng 1 là header
        for col in REQUIRED:
            if not r.get(col):
                errors.append(f"line {i}: missing {col}")
        oid = r.get("order_id")
        if oid in seen_ids:
            errors.append(f"line {i}: duplicate order_id {oid}")
        seen_ids.add(oid)
        try:
            if float(r["unit_price"]) <= 0:
                errors.append(f"line {i}: unit_price must be > 0")
        except (ValueError, TypeError, KeyError):
            errors.append(f"line {i}: unit_price is not a number")
        try:
            if int(r["quantity"]) <= 0:
                errors.append(f"line {i}: quantity must be > 0")
        except (ValueError, TypeError, KeyError):
            errors.append(f"line {i}: quantity is not an integer")
        try:
            datetime.strptime(r["order_date"], "%Y-%m-%d")
        except (ValueError, TypeError, KeyError):
            errors.append(f"line {i}: order_date must be YYYY-MM-DD")
        if r.get("status") not in VALID_STATUS:
            errors.append(f"line {i}: invalid status {r.get('status')}")
    return errors


if __name__ == "__main__":
    problems = validate_orders(load_orders("data/orders.csv"))
    print("OK" if not problems else "\n".join(problems))
