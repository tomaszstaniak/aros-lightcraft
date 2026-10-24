# Mainline x86_64 ABIv1 build profile

The ABIv11 release remains separate. The v1 build uses the official Rust nightly-2026-08-04 compiler with an experimental AROS standard-library integration (compiler504869653f510b279c542e65ccd1ea9710c119ba), precompiled std and matching application libc0.2.190 bindings. CPU rendering and CPU image processing remain the defaults.

The qualified x86_64 SDK used for this build is an integration candidate, not a published toolchain release. Build a private SDK and matching runtime using [sdk-v1.md](sdk-v1.md). Shared SDKs are not replaced.

This profile requires the proposed fd.library51/posixc0.41 runtime and its matching headers, socket ownership support and pthread2 source. Those proposals are recorded in upstreams.json. The existing older mainline system is not a matching runtime. Building and linking do not qualify native execution.

Use the v1 recipe at `v0.13.0-aros2`; `v0.13.0-aros1` preserves the v11 release recipe.

Create var/ and copy local.v1.example.json to var/local-v1.json and supply the qualified SDK installation, matching C SDK/tools and original libc archive. Obtain libc0.2.190 from crates.io and check its SHA256 against patches/crates/crates.json. Its AROS bindings are reconstructed from the two versioned patches. Keep the v1 cache and build root separate from v11.

Prepare LightCraft and egui-aros as in development.md. The selected C SDK must contain the complete matching pthread archive, including condition-attribute clock functions.

```
LIGHTCRAFT_LOCAL=var/local-v1.json python3 scripts/lc.py deps
LIGHTCRAFT_LOCAL=var/local-v1.json python3 scripts/lc.py build -p lightcraft-cli --no-default-features --lto fat --online
LIGHTCRAFT_LOCAL=var/local-v1.json python3 scripts/lc.py build --no-default-features --lto fat --online
```

No SDK or compiler is changed. The driver verifies the installed SDK wrappers and compiler identity using the installation's own qualification code. It checks that std and the C startup both select `-nix`, and rejects an old pthread archive lacking the clock functions. The matching SDK archive is linked normally; no private pthread objects are prelinked. The v11 filesystem gate and realtime-clock workaround are not applied to v1.

Build records identify compiler, SDK generation, original and derived locks, dependencies, source pins, pthread archive, command and binary hashes. The upstream lockfile remains unchanged. An accepted native runtime is required before publishing a v1 program archive as a working release.

The SDK recipe maps std source paths while compiling the library. Keep the exact unstripped application binaries for diagnosis and use AROS-safe stripping for the program archive. Native application qualification remains a separate requirement from SDK construction.

The default v1 driver always disables upstream default features. The release packager rejects optional-feature builds and checks the actual dependency graph for GPU backends. Run it with the same local configuration:

```
LIGHTCRAFT_LOCAL=var/local-v1.json python3 scripts/package_v1.py BUILD_OUTPUT --dist DIST_OUTPUT --readme packaging/v1/README.md
```

The ZIP contains licenses, build metadata, the CPU-default icon and an embedded arospkg manifest. Exact unstripped files and checksums are kept beside it for diagnosis. The program archive does not install system libraries.
