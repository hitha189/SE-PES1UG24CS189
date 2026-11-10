# Reflection

## 1. Which issues were the easiest and hardest to fix?

The easiest issues were the style and cleanup warnings: unused imports, missing docstrings, the snake_case function name, and the blank lines between functions. The tools told me exactly what to change, and each fix took seconds. The hardest was replacing eval() in apply_promo_code. I could not just delete it, because the program needs promo codes like "total * 0.9". I had to work out what the codes needed to look like, then write a regex and use the operator module to do the math safely. The other harder part was the bare except blocks. Fixing them meant deciding which errors were actually expected (KeyError, TypeError) and what the program should do when they happen.

## 2. Did the tools report any false positives?

Yes, one warning was misleading. Pylint and Flake8 said the local variable "total" in apply_promo_code was assigned but never used. In fact eval() was using it, because the promo string "total * 0.9" refers to that variable by name. The tools could not see this, since the variable was only used inside a string. Deleting it would have broken the promo feature, so I had to understand the code before acting on the warning. This was a good reminder that tool output is a starting point for judgment, not an order to follow blindly. Bandit's B311 warning about the random module was also low severity, since receipt numbers are not very sensitive, but switching to secrets cost nothing, so I fixed it.

## 3. How could static analysis fit into a real development workflow?

I would run all three tools automatically so that problems are caught before they reach the main branch. Pre-commit hooks can run Flake8 and Bandit on every commit. A CI pipeline (for example GitHub Actions) can run Pylint, Bandit and Flake8 on every pull request and fail the build if the Pylint score drops below a set threshold or Bandit finds a Medium or High issue. This makes code quality a shared team standard instead of something one reviewer has to remember to check, and it keeps human code reviews focused on design and logic.

## 4. What improvements did I see after the fixes?

The measurable results were clear. The Pylint score went from 5.65/10 to 10.00/10, Bandit went from 3 issues (1 Medium, 2 Low) to 0, and Flake8 went from 12 warnings to 0. Beyond the numbers, the code is safer, because user input is no longer executed as code. It is also more robust, because errors are now logged instead of silently swallowed, the shared mutable default list is gone, and the log file is properly closed. It is easier to read thanks to docstrings and consistent naming.

However, the tools did not find everything. Running the program showed bugs that none of them flagged: a negative quantity produces a negative bill, totals are not rounded to 2 decimal places, a negative tax rate is accepted, and promo codes apply to the running sales total instead of a single bill. Static analysis improves code quality and security, but it cannot check business logic, so it needs to be combined with testing and input validation.