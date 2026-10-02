# coverage-diff-hooks

[pre-commit](https://pre-commit.com) hooks that block a commit (or a push) when the
**new or modified lines** it contains are not covered by tests. Legacy code you did
not touch is exempt.

| Hook | Stack | Status |
|---|---|---|
| `coverage-diff-python` | pytest + pytest-cov + diff-cover | Tested |
| `coverage-diff-php` | PHPUnit + PCOV/Xdebug + diff-cover | Tested in SuiteCRM |

> `--run`, `--report`, `--suite` and `pre-push` support need **`v0.3.0` or later**.

## How it works

1. Runs your project's tests with coverage and writes a report
   (Cobertura XML for Python, Clover for PHP).
2. Runs [diff-cover](https://github.com/Bachmann1234/diff_cover) to compare that
   report against the lines you changed.
3. If any new/modified line is uncovered, the commit is blocked.

The hook does not know where your tests live or how you run them: **you tell it in
your `.pre-commit-config.yaml`** (see "Which case is my project?").

## Getting started

### Once per machine

```bash
pip install pre-commit
```

### Once per project

1. **Install your test tools in the project's virtualenv** and keep it **activated**
   when you commit (the hook uses the `pytest` / `php` it finds on your `PATH`):
   - Python: `pip install pytest pytest-cov` (or `pip install -r requirements-dev.txt`).
   - PHP: PHPUnit (`vendor/bin/phpunit`) and PCOV or Xdebug loaded in PHP.
2. **Add the hook** to the project's `.pre-commit-config.yaml` (next section).
3. **Stage the config**: `git add .pre-commit-config.yaml` (pre-commit refuses to run
   with an unstaged config).
4. **Enable the git hook**: `pre-commit install`
   (add `--hook-type pre-push` as well if you run it at push time).

`diff-cover` does not need to be installed: pre-commit installs it in an isolated
environment.

## Which case is my project?

Always pin `rev` to a tag, never a branch.

### Case 1: Python, standard pytest layout

`pytest` finds your tests by itself (`tests/` folder, `test_*.py` files). Nothing to configure:

```yaml
repos:
  - repo: https://github.com/lujantissera/coverage-diff-hooks.git
    rev: v0.3.0
    hooks:
      - id: coverage-diff-python
```

### Case 2: Python, custom test layout

Your tests are somewhere else or need special arguments (for example `src/tests.py`,
which `pytest` does not discover). Tell the hook the command and where it writes its report:

```yaml
      - id: coverage-diff-python
        args:
          - --run
          - "pytest --cov=mypackage --cov-report=xml:coverage/cov.xml src/tests.py -q"
          - --report
          - coverage/cov.xml
          - --exclude
          - "src/tests.py"        # do not ask for coverage of the test files themselves
```

Use forward slashes in commands and paths. Copy the command from your CI or your
`run_tests.sh`, and add `--cov-report=xml:<path>`.

### Case 3: Python, several suites or a slow test run

Declare each suite with the files that trigger it. Only the suites affected by your
changes run:

```yaml
      - id: coverage-diff-python
        stages: [pre-push]          # optional: run when pushing, keep commits fast
        args:
          - --suite
          - "src/worker.py::pytest --cov=worker --cov-report=xml:coverage/worker.xml src/test_worker.py -q::coverage/worker.xml"
          - --suite
          - "src/app.py::pytest --cov=app --cov-report=xml:coverage/app.xml src/tests.py -q::coverage/app.xml"
          - --exclude
          - "src/test_*.py"
```

Format: `"<globs>::<command>::<report>"`. Several globs are separated by commas. If you
change only `worker.py`, only the worker suite runs. If you use `stages: [pre-push]`,
install it with `pre-commit install --hook-type pre-push`.

### Case 4: PHP

```yaml
      - id: coverage-diff-php
        args: [--exclude, "vendor/*", --exclude, "Test/*"]
```

Defaults: `vendor/bin/phpunit`, `phpunit.xml`, `build/logs/clover.xml`; change them
with `--phpunit`, `--phpunit-config`, `--clover`. The folders you want measured must
be inside `<coverage><include>` of your `phpunit.xml`.

## Everyday workflow

1. Write your code **and its tests**, then `git add` and `git commit`.
2. The hook runs your tests and checks the lines you changed.
3. **Passes:** the commit is saved.
4. **Blocked:** read the table (`file`, `Missing lines`), add tests that exercise those
   lines, stage them and commit again. The message also suggests `/test-creator`
   (see below).
5. Only if those lines genuinely cannot be tested, use the escape hatch and tell your team.

## Options (`args`)

| Option | Default | Hook | Notes |
|---|---|---|---|
| `--fail-under N` | `100` | both | % of the diff that must be covered. Lowering it weakens the gate. |
| `--compare-branch REF` | `HEAD` | both | Ref the diff is computed against. Ignored at pre-push (uses the pushed range). |
| `--exclude GLOB` | none | both | Repeatable. Matching files are ignored. |
| `--run "CMD"` | `pytest --cov --cov-report=xml:coverage.xml -q` | Python | Test command that always runs. Repeatable. |
| `--report PATH` | `coverage.xml` | Python | Cobertura report for diff-cover. Repeatable (reports are merged). |
| `--suite "GLOBS::CMD::REPORT"` | none | Python | Suite that runs only if a changed file matches. Repeatable. |
| `--phpunit PATH` | `vendor/bin/phpunit` | PHP | |
| `--phpunit-config PATH` | `phpunit.xml` | PHP | |
| `--clover PATH` | `build/logs/clover.xml` | PHP | |

Environment variables (lowest priority; `args` override them):
`COVERAGE_DIFF_FAIL_UNDER`, `COVERAGE_DIFF_COMPARE_REF`, `PHP_COVERAGE_ARGS`
(extra flags passed to `php`, PHP hook only).

## Commit time or push time

By default the hook runs at **commit** time and measures the staged changes. For slow
test suites, set `stages: [pre-push]`: it then runs on `git push` and measures all
the commits being pushed. Both modes use the same options.

## Optional: the `/test-creator` skill

When a commit is blocked, the message suggests `/test-creator`: a
[Claude Code](https://claude.com/claude-code) skill that writes the missing test.
It is optional; the hooks work without it. The skill ships inside this repo and is
**not** installed automatically.

Install it once per project, from the project's root, in one of two ways:

```bash
# Option A: with the installer (adds this package to the active environment)
pip install git+https://github.com/lujantissera/coverage-diff-hooks.git@<tag-or-commit>
coverage-diff-install-skill          # add --force to overwrite an existing copy
pip uninstall coverage-diff-hooks    # optional, once installed

# Option B: copy by hand
# copy coverage_diff_hooks/skills/test-creator/ from this repo to <project>/.claude/skills/test-creator/
```

How it works:

- `SKILL.md` holds the generic workflow and quality rules (tests must assert real
  behavior; a green gate is not enough). It never touches production code and never commits.
- `references/php.md` and `references/python.md` hold the language conventions; the
  skill reads the one that matches the hook that blocked the commit.
- A project can add its own rules in `.claude/test-creator.md`: where tests live, which
  support files may be edited, a reference test to imitate, project-specific safety rules.

Review every generated test before committing: the AI writes it, you approve it.

## Behavior

| Situation | Result |
|---|---|
| No changed files of the hook's language | Passes, nothing runs |
| Repo has no commits yet | Passes, check skipped |
| `--suite` used and no suite matches the changed files | Passes, nothing runs |
| A changed file matches no `--suite` | Not checked; a note lists it |
| Test command not found (e.g. `pytest` not installed) | Blocked, with a clear message |
| Your tests fail | Blocked |
| New/modified lines uncovered | Blocked, with a table of missing lines |
| `diff-cover` finds no coverage info (false green) | Blocked |
| `diff-cover` crashes | Blocked, with a message saying it is not a coverage problem |
| PHP: no PCOV/Xdebug loaded | Blocked |
| PHP: changed file missing from the Clover report | Blocked (check `<coverage><include>` in `phpunit.xml`) |

The hooks never run `git commit` or `git push`.

## Emergency escape hatch

```bash
SKIP=coverage-diff-python git commit -m "..."   # or coverage-diff-php
```

Use it only when you genuinely cannot test those lines, and tell your team.

## Limitations

- The hook runs the **whole** test command you configure. For big projects use
  `--suite` and/or `stages: [pre-push]` to keep commits fast.
- Files that no `--suite` covers are not checked (only a note is printed).
- Measured lines come from `git diff`; renamed or moved files may count as new code.
- Windows path normalization (case and `\` vs `/`) is applied only when checking
  that changed files appear in the PHP Clover report.
- Early-stage project (`v0.3.x`): the PHP hook has so far been validated on a single
  real project (SuiteCRM). Feedback and issues are welcome.

## License

[MIT](LICENSE) © 2026 Lujan Tissera

## Troubleshooting

| Symptom | Fix |
|---|---|
| `[ERROR] Your pre-commit configuration is unstaged` | `git add .pre-commit-config.yaml` |
| `command 'pytest' was not found on PATH` | Activate the virtualenv and install your test dependencies. |
| `ERROR: tests failed. Command: ...` | The tests fail on their own, not because of coverage. Fix them first (run the same command by hand to see why). |
| `No lines with coverage information` | The report paths do not match the changed files, or the report does not include them (check `--cov=` / `<include>`). |
| The hook runs no tests, or too few | `pytest` did not discover your tests: use `--run` with the exact command your CI uses. |
| Hook id not found / wrong hook ran | Check the `id`: `coverage-diff-python` or `coverage-diff-php`. |
| A formatter (black, prettier) "modified files" and the commit fails | Re-stage the files (`git add`) and commit again. Avoid files with both staged and unstaged changes. |
| Hook does not update after a new release | Change `rev`, or run `pre-commit clean`. |
| Weird characters instead of colors | Use Git Bash, Windows Terminal or VS Code. |
| Commit is too slow | Use `--suite` to run only the affected suites, or `stages: [pre-push]`. |
