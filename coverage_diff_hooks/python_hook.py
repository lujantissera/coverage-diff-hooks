import os
import shlex
import subprocess
import sys

from coverage_diff_hooks.common import (
    has_commits, parse_args, report_result, run_diff_cover, staged_files,
)

HOOK_ID = "coverage-diff-python"
DEFAULT_REPORT = "coverage.xml"
DEFAULT_RUN = f"pytest --cov --cov-report=xml:{DEFAULT_REPORT} -q"


def add_python_args(parser):
    parser.add_argument(
        "--run", action="append", default=[],
        help="test command to run, can be repeated (default: pytest with coverage)",
    )
    parser.add_argument(
        "--report", action="append", default=[],
        help="Cobertura XML report for diff-cover, can be repeated (default: coverage.xml)",
    )


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
    commands = args.run or [DEFAULT_RUN]
    reports = args.report or [DEFAULT_REPORT]

    if not staged_files(".py", args.exclude):
        print(f"{HOOK_ID}: no Python files staged, skipping.")
        return 0
    if not has_commits():
        print(f"{HOOK_ID}: repo has no commits yet, skipping.")
        return 0

    error = run_tests_with_coverage(commands, reports)
    if error:
        print(f"{HOOK_ID}: {error}")
        return 1
    missing = [r for r in reports if not os.path.exists(r)]
    if missing:
        print(f"{HOOK_ID}: ERROR: coverage report(s) not found: {', '.join(missing)}")
        print("Check that your --run commands write them (--cov-report=xml:<path>).")
        return 1

    code, output = run_diff_cover(reports, args.fail_under, args.compare_branch, args.exclude)
    return report_result(HOOK_ID, code, output, args.fail_under)


if __name__ == "__main__":
    sys.exit(main())
