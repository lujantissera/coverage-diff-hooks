import argparse
import shutil
from pathlib import Path

SKILL_NAME = "test-creator"


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Copy the test-creator skill into .claude/skills/ of the current project.",
    )
    parser.add_argument("--force", action="store_true", help="overwrite an existing copy")
    args = parser.parse_args(argv)

    source = Path(__file__).parent / "skills" / SKILL_NAME
    target = Path.cwd() / ".claude" / "skills" / SKILL_NAME

    if target.exists() and not args.force:
        print(f"{target} already exists. Use --force to overwrite it.")
        return 1
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target)
    print(f"Installed skill to {target}")
    print("Optional: create .claude/test-creator.md with your project-specific rules.")
    return 0
