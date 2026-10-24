---
type: guide
updated: 2026-10-24
---

# Build LightCraft for x86_64 AROS ABIv11

To reproduce a published release, check out its release tag before preparing sources. Changed program bytes require a new release identifier.

The source pin is LightCraft v0.13.0, `23e181283cb448205d865e8cd288b56afe987986`.
Keep the upstream Cargo.lock. The build uses a separate source/lock copy under build/v11;
path patches replace exact dependency versions there, never in the registry cache.

1. `python3 scripts/source.py prepare` in a fresh checkout, then `python3 scripts/source.py verify`.
2. Copy local.example.json to ignored local.json and set the compiler, archiver, safe strip,
   ABIv11 SDK, rust-aros checkout, toolchain and egui-aros locations. Environment
   `LIGHTCRAFT_*` settings listed by `python3 scripts/lc.py config` override local values.
3. The source ZIP supplies the exact matched `sources/rust-std.tar.xz`. Recreate it with
   `python3 scripts/install-rust-snapshot.py sources/rust-std.tar.xz /new/private/sysroot aros-lightcraft-local`.
   The destination and alias must be new; install the pinned nightly with rust-src first.
   Alternatively use rust-aros's std-groundwork/std-patch recipe and compare the recorded
   std_source_sha256; compiler version alone does not establish source equivalence.
   The compiler must report `rustc 1.100.0-nightly (0dfb098f3 2026-08-31)` (UI needs >=1.95).
   Use the x86_64/v11 profile, not the newer ARM profile. The recorded target template/libc
   source pin is in scripts/lcconfig.py. The matching std source identity is recorded per build.
4. Check out egui-aros at the pin in upstreams.json. Run its `scripts/ea.py fetch` to prepare
   its pinned upstreams, or configure egui_upstream_root to an existing read-only prepared set.
   The driver invokes the pinned `ea.py vendor` with this project's Cargo.lock.
5. `python3 scripts/lc.py deps` fetches the original, locked upstream dependencies into
   the configured private cargo_home. It does not modify either source checkout. The
   frontend's path-patched dependencies are then prepared by the build driver.
6. `python3 scripts/lc.py build --no-default-features --lto fat --online`.
   For development only, add `--worktree` to include unsaved changes; the manifest records this.
   Offline rebuilds omit --online. Select `-p lightcraft-cli` to build the core/CLI first.

The driver checks compiler identity, crate archive checksums and patched-tree hashes.
It privately rebuilds pthread from the pinned SDK source and first requires its original
objects to reproduce the installed SDK. Only the corrected objects precede the SDK in the
link. It records compiler versions, source/patch hashes, target JSON, command, libraries and
binary hashes in build/v11/out/<id>/manifest.json; build.log is retained even on failure.
No SDK/toolchain/checkouts are changed. A build is not native runtime acceptance.

## Selected profile

Both GUI drawing and image processing are CPU-only. egui-aros supplies the window, input,
clipboard and CPU renderer. The upstream image pipeline, codecs, catalog and sidecars remain.
The independent launch renderer configuration is documented in README.md and --help.
There is no GL context, GPU adapter probe, SAM or automatic model download at startup.

The final link explicitly uses **-nix**. DOS startup/ASL paths are resolved with
Lock/NameFromLock/AddPart, then converted at the boundary to /volume/drawer/file for the CRT
and upstream POSIX lexical path operations. A leading AmigaDOS slash is resolved by DOS as
a parent before conversion. Volume roots and assigns are not combined with PathBuf::join.
At startup, before workers, main preserves its CRT directory using chdir(".") in this exact
-nix mode. Settings and the default catalog live in PROGDIR:LightCraftData.

Give Shell invocations `Stack 16777216`. The icon requests the same **16 MiB**. This is a
selected/tested allocation, not a measured minimum. Timing on QEMU TCG describes emulation.

## Packaging

`python3 scripts/package.py BUILD_OUTPUT` creates the program and source archives with licenses and build metadata. Use AROS-safe stripping (`--strip-unneeded`), preserving relocations. Retain the exact original unstripped binaries for debugging.

The release source archive supplies the pinned source inputs under sources/. Local toolchain locations belong only in ignored local.json. Never change shared toolchains or edit Cargo's registry cache.

## Worker lifetime

Closing cancels procedural generation between rows and waits for outstanding image jobs. The frontend then releases the application, private Rayon pools and global pool before exiting. Native Workbench startup data remains owned by the system; the adapter copies the strings it needs before releasing icon data.
