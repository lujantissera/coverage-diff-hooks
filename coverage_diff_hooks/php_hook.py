import os
import shlex
import subprocess
import sys

from coverage_diff_hooks.common import (
    has_commits, normalize_path, parse_args, report_result, run_diff_cover, staged_files,
)

HOOK_ID = "coverage-diff-php"


def add_php_args(parser):
    parser.add_argument("--phpunit", default="vendor/bin/phpunit")
    parser.add_argument("--phpunit-config", default="phpunit.xml")
    parser.add_argument("--clover", default="build/logs/clover.xml")


def php_driver_loaded():
    """True if PCOV or Xdebug is loaded in PHP."""
    result = subprocess.run(
        ["php", "-r", 'exit(extension_loaded("pcov") || extension_loaded("xdebug") ? 0 : 1);'],
    )
    return result.returncode == 0


def run_phpunit(phpunit, config, clover):
    """Run PHPUnit and write a Clover report. Return PHPUnit's exit code."""
    os.makedirs(os.path.dirname(clover) or ".", exist_ok=True)
    if os.path.exists(clover):
        os.remove(clover)
    extra_php_args = shlex.split(os.environ.get("PHP_COVERAGE_ARGS", ""))
    env = dict(os.environ, XDEBUG_MODE="coverage")
    result = subprocess.run(
        ["php", *extra_php_args, phpunit, "--configuration", config, "--coverage-clover", clover],
        env=env,
    )
    return result.returncode


def files_missing_from_report(files, clover):
    """Staged files that do not appear in the Clover report."""
    with open(clover, encoding="utf-8") as report:
        content = normalize_path(report.read())
    return [f for f in files if normalize_path(f) not in content]


def main(argv=None):
    args = parse_args(argv, configure=add_php_args)
    files = staged_files(".php", args.exclude)
    if not files:
        print(f"{HOOK_ID}: no PHP files staged, skipping.")
        return 0
    if not has_commits():
        print(f"{HOOK_ID}: repo has no commits yet, skipping.")
        return 0
    if not php_driver_loaded():
        print(f"{HOOK_ID}: ERROR: no coverage driver (PCOV/Xdebug) is loaded in PHP.")
        return 1
    if run_phpunit(args.phpunit, args.phpunit_config, args.clover) != 0:
        print(f"{HOOK_ID}: ERROR: tests are failing. Fix them before continuing.")
        return 1
    missing = files_missing_from_report(files, args.clover)
    if missing:
        for f in missing:
            print(f"{HOOK_ID}: ERROR: '{f}' does not appear in the coverage report.")
        print("Its folder may be missing from <coverage><include> in your phpunit.xml.")
        return 1
    code, output = run_diff_cover(args.clover, args.fail_under, args.compare_branch, args.exclude)
    return report_result(HOOK_ID, code, output, args.fail_under)


if __name__ == "__main__":
    sys.exit(main())
