# coverage-diff-hooks

[pre-commit](https://pre-commit.com) hooks that block a commit when the **new or
modified lines** it contains are not covered by tests. Legacy code you did not
touch is exempt.

Currently available: `coverage-diff-python` (pytest + coverage.py + diff-cover).

## How it works

1. Runs your project's `pytest` with coverage and writes `coverage.xml` (Cobertura).
2. Runs [diff-cover](https://github.com/Bachmann1234/diff_cover) to compare that
   report against your staged changes.
3. If any new/modified line is uncovered, the commit is blocked.

## Quick start (5 minutes)

### 1. Install, once per machine

```bash
pip install pre-commit
```

### 2. Install in your project's virtualenv

```bash
pip install pytest pytest-cov
```

The hook runs the `pytest` found on your `PATH`, so **activate your project's
virtualenv before committing**. `diff-cover` does not need to be installed: pre-commit
installs it automatically in an isolated environment.

### 3. Add the hook to `.pre-commit-config.yaml`

```yaml
repos:
  - repo: https://github.com/lujantissera/coverage-diff-hooks.git
    rev: v0.1.0
    hooks:
      - id: coverage-diff-python
```

Always pin `rev` to a tag (never a branch), so upgrades are explicit.

### 4. Enable it in your repo

```bash
pre-commit install
```

From now on, every `git commit` that touches `.py` files runs the check.

## Behavior

| Situation | Result |
|---|---|
| Commit touches no `.py` files | Passes, nothing runs |
| Repo has no commits yet | Passes, check skipped |
| Your tests fail | Blocked |
| New/modified lines uncovered | Blocked, with a table of missing lines |
| `diff-cover` finds no coverage info (false green) | Blocked |
| `diff-cover` crashes | Blocked, with a message saying it is not a coverage problem |

Required coverage on the diff is **100%**. Do not lower it without asking the team.

## Emergency escape hatch

```bash
SKIP=coverage-diff-python git commit -m "..."
```

Use it only when you genuinely cannot test those lines, and tell your team.

## Limitations (v0.1.0)

- Threshold (100%), compare ref (`HEAD`) and excluded folders are fixed in the code.
  Configuration through `.coverage-diff.yml` / environment variables is planned.
- Only staged changes are measured (`--ignore-unstaged`).
- No PHP hook yet.
- Windows path normalization is not implemented; it has not been needed so far.

## Troubleshooting

- **`pytest: command not found` / tests not found:** activate your virtualenv first.
- **Hook does not update after a new release:** change `rev`, or run `pre-commit clean`.
- **Weird characters instead of colors:** use Git Bash, Windows Terminal or VS Code.
