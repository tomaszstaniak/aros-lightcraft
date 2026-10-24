---
type: guide
updated: 2026-10-24
---

# Patch workflow

`upstream/lightcraft/` is the clean pinned external source. Edit only `work/lightcraft/`. Commit source changes there, export each delta into `patches/lightcraft/`, list it in `series`, and commit the patch and metadata in this repository. Record rationale, ABI, verification and upstream status in every patch.

Do not edit Cargo registry sources. If a dependency requires a patch, record its origin and exact revision with a separate series. Preserve local commits, stashes and untracked files before reconstructing or deleting a work copy. The source verifier compares committed trees; it is not a backup.
