# Mainline x86_64 ABIv1 build profile

The released program is ABIv11. The separate v1 build uses the qualified official Rust nightly-2026-08-04 profile (compiler504869653f510b279c542e65ccd1ea9710c119ba), precompiled std and matching application libc0.2.190 bindings. CPU rendering and CPU image processing remain the defaults.

The qualified x86_64 SDK used for this build is an integration candidate, not a published toolchain release. This repository does not yet supply an independently installable v1 SDK.

This profile requires the proposed fd.library51/posixc0.41 runtime and its matching headers, socket ownership support and pthread2 source. Those proposals are recorded in upstreams.json. The existing older mainline system is not a matching runtime. Building and linking do not qualify native execution.

Create var/ and copy local.v1.example.json to var/local-v1.json and supply the qualified SDK installation, matching C SDK/tools and original libc archive. Obtain libc0.2.190 from crates.io and check its SHA256 against patches/crates/crates.json. Its AROS bindings are reconstructed from the two versioned patches. Keep the v1 cache and build root separate from v11.

Prepare LightCraft and egui-aros as in development.md. Prepare the pinned aros-v1-pthread source from upstreams.json under upstream/aros-v1-pthread; a filtered sparse checkout of compiler/pthread is sufficient. The driver requires a clean checkout at the exact commit.

```
LIGHTCRAFT_LOCAL=var/local-v1.json python3 scripts/lc.py deps
LIGHTCRAFT_LOCAL=var/local-v1.json python3 scripts/lc.py build -p lightcraft-cli --no-default-features --lto fat --online
LIGHTCRAFT_LOCAL=var/local-v1.json python3 scripts/lc.py build --no-default-features --lto fat --online
```

No SDK or compiler is changed. The driver verifies the installed SDK wrappers and compiler identity using the installation's own qualification code. It rebuilds the entire matching pthread link library privately and checks source headers against the selected SDK. This avoids mixing new pthread layouts with the older static library shipped in the base SDK. Those objects are placed before SDK libraries at link time. The v11 filesystem gate and realtime-clock workaround are not applied to v1.

Build records identify compiler, SDK generation, original and derived locks, dependencies, source pins, pthread objects, command and binary hashes. The upstream lockfile remains unchanged. An accepted native runtime is required before publishing a v1 program archive as a working release.

The current precompiled std input embeds build-directory names in diagnostic strings. A redistributable v1 build needs a std rebuilt with source-path remapping, in addition to native runtime qualification. Application flags cannot rewrite diagnostic strings already stored in a precompiled standard library. No v1 program archive is published yet.
