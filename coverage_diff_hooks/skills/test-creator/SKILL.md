---
name: test-creator
description: >-
  Writes the missing unit test(s) for lines that the coverage-diff pre-commit
  gate (hooks coverage-diff-php or coverage-diff-python) flagged as uncovered.
  Use when the user invokes /test-creator, or after a commit was blocked with
  "COMMIT BLOCKED: new lines without tests" and the user asks to generate the test.
disable-model-invocation: true
---

# test-creator

Invoke as **/test-creator** right after a commit is blocked by a `coverage-diff-*`
pre-commit hook. It writes the missing test(s) so the next run of the gate passes.
It does not touch production code, and it never commits.

## Scope and safety

- Only add or edit test files (and test support files such as stubs or fixtures
  that the project settings allow). Never modify the production file(s) that
  triggered the gate: no refactors, no "making it more testable".
- Never run `git add` or `git commit`. Leave the changes for the user to review.
- If a line genuinely cannot be tested without real infrastructure (database, file
  I/O, external HTTP call), say so explicitly instead of writing a test that does
  not really exercise the logic.
- Never lower the gate's `--fail-under` threshold.

## Step 0: load settings and language rules

1. Read `.claude/test-creator.md` in the project, if it exists. It defines where
   tests live, which support files may be edited, a reference test to imitate, and
   project-specific rules. If it does not exist, infer the tests folder and style
   from the existing tests, and tell the user you did.
2. Identify which hook blocked the commit and read the matching rules:
   - `coverage-diff-php` -> [references/php.md](references/php.md)
   - `coverage-diff-python` -> [references/python.md](references/python.md)

## Workflow

1. **Find what is missing.** The gate only measures **staged** changes. Make sure the
   flagged production file is staged (ask the user if unsure), then run:

   ```bash
   pre-commit run <hook-id> --files <flagged-file>
   ```

   Read the "Missing lines" table: `<file> (<pct>): Missing lines <ranges>`. If the
   user already pasted that output, use it instead of re-running.

2. **Understand each flagged line.** Read the whole function or method that contains
   the missing ranges, not just those lines: its parameters, what it reads and
   writes, and which external things it touches.

3. **Find or create the test file** following the project settings and the language
   rules. Add to an existing test file when there is one for that unit.

4. **Write the tests** following the quality rules below.

5. **Verify.** Run the same `pre-commit run` command again. If it still blocks:
   - The same "Missing lines" remain: your test does not reach them. Check the
     branches and conditions you skipped and add cases. Do not weaken existing tests.
   - A new error or warning: usually missing test setup. Fix the test, not the code.

6. **Report back** in a few lines: which test files were created or changed, any
   support files added and why, and whether the gate now passes. Tell the user to
   review the diff before committing.

## Quality rules (a green gate is not enough)

The gate measures that a line ran, not that it works. A test that executes a line
without checking anything gives 100% and proves nothing.

- Every test must have meaningful assertions on the result or on the state the code
  changes.
- Every test must be able to fail: if the logic were broken, the test should catch it.
- Cover each branch of the new code (the "yes", the "no", edge values), not only the
  happy path.
- Test the real unit. Replace only its external dependencies, never the code under test.
- One behavior per test, with a name that says what it checks.
- If you cannot assert something useful, say so instead of padding coverage.
