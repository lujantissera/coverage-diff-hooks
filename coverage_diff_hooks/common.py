import argparse
import fnmatch
import os
import subprocess

RED, YELLOW, CYAN, BOLD, RESET = "\033[0;31m", "\033[1;33m", "\033[1;36m", "\033[1m", "\033[0m"


def parse_args(argv=None, configure=None):
    """Options a consumer project can pass through `args:` in .pre-commit-config.yaml.

    `configure` lets a hook register extra, language-specific options.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--fail-under", type=int,
        default=int(os.environ.get("COVERAGE_DIFF_FAIL_UNDER", 100)),
    )
    parser.add_argument(
        "--compare-branch",
        default=os.environ.get("COVERAGE_DIFF_COMPARE_REF", "HEAD"),
    )
    parser.add_argument(
        "--exclude", action="append", default=[],
        help="glob to ignore, can be repeated",
    )
    if configure:
        configure(parser)
    return parser.parse_args(argv)


def normalize_path(path):
    """Lowercase and use `/`, so report paths and git paths can be compared (Windows)."""
    return path.replace("\\", "/").lower()


def diff_range():
    """(from_ref, to_ref) when pre-commit runs at the pre-push stage, else None.

    pre-commit sets these variables for pre-push (and for `--from-ref/--to-ref`).
    """
    from_ref = os.environ.get("PRE_COMMIT_FROM_REF")
    to_ref = os.environ.get("PRE_COMMIT_TO_REF")
    if from_ref and to_ref:
        return from_ref, to_ref
    return None


def changed_files(extension, exclude):
    """Files in this commit (or in the push, at pre-push) with the given extension,
    minus the excluded globs."""
    ref_range = diff_range()
    scope = [f"{ref_range[0]}...{ref_range[1]}"] if ref_range else ["--cached"]
    result = subprocess.run(
        ["git", "diff", *scope, "--name-only", "--diff-filter=ACMR"],
        capture_output=True, text=True, check=True,
    )
    files = [f for f in result.stdout.splitlines() if f.endswith(extension)]
    return [f for f in files if not any(fnmatch.fnmatch(f, p) for p in exclude)]


def has_commits():
    """Return True if the repo already has at least one commit."""
    result = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", "HEAD"],
        capture_output=True,
    )
    return result.returncode == 0


def run_diff_cover(reports, fail_under, compare_branch, exclude):
    """Run diff-cover on the staged changes. Return (exit_code, output).

    `reports` is a list of coverage report paths; diff-cover merges them.
    """
    ref_range = diff_range()
    if ref_range:
        compare_branch = ref_range[0]  # at pre-push, compare against what the remote has
    command = [
        "diff-cover", *reports,
        f"--fail-under={fail_under}",
        f"--compare-branch={compare_branch}",
        "--ignore-unstaged",
    ]
    if exclude:
        command += ["--exclude", *exclude]
    result = subprocess.run(command, capture_output=True, text=True)
    output = result.stdout + result.stderr
    if result.returncode == 0 and "No lines with coverage information" in output:
        return 1, output  # false green: treat as error
    return result.returncode, output


def block_message(hook_id):
    return f"""
{RED}================================================================{RESET}
{RED}{BOLD}  COMMIT BLOCKED: new lines without tests{RESET}
{RED}================================================================{RESET}
Look at the table above: file + "Missing lines".

{CYAN}{BOLD}>> Want it done for you? Ask the agent /test-creator to write the test for your new function. <<{RESET}

How to get out of this manually instead:
  1. Open the file at those lines.
  2. Write a test that exercises them.
  3. Commit again.
  4. If those lines genuinely can't be tested, discuss it with the
     team before touching the threshold (fail-under is not lowered
     without asking).

  {YELLOW}Emergency escape hatch: SKIP={hook_id} git commit -m "..."{RESET}
{RED}================================================================{RESET}
"""


def report_result(hook_id, code, output, fail_under):
    """Print the outcome of diff-cover and return the hook's exit code."""
    print(output)
    if "Traceback" in output:
        print(f"{hook_id}: diff-cover crashed (not a coverage problem). See output above.")
        return 1
    if code != 0:
        print(block_message(hook_id))
        return 1
    print(f"{hook_id}: OK, diff coverage meets the threshold ({fail_under}%).")
    return 0
