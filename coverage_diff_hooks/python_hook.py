import subprocess
import sys

from coverage_diff_hooks.common import (
    has_commits, parse_args, report_result, run_diff_cover, staged_files,
)

HOOK_ID = "coverage-diff-python"
REPORT = "coverage.xml"


def run_tests_with_coverage():
    """Run the project's pytest and write coverage.xml (Cobertura format)."""
    result = subprocess.run(
        ["pytest", "--cov", f"--cov-report=xml:{REPORT}", "-q"],
    )
    return result.returncode


def main(argv=None):
    args = parse_args(argv)
    if not staged_files(".py", args.exclude):
        print(f"{HOOK_ID}: no Python files staged, skipping.")
        return 0
    if not has_commits():
        print(f"{HOOK_ID}: repo has no commits yet, skipping.")
        return 0
    if run_tests_with_coverage() != 0:
        print(f"{HOOK_ID}: tests failed.")
        return 1
    code, output = run_diff_cover(REPORT, args.fail_under, args.compare_branch, args.exclude)
    return report_result(HOOK_ID, code, output, args.fail_under)


if __name__ == "__main__":
    sys.exit(main())
