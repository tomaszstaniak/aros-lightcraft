# Build the x86_64 v1 SDK and runtime

This recipe uses the pinned official Rust 1.99 nightly compiler and an AROS library-only integration. It does not modify the compiler executable. Keep all outputs separate from existing SDKs, toolchains and installed systems.

## Inputs

Use the repositories and complete revisions in `upstreams.json`. `aros-v1-sdk` starts at `2eb81b402b0d3de6d0b068ce74fdb6eb653f2d60`; apply `patches/aros-v1-sdk/series` in order. The series preserves the existing official-profile integration, removes workstation source paths from compiled std diagnostics and supports an explicit `-nix` Path grammar.

```
python3 scripts/source.py prepare --repository aros-v1-sdk
python3 scripts/source.py verify --repository aros-v1-sdk
```

The source's `tools/crosstools/rust/unmodified/channel.json` pins the official host tools and stock rust-src archive, including their checksums. The compiler commit is `504869653f510b279c542e65ccd1ea9710c119ba`, channel `nightly-2026-08-04`. Use its paired Cargo and rust-src; the older compiler used for the v11 release is a separate input.

Building AROS on macOS requires a case-sensitive build volume, GNU make, GNU sed, GNU awk, Bison 3 and Flex. Put those tools on PATH before the system tools. Use the native x86_64 AROS GCC 10.5.0 toolchain. Supply a compatible host `collect-aros` and the AROS LLVM tools directory containing `bin/llvm-ar`, `llvm-nm`, `llvm-objcopy` and `ld.lld`. These are build tools; the target remains x86_64.

## C SDK and runtime

Set the following paths to dedicated local directories. `SOURCE` is the absolute path to `work/aros-v1-sdk`; `BUILD` is an empty case-sensitive directory; `TOOLCHAIN` is the existing native GCC toolchain directory. `PORTSSOURCES` is a private download directory. Existing verified source archives may be reused read-only.

Configure writes a generated `x86_64-aros-uname` script beside the compiler. To keep the original toolchain untouched, create a private directory containing links to its entries, except `*-uname`, and use that directory as `PRIVATE_TOOLCHAIN`.

```
cd "$BUILD"
SED=gsed ac_cv_prog_cc_c23=no ac_cv_prog_cc_c11=no \
  "$SOURCE/configure" --target=pc-x86_64 \
  --with-aros-toolchain-install="$PRIVATE_TOOLCHAIN" \
  --with-portssources="$PORTSSOURCES"

gmake -j4 workbench-libs-fd-includes
gmake -j4 workbench-libs-fd
gmake -j4 compiler-stdc
gmake -j4 compiler-posixc
gmake -j4 workbench-network-stacks-arostcp-bsdsocket
```

Run these goals in order. A fresh MetaMake bootstrap cannot safely be started by several top-level goals simultaneously. The build also produces the shared headers and static libraries needed by these targets.

The resulting C SDK is `bin/pc-x86_64/AROS/Developer`. It includes the complete pthread implementation and posixc import libraries. Do not combine its headers with an older pthread archive. The runtime files are `AROS/Libs/fd.library`, `posixc.library`, `stdc.library` and `AROS/System/Network/AROSTCP/C/AROSTCP`, relative to `bin/pc-x86_64`.

The required runtime proposals include fd.library 51, posixc.library 0.41 and matching stdc/AROSTCP components. Replacing only the files used at link time does not update a running system. Install a coherent set on an isolated test system, reboot and verify the loaded versions. Preserve the previous installation before changing it. This repository's application archive does not install system libraries.

## Rust SDK

Set `CSDK` to the C SDK above, `HOST_ROOT` to the pinned official host installation, `RUST_SRC` to the verified stock Rust source root containing `library/`, and `LLVM_TOOLS` and `COLLECT_AROS` to the selected host tools. `PREFIX` and `STD_WORK` must be private output directories.

```
python3 "$SOURCE/tools/crosstools/rust/unmodified/integrate.py" \
  --target x86_64-unknown-aros \
  --prefix "$PREFIX" --work "$STD_WORK" \
  --host-root "$HOST_ROOT" --host-triple aarch64-apple-darwin \
  --rust-src "$RUST_SRC" --sdk "$CSDK" \
  --crosstools "$LLVM_TOOLS" --collect-aros "$COLLECT_AROS" \
  --cc "$TOOLCHAIN/x86_64-aros-gcc" --cc-arg=-nix \
  --offline --jobs 2
```

`--cc-arg=-nix` selects both the C startup and the corresponding Rust Path grammar. Without it, the SDK retains native AmigaDOS path semantics. LightCraft's v1 build driver requires the `-nix` variant and rejects a mixed configuration. DOS paths supplied by Shell, Workbench and requesters are resolved at the application's boundaries before being passed to the engine.

The builder maps std source locations to `/rust-src/` and its temporary paths to `/aros-build/` before compiling them into rlibs. Stripping an application cannot remove source paths already embedded as diagnostic constants in a precompiled std.

The installed `aros-official-rust.json` records compiler identity, C flags, source and SDK hashes, generated wrappers and SDK generation. Preserve it with the build records. See [mainline-v1.md](mainline-v1.md) for the application build.
