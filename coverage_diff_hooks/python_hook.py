import subprocess
import sys


RED, YELLOW, CYAN, BOLD, RESET = "\033[0;31m", "\033[1;33m", "\033[1;36m", "\033[1m", "\033[0m"


def block_message():
    return f"""
{RED}================================================================{RESET}
{RED}{BOLD}  COMMIT BLOCKED: new lines without tests{RESET}
{RED}================================================================{RESET}
Look at the table above: file + "Missing lines".

{CYAN}{BOLD}>> Want it done for you? Ask the agent /TestCreator to write the test for your new function. <<{RESET}

How to get out of this manually instead:
  1. Open the file at those lines.
  2. Write a test that exercises them.
  3. Commit again.
  4. If those lines genuinely can't be tested, discuss it with the
     team before touching the threshold (fail-under is not lowered
     without asking).

  {YELLOW}Emergency escape hatch: SKIP=coverage-diff-python git commit -m "..."{RESET}
{RED}================================================================{RESET}
"""


def staged_python_files():
    """Return the staged .py files (added, copied, modified, renamed)."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
        capture_output=True, text=True, check=True,
    )
    files = result.stdout.splitlines()
    return [f for f in files if f.endswith(".py")]


def run_tests_with_coverage():
    """Run the project's pytest and write coverage.xml (Cobertura format)."""
    result = subprocess.run(
        ["pytest", "--cov", "--cov-report=xml:coverage.xml", "-q"],
    )
    return result.returncode


def run_diff_cover(fail_under=100):
    """Run diff-cover on the staged changes. Return (exit_code, output)."""
    result = subprocess.run(
        [
            "diff-cover", "coverage.xml",
            f"--fail-under={fail_under}",
            "--compare-branch=HEAD",
            "--ignore-unstaged",
        ],
        capture_output=True, text=True,
    )
    output = result.stdout + result.stderr
    if result.returncode == 0 and "No lines with coverage information" in output:
        return 1, output  # false green: treat as error
    return result.returncode, output


def main():
    if not staged_python_files():
        print("coverage-diff-python: no Python files staged, skipping.")
        return 0
    if run_tests_with_coverage() != 0:
        print("coverage-diff-python: tests failed.")
        return 1
    code, output = run_diff_cover()
    print(output)
    if code != 0:
        print(block_message())
        return 1
    print("coverage-diff-python: OK, diff coverage meets the threshold.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
