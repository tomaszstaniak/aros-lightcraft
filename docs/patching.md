---
type: guide
updated: 2026-11-23
---

# Source and patch workflow

## Registered source

`upstreams.json` maps `lightcraft` (the build source) to its URL and full commit. `patches/lightcraft/series`
lists the patches in order (on the 0.21.1 base). The example manifest is illustrative only.

`scripts/craft.py` implements the procedure below: `fetch` (clone, or verify origin,
pin and clean state), `materialize` (new work copy only), `export` (work-copy
commits since the pin to numbered patches and `series`; refuses uncommitted
changes) and `verify` (rebuild the series in a new temporary directory whose path
contains spaces and compare its Git tree, contents and modes, with the work
copy's committed tree).

## Materialization procedure

1. Read and validate the active manifest and explicit series. Fetch the registered
   URL into a new `upstream/lightcraft` checkout, detach at the exact full commit,
   verify its identity and clean state. Never edit that clean source.
2. Create a separate new `work/lightcraft` from the pin and apply the ordered series.
   Stop on conflicts; record the pin, series order and patch content digests.
3. Before reusing work, check its expected inputs against the current manifest and
   patches. Reconstruct independently in a temporary directory and compare actual
   saved source contents and modes before claiming synchronization.
4. Never overwrite or reset an existing work copy as bootstrap behavior. Preserve
   staged, unstaged, untracked and valuable ignored files, branches, commits,
   stashes and reflogs. A clean status or stored digest does not preserve history
   or establish source equivalence. Refuse destructive recreation unless both are
   verified independently and recovery is retained outside the replaced copy.

## Saving changes

Save every external-source modification in `patches/lightcraft/` as a numbered,
coherent patch. Use the full Git binary patch format for binary changes; a text-only
`Binary files differ` notice is insufficient. Save only the delta following earlier
patches and append its exact filename to `series`. Never overwrite existing patches
by calculating a number from file count.

Work-copy commits are the patches: write the metadata into the commit message, then
`export`. Each patch records title, repository, author, date, base commit, prerequisites,
problem, rationale, platform scope, upstream status (`candidate`, `local-only`,
`submitted`, or `accepted`), actual verification and a removal condition if temporary.
Submitted/accepted changes require the upstream link. Explicitly mark unrun tests.
Save patch, metadata and series atomically enough to retain recoverable edits if
interrupted; do not advance a claimed baseline after failure. Commit the preserved
patch before any separately authorized upstream submission. Work-copy commits or a
remote fork do not replace this repository's patch record.

## Reproduction and pin changes

Validate the complete series in a separate temporary reconstruction without changing
active copies. Compare contents, binary bytes and executable modes with the expected
saved tree. Test stale inputs, unsaved changes, stashes/branches/reflogs, amended
commits, successive patches and binary changes before relying on new tooling.
Preserve the previous series before updating the base: the 0.13.0 series is in this repository's git history. Retire accepted
patches only when the new pinned source contains them; retain their provenance in
history. `python3 scripts/craft.py update-check --upstream-commit <full commit> --output report.json` tries the series on a newer upstream commit without changing this repository. A source reconstruction check proves neither a build nor runtime behavior.
