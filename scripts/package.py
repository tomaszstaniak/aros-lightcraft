#!/usr/bin/env python3
"""Release archives from build outputs: `craft.py package` of the pinned Craft tools.

    package.py binary BUILD_OUTPUT [--dist DIR]
    package.py source BUILD_OUTPUT [BUILD_OUTPUT ...] [--dist DIR]

Same as `python3 scripts/craft.py package ...`; `--help` describes the archives.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import craft  # noqa: E402

if __name__ == "__main__":
    sys.exit(craft.main(["package", *sys.argv[1:]]))
