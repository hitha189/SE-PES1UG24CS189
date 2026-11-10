"""Retail point-of-sale: checkout totals, promo codes and receipt log."""
import logging
import operator
import re
import secrets

# Global state
price_list = {"pen": 10, "notebook": 45, "bag": 799, "bottle": 150}
sales = {"total": 0}
receipt_lines = []

PROMO_PATTERN = re.compile(r"^\s*total\s*([*+\-/])\s*(\d+(?:\.\d+)?)\s*$")
OPERATORS = {
    "*": operator.mul,
    "+": operator.add,
    "-": operator.sub,
    "/": operator.truediv,
}


def process_checkout(cart_items, tax_rate=0.05, receipts=None):
    """Return the total (with tax) for a cart and record the receipt."""
    if receipts is None:
        receipts = []
    subtotal = 0
    for name, qty in cart_items:
        try:
            subtotal += price_list[name] * qty
        except (KeyError, TypeError):
            logging.warning("Skipping invalid cart item: %r", name)
    total = subtotal + subtotal * tax_rate
    receipts.append(total)
    sales["total"] += total
    receipt_lines.append(
        f"Receipt #{secrets.randbelow(9000) + 1000} total={total:.2f}"
    )
    return total


def apply_promo_code(code_str):
    """Apply a promo such as 'total * 0.9' to the running sales total."""
    match = PROMO_PATTERN.match(code_str)
    if match is None:
        raise ValueError(f"Invalid promo code: {code_str!r}")
    symbol, number = match.groups()
    return OPERATORS[symbol](sales["total"], float(number))


def update_stock(item, qty):
    """Report a stock update for an item, warning if it is unknown."""
    try:
        price_list[item] = price_list[item]
        print("Stock updated for", item, "by", qty)
    except KeyError:
        logging.warning("Cannot update stock: unknown item %r", item)


def save_receipt_log(file="pos_log.txt"):
    """Append all receipt lines to the log file."""
    with open(file, "a", encoding="utf-8") as log_file:
        for line in receipt_lines:
            log_file.write(line + "\n")


def print_sales():
    """Print the running sales total."""
    print(f"Sales so far: {sales['total']}")


def main():
    """Run the demo checkout flow."""
    print("Bill 1:", process_checkout([("pen", 3), ("notebook", 2)]))
    print("Bill 2:", process_checkout([("bag", 1), ("laptop", 1)]))
    print("Bill 3:", process_checkout([("bottle", -4)]))
    print("Bill 4:", process_checkout([("pen", "2")], tax_rate=-1))
    update_stock("laptop", 5)
    print("After promo:", apply_promo_code("total * 0.9"))
    code = input("Enter promo code (e.g. total - 50): ") or "total - 50"
    try:
        print("After your promo:", apply_promo_code(code))
    except ValueError as error:
        print(error)
    save_receipt_log()
    print_sales()


if __name__ == "__main__":
    main()
