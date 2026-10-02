# coverage-diff-hooks

[pre-commit](https://pre-commit.com) hooks that block a commit when the **new or
modified lines** it contains are not covered by tests. Legacy code you did not
touch is exempt.

| Hook | Stack | Status |
|---|---|---|
| `coverage-diff-python` | pytest + pytest-cov + diff-cover | Tested |
| `coverage-diff-php` | PHPUnit + PCOV/Xdebug + diff-cover | Tested in SuiteCRM (from `v0.2.0`) |

## How it works

1. Runs your project's tests with coverage and writes a report
   (`coverage.xml` for Python, `build/logs/clover.xml` for PHP).
2. Runs [diff-cover](https://github.com/Bachmann1234/diff_cover) to compare that
   report against your staged changes.
3. If any new/modified line is uncovered, the commit is blocked.

## Quick start (5 minutes)

### 1. Install, once per machine

```bash
pip install pre-commit
```

### 2. Make sure your project has its test tooling

- **Python:** `pip install pytest pytest-cov` in your project's virtualenv.
  The hook runs the `pytest` found on your `PATH`, so **activate the virtualenv
  before committing**.
- **PHP:** PHPUnit (`vendor/bin/phpunit`) and a coverage driver (PCOV or Xdebug)
  loaded in PHP.

`diff-cover` does not need to be installed: pre-commit installs it automatically
in an isolated environment.

### 3. Add the hook to `.pre-commit-config.yaml`

```yaml
repos:
  - repo: https://github.com/lujantissera/coverage-diff-hooks.git
    rev: v0.2.0
    hooks:
      - id: coverage-diff-python
```

Always pin `rev` to a tag (never a branch), so upgrades are explicit.

### 4. Enable it in your repo

```bash
pre-commit install
```

From now on, every `git commit` that touches matching files runs the check.

## Configuration (`args`)

Options are passed per project through `args` in `.pre-commit-config.yaml`:

```yaml
    hooks:
      - id: coverage-diff-php
        args: [--exclude, "vendor/*", --exclude, "Test/*", --fail-under, "100"]
```

| Option | Default | Applies to | Notes |
|---|---|---|---|
| `--fail-under N` | `100` | both | % of the diff that must be covered. Do not lower without asking the team. |
| `--compare-branch REF` | `HEAD` | both | Ref the diff is computed against. |
| `--exclude GLOB` | none | both | Repeatable. Files matching it are ignored. |
| `--phpunit PATH` | `vendor/bin/phpunit` | PHP | |
| `--phpunit-config PATH` | `phpunit.xml` | PHP | |
| `--clover PATH` | `build/logs/clover.xml` | PHP | |

Environment variables (override defaults; `args` override them):
`COVERAGE_DIFF_FAIL_UNDER`, `COVERAGE_DIFF_COMPARE_REF`, `PHP_COVERAGE_ARGS`
(extra flags passed to `php`, PHP hook only).

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
| Commit touches no files of the hook's language | Passes, nothing runs |
| Repo has no commits yet | Passes, check skipped |
| Your tests fail | Blocked |
| New/modified lines uncovered | Blocked, with a table of missing lines |
| `diff-cover` finds no coverage info (false green) | Blocked |
| `diff-cover` crashes | Blocked, with a message saying it is not a coverage problem |
| PHP: no PCOV/Xdebug loaded | Blocked |
| PHP: staged file missing from the Clover report | Blocked (check `<coverage><include>` in `phpunit.xml`) |

The hooks never run `git commit` or `git push`.

## Emergency escape hatch

```bash
SKIP=coverage-diff-python git commit -m "..."   # or coverage-diff-php
```

Use it only when you genuinely cannot test those lines, and tell your team.

## Limitations

- Only staged changes are measured (`--ignore-unstaged`).
- Windows path normalization (case and `\` vs `/`) is applied only when checking
  that staged files appear in the PHP Clover report.

## Troubleshooting

- **`pytest: command not found` / tests not found:** activate your virtualenv first.
- **Hook does not update after a new release:** change `rev`, or run `pre-commit clean`.
- **Weird characters instead of colors:** use Git Bash, Windows Terminal or VS Code.
