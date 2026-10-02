import fnmatch
import os
import shlex
import subprocess
import sys

from coverage_diff_hooks.common import (
    changed_files, has_commits, parse_args, report_result, run_diff_cover,
)

HOOK_ID = "coverage-diff-python"
DEFAULT_REPORT = "coverage.xml"
DEFAULT_RUN = f"pytest --cov --cov-report=xml:{DEFAULT_REPORT} -q"


def add_python_args(parser):
    parser.add_argument(
        "--run", action="append", default=[],
        help="test command that always runs, can be repeated (default: pytest with coverage)",
    )
    parser.add_argument(
        "--report", action="append", default=[],
        help="Cobertura XML report for diff-cover, can be repeated (default: coverage.xml)",
    )
    parser.add_argument(
        "--suite", action="append", default=[],
        help='"<globs>::<command>::<report>": runs only when a changed file matches one of '
             "the comma-separated globs. Can be repeated.",
    )


def parse_suite(spec):
    """Split '<globs>::<command>::<report>' into (patterns, command, report)."""
    parts = [p.strip() for p in spec.split("::")]
    if len(parts) != 3 or not all(parts):
        raise ValueError(f"invalid --suite {spec!r}, expected '<globs>::<command>::<report>'")
    patterns = [g.strip() for g in parts[0].split(",") if g.strip()]
    return patterns, parts[1], parts[2]


def select_suites(specs, files):
    """Return (commands, reports, unmatched_files) for the suites touched by `files`."""
    commands, reports, matched = [], [], set()
    for spec in specs:
        patterns, command, report = parse_suite(spec)
        hits = {f for f in files for g in patterns if fnmatch.fnmatch(f, g)}
        if hits:
            commands.append(command)
            reports.append(report)
            matched |= hits
    return commands, reports, [f for f in files if f not in matched]


def run_tests_with_coverage(commands, reports):
    """Run each test command. Return an error message, or None if all passed."""
    for report in reports:
        os.makedirs(os.path.dirname(report) or ".", exist_ok=True)
    for command in commands:
        argv = shlex.split(command)
        try:
            result = subprocess.run(argv)
        except FileNotFoundError:
            return (
                f"ERROR: command '{argv[0]}' was not found on PATH.\n"
                "Activate your virtualenv and install your test dependencies "
                "(for example: pip install pytest pytest-cov)."
            )
        if result.returncode != 0:
            return f"ERROR: tests failed. Command: {command}"
    return None


def main(argv=None):
    args = parse_args(argv, configure=add_python_args)

    files = changed_files(".py", args.exclude)
    if not files:
        print(f"{HOOK_ID}: no Python files changed, skipping.")
        return 0
    if not has_commits():
        print(f"{HOOK_ID}: repo has no commits yet, skipping.")
        return 0

    commands, reports = list(args.run), list(args.report)
    if args.suite:
        try:
            suite_commands, suite_reports, unmatched = select_suites(args.suite, files)
        except ValueError as error:
            print(f"{HOOK_ID}: ERROR: {error}")
            return 1
        commands += suite_commands
        reports += suite_reports
        if unmatched:
            print(f"{HOOK_ID}: note: no suite covers these files: {', '.join(unmatched)}")
        if not commands:
            print(f"{HOOK_ID}: no test suite is affected by these changes, skipping.")
            return 0
    elif not commands:
        commands, reports = [DEFAULT_RUN], [DEFAULT_REPORT]
    reports = list(dict.fromkeys(reports))

    error = run_tests_with_coverage(commands, reports)
    if error:
        print(f"{HOOK_ID}: {error}")
        return 1
    missing = [r for r in reports if not os.path.exists(r)]
    if missing:
        print(f"{HOOK_ID}: ERROR: coverage report(s) not found: {', '.join(missing)}")
        print("Check that your commands write them (--cov-report=xml:<path>).")
        return 1

    code, output = run_diff_cover(reports, args.fail_under, args.compare_branch, args.exclude)
    return report_result(HOOK_ID, code, output, args.fail_under)


if __name__ == "__main__":
    sys.exit(main())
