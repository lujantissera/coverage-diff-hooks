# Project status

Last updated: 2026-10-02.

## Goal

Reusable pre-commit hooks that block a commit when new/modified lines lack tests,
so any project consumes them with one entry in its `.pre-commit-config.yaml`
instead of copying scripts. Generalizes a pilot built in SuiteCRM
(`bin/check-diff-coverage.sh`, hook id `php-diff-coverage`, `repo: local`).

## Layout

```
.pre-commit-hooks.yaml        declares the hooks (must stay in the repo root)
pyproject.toml                installable package + console scripts (must stay in the root)
coverage_diff_hooks/
  common.py                   shared: args, staged files, diff-cover call, messages, guards
  python_hook.py              pytest + pytest-cov
  php_hook.py                 PHPUnit + PCOV/Xdebug
```

## Done and validated

- `coverage-diff-python`, installed from GitHub at tag `v0.1.0` into a throwaway demo
  project: a commit with tested code passes; a commit with an untested function is
  blocked with `calc.py (50.0%): Missing lines N`.
- Refactor to `common.py` and `args` (`--fail-under`, `--compare-branch`, `--exclude`),
  validated locally with the Python hook (commit `85ea4a1`): default 100% blocks,
  `--fail-under 40` passes.
- Ported from the SuiteCRM pilot: skip when no files of the language are staged, skip
  when the repo has no commits, false-green guard ("No lines with coverage
  information"), English colored block message with `/TestCreator` and `SKIP=<id>`,
  default threshold 100, `--ignore-unstaged`, never commits or pushes.

## PHP hook: validated

- `coverage-diff-php` (`php_hook.py`) was tested in SuiteCRM using commit `45cc409`
  as `rev`, and the checks passed. Released as tag `v0.2.0`.
- SuiteCRM should now pin `rev: v0.2.0` instead of the commit hash.

## Next steps

1. In SuiteCRM: change `rev` from the hash to `v0.2.0`, then (once verified) delete
   `bin/check-diff-coverage.sh` and update docs/CI that mention `php-diff-coverage`
   or `SKIP=php-diff-coverage` (the hook id is now `coverage-diff-php`).
2. Add `tests/` to this repo (e.g. `normalize_path`, `staged_files`, `parse_args`).
3. Create the `/TestCreator` skill in each consuming repo (not in this repo).
4. Migrate the Python project(s) (QEngine) to `coverage-diff-python` at `v0.2.0`.
5. Later: hooks for other languages (Java, Node). When more than ~3 languages exist,
   consider moving language hooks into `coverage_diff_hooks/languages/`.

## Known caveats

- `--exclude` globs are matched with `fnmatch` on the staged path; `diff-cover` also
  receives them for its own filtering. Behavior of both should be confirmed in PHP.
- The hooks call `pytest`/`php` from the `PATH`, so the consumer's environment must
  be active when committing.
- Local PHP environment used for the attempt: PHP 8.2.12 (XAMPP) with PCOV loaded, but
  the `zip` extension is disabled, so `composer require` needs `--prefer-source`
  or enabling `extension=zip` in `php.ini`.

## Throwaway demo projects (outside this repo, safe to delete)

- `C:\Users\LujánTissera\hooks-demo` (Python, complete).
- `C:\Users\LujánTissera\hooks-demo-php` (PHP, abandoned: PHPUnit not installed).
