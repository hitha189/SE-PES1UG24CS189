# Issues Found

| Issue | Type | Line(s) | Description | Fix Approach |
| ----- | ---- | ------- | ----------- | ------------ |
| Use of eval() on user input | Security (Bandit B307, Medium; Pylint W0123) | 27 | The promo code typed by the user was executed as Python code, so anyone could run arbitrary commands. | Removed eval. A regex only accepts "total <operator> <number>" and the math is done with the operator module. Invalid codes raise ValueError. |
| try/except/pass | Security/Bug (Bandit B110, Low; Pylint W0718) | 33-34 | update_stock swallowed every error silently, so an unknown item like "laptop" failed with no message. | Catch only KeyError and log a warning with logging.warning. |
| random for receipt numbers | Security (Bandit B311, Low) | 21 | The random module is predictable and not meant for security-related values. | Replaced random.randint with secrets.randbelow(9000) + 1000. |
| Mutable default argument | Bug (Pylint W0102) | 10 | receipts=[] is created once and shared across all calls, so data leaks between checkouts. | Changed the default to None and create a new list inside the function. |
| Bare except | Bug (Pylint W0702, Flake8 E722) | 16 | It hid every error, including invalid items and wrong types, so bad bills looked normal. | Catch (KeyError, TypeError) and log a warning for the skipped item. |
| File opened without with/encoding | Bug (Pylint R1732, W1514) | 37 | The log file was never closed and used a system-dependent encoding. | Used with open(file, "a", encoding="utf-8"). |
| Unused imports and variable | Style (Pylint W0611, W0612; Flake8 F401, F841) | 1, 3, 26 | json, logging and the local variable total were never used. | Removed json and the variable. logging is now used for warnings. |
| Global statement and naming | Style (Pylint W0603, C0103) | 7, 11, 41 | A global variable was modified inside a function, sales_total was not UPPER_CASE, and printSales was not snake_case. | Stored the running total in a dict (sales["total"]) and renamed the function to print_sales. |
| Missing docstrings | Style (Pylint C0114, C0116) | many | The module and all functions had no documentation. | Added one-line docstrings. |
| f-strings | Style (Pylint C0209) | 21 | Old % formatting was used. | Switched to f-strings. |
| PEP 8 spacing and line length | Style (Flake8 E302, E305, E501, W292) | 10, 21, 24, 29, 36, 41, 44, 56 | Missing blank lines between functions, a line over 79 characters, and no final newline. | Added two blank lines, split the long line, and added a final newline. |

## Bugs found by running the program (not flagged by any tool)

These are still in the code, and the tools could not detect them:

- Negative quantity gives a negative bill (Bill 3: -630.0).
- Money is not rounded (e.g. 284.95000000000005).
- Promo codes apply to the running sales total, not to a single bill.
- A negative tax rate is accepted (Bill 4).

Static analysis cannot catch wrong business logic, so these need tests or input validation.