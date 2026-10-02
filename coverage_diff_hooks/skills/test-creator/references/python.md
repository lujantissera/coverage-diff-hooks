# Python rules (pytest)

Applies when the blocking hook is `coverage-diff-python`.

## Where tests go

Follow the project settings. Without them, mirror the existing layout: a `tests/`
folder, or `test_*.py` files next to the code, whichever the project already uses.
Test files are named `test_<module>.py`; test functions are named `test_<behavior>`.

## Style

- Plain `pytest` functions with plain `assert`. Use classes only if the project does.
- Use `@pytest.mark.parametrize` for several inputs of the same behavior.
- Share setup through fixtures (`@pytest.fixture`), not copy-paste. Use `tmp_path`
  for files and `monkeypatch` to set environment variables or attributes.
- Check errors with `pytest.raises(SomeError)` and assert on the message when it matters.

## External dependencies

- Replace network, database, clock and file system access with `unittest.mock`
  (`patch`, `MagicMock`) or `monkeypatch`. Patch the name **where it is used**,
  not where it is defined.
- Never mock the function under test.

## Running

The hook runs `pytest --cov`. To check one file quickly:

```bash
pytest tests/test_<module>.py -q
```

Activate the project's virtualenv first.
