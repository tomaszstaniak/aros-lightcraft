#!/usr/bin/env python3
"""Prepare or verify the pinned source without resetting existing checkouts."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile
ROOT = Path(__file__).resolve().parents[1]
def git(path, *args):
    return subprocess.check_output(["git", "-c", "gc.auto=0", "-c", "maintenance.auto=false", "-C", str(path), *args], text=True).strip()
def clean(path):
    if git(path, "status", "--porcelain", "--untracked-files=all"):
        raise SystemExit(f"Refusing dirty checkout: {path}")
def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["prepare", "verify"])
    args = parser.parse_args()
    spec = json.loads((ROOT / "upstreams.json").read_text())["repositories"]["lightcraft"]
    upstream, work = ROOT / "upstream/lightcraft", ROOT / "work/lightcraft"
    series = [s.strip() for s in (ROOT / "patches/lightcraft/series").read_text().splitlines() if s.strip() and not s.lstrip().startswith("#")]
    if args.command == "prepare":
        if not upstream.exists():
            upstream.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(["git", "clone", "--no-checkout", spec["url"], str(upstream)], check=True)
            git(upstream, "checkout", "--detach", spec["commit"])
        clean(upstream)
        if git(upstream, "rev-parse", "HEAD") != spec["commit"]:
            raise SystemExit("Upstream does not match pin; no reset performed")
        if work.exists():
            raise SystemExit("Work copy exists; no reset performed. Use verify.")
        work.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", "--no-hardlinks", str(upstream), str(work)], check=True)
        git(work, "switch", "-c", "port/v11-x86_64", spec["commit"])
        for name in series:
            git(work, "am", str(ROOT / "patches/lightcraft" / name))
    clean(upstream)
    clean(work)
    if git(upstream, "rev-parse", "HEAD") != spec["commit"]:
        raise SystemExit("Upstream pin mismatch")
    with tempfile.TemporaryDirectory(prefix="lightcraft-verify-") as tmp:
        git(ROOT, "clone", "--quiet", "--no-hardlinks", "--no-checkout", str(upstream), tmp)
        git(tmp, "checkout", "--quiet", "--detach", spec["commit"])
        for name in series:
            patch = ROOT / "patches/lightcraft" / name
            git(tmp, "apply", "--index", str(patch))
        expected = git(tmp, "write-tree")
        actual = git(work, "rev-parse", "HEAD^{tree}")
        if expected != actual:
            raise SystemExit(f"Tree mismatch: series {expected}, work {actual}")
        print(f"Verified source tree {actual}; {len(series)} patches. No build/runtime claim.")
if __name__ == "__main__":
    main()
