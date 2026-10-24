"""Build the CPU port with a qualified official x86_64 ABIv1 Rust installation."""
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lc

Failure = lc.Failure
COMPILER = "504869653f510b279c542e65ccd1ea9710c119ba"
TRIPLE = "x86_64-unknown-aros"


def read_installation(prefix):
    prefix = Path(prefix)
    data = json.loads((prefix / "aros-official-rust.json").read_text())
    profile = data.get("profile", {})
    if profile.get("abi") != 1 or profile.get("arch") != "x86_64" or profile.get("triple") != TRIPLE:
        raise Failure("require the official x86_64 ABIv1 installation")
    if data.get("compiler_commit") != COMPILER:
        raise Failure("official compiler differs from the qualified mainline profile")
    for name, expected in data["installed"].items():
        if lc.sha256_file(prefix / name) != expected:
            raise Failure("installed SDK wrapper or target changed: " + name)
    source = next((Path(n) for n in data["inputs"] if n.endswith("/unmodified/profiles.py")), None)
    if source is None or lc.sha256_file(source) != data["inputs"][str(source)]:
        raise Failure("the SDK's qualified validation source is missing or changed")
    spec = importlib.util.spec_from_file_location("aros_official_profiles", source)
    module = importlib.util.module_from_spec(spec)
    previous_bytecode = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
        module.validate_installation(prefix, COMPILER)
    finally:
        sys.dont_write_bytecode = previous_bytecode
    return data


def build_pthread(cfg, root):
    """Use the same pthread2 source as the qualified headers, never the old SDK archive."""
    import io
    import tarfile
    spec = lc.upstreams()["aros-v1-pthread"]
    upstream = lc.check_upstream("aros-v1-pthread", spec)
    dest = root / ("pthread-v1-" + spec["commit"][:12])
    source = dest / "compiler/pthread"
    if not source.exists():
        dest.mkdir(parents=True, exist_ok=True)
        data = lc.run(["git", "-C", upstream, "archive", "--format=tar", spec["commit"], "compiler/pthread", "LICENSE"]).stdout
        with tarfile.open(fileobj=io.BytesIO(data)) as tar:
            tar.extractall(dest, filter="data")
    for name in ("pthread.h", "semaphore.h", "sched.h"):
        if (source / name).read_bytes() != (Path(cfg["aros_sdk"]) / "include" / name).read_bytes():
            raise Failure("pthread source differs from the qualified SDK header: " + name)
    names, collecting = [], False
    for line in (source / "mmakefile.src").read_text().splitlines():
        if line.startswith(("LINKLIBFILES", "PTHREADFUNCS")):
            collecting = True
            line = line.split(":=", 1)[1]
        if collecting:
            names += [n for n in line.replace("\\", " ").split() if n]
            collecting = line.rstrip().endswith("\\")
    objects = dest / "objects"
    objects.mkdir(exist_ok=True)
    commands = []
    for name in names:
        command = [cfg["aros_gcc"], "-O2", "-mcmodel=large", "-fno-omit-frame-pointer", "-fno-pic",
                   "-I", str(source), "-c", str(source / (name + ".c")), "-o", str(objects / (name + ".o"))]
        commands.append(command)
        lc.run(command)
    archive = dest / "libpthread-v1.a"
    lc.run([cfg["aros_ar"], "rcs", archive, *[objects / (n + ".o") for n in names]])
    # The upstream archive contains an alternate implementation of this one function.
    # Normal archive extraction selects pthread.o first; explicit pre-link objects
    # must make that same selection rather than define it twice.
    prelink_members = [n for n in names if n != "pthread_attr_setstacksize"]
    # Reject a changed provider inventory before constructing an explicit-object link.
    nm = str(Path(cfg["aros_ar"]).with_name(Path(cfg["aros_ar"]).name.removesuffix("-ar") + "-nm"))
    providers = {}
    for name in names:
        text = lc.run([nm, "-g", "--defined-only", objects / (name + ".o")]).stdout.decode()
        for line in text.splitlines():
            row = line.split()
            if len(row) == 3 and row[1] in ("T", "D", "B", "R", "S", "C"):
                providers.setdefault(row[2], []).append(name)
    duplicates = {key: sorted(value) for key, value in providers.items() if len(value) > 1}
    if duplicates != {"pthread_attr_setstacksize": ["pthread", "pthread_attr_setstacksize"]}:
        raise Failure("unexpected pthread duplicate-provider inventory: " + str(duplicates))
    for required in ("pthread_condattr_setclock", "pthread_condattr_getclock", "pthread_create", "pthread_cond_init", "pthread_cond_timedwait"):
        if required not in providers:
            raise Failure("matching pthread implementation lacks " + required)
    record = dict(source=spec, duplicate_providers=duplicates, prelink_members=prelink_members, headers={n: lc.sha256_file(source / n) for n in ("pthread.h", "semaphore.h", "sched.h")},
                  commands=commands, archive_sha256=lc.sha256_file(archive), members=names,
                  sdk_archive_sha256=lc.sha256_file(Path(cfg["aros_sdk"]) / "lib/libpthread.a"),
                  native_runtime="UNTESTED")
    (dest / "manifest.json").write_text(json.dumps(record, indent=2) + "\n")
    return archive, record


def build(args, cfg):
    cfg = lc.lcconfig.load(["official_sdk", "official_libc_archive", "aros_gcc", "aros_ar", "aros_sdk", "egui_aros", "cargo_home", "build_root"])
    if cfg["panic"] != "abort":
        raise Failure("the selected precompiled v1 std profile requires panic=abort")
    prefix = Path(cfg["official_sdk"])
    installation = read_installation(prefix)
    expected_cc = prefix / "bin" / installation["profile"]["driver"]
    native_build = json.loads((Path(installation["native_build"]) / "result.json").read_text())
    if Path(cfg["aros_gcc"]).resolve() != expected_cc.resolve():
        raise Failure("the C compiler must be the qualified installation driver")
    if Path(cfg["aros_sdk"]).resolve() != Path(native_build["sdk"]).resolve():
        raise Failure("the configured C SDK differs from the qualified driver sysroot")
    for name in ("RUSTFLAGS", "CARGO_ENCODED_RUSTFLAGS", "RUSTC_WRAPPER", "RUSTC_WORKSPACE_WRAPPER", "CARGO_TARGET_DIR"):
        if os.environ.get(name):
            raise Failure("clear " + name + ": it would override the qualified v1 profile")
    root = Path(cfg["build_root"])
    if any(c.isspace() for c in str(root)):
        raise Failure("use a v1 build_root without whitespace for Rust pre-link object arguments")
    root.mkdir(parents=True, exist_ok=True)
    src = root / "src"
    head, dirty = lc.work_state(lc.WORK)
    files = lc.snapshot(args.worktree)
    lc.sync_tree(files, src)
    original_lock = hashlib.sha256(files["Cargo.lock"][0]).hexdigest()
    archive = Path(cfg["official_libc_archive"])
    spec = next(x for x in lc.crate_specs() if x["name"] == "libc" and "v1" in x.get("profiles", []))
    if lc.sha256_file(archive) != spec["checksum"]:
        raise Failure("application libc archive checksum mismatch")
    cache = Path(cfg["cargo_home"]) / "registry/cache/index.crates.io-1949cf8c6b5b557f"
    cache.mkdir(parents=True, exist_ok=True)
    cached = cache / archive.name
    if not cached.exists():
        shutil.copy2(archive, cached)
    crates = lc.cmd_crates(args, quiet=True)
    vendor, egui_record = lc.egui_aros_vendor(cfg, root, src)
    # The shared vendor includes a v11-only realtime-clock workaround.
    # Mainline pthread2 implements the selected condvar clock.
    vendor.pop("parking_lot_core", None)
    for name, info in crates.items():
        vendor[name] = info["path"]
    pthread_archive, pthread_record = build_pthread(cfg, root)
    command = [str(prefix / "bin/cargo"), "--config", str(prefix / "cargo-config.toml")]
    flags = ["-Lnative=" + str(Path(cfg["aros_sdk"]) / "lib"), '--cfg=aros_sdk_generation="' + installation["generation"] + '"',
             "-Cpanic=abort", "-Clink-arg=-nix",
             "-Zpre-link-args=" + " ".join(str(pthread_archive.parent / "objects" / (name + ".o")) for name in pthread_record["prelink_members"]), '--cfg=getrandom_backend="custom"',
             f"--remap-path-prefix={root}=/build", f"--remap-path-prefix={src}=/lightcraft",
             f"--remap-path-prefix={cfg['cargo_home']}=/cargo", f"--remap-path-prefix={installation['native_build']}=/rust"]
    command += ["--config", "target." + TRIPLE + ".rustflags=" + json.dumps(flags)]
    for name, path in vendor.items():
        command += ["--config", f"patch.crates-io.{name}.path=" + json.dumps(path)]
        if name in crates:
            command += ["--config", f"patch.crates-io.{name}.package=" + json.dumps(crates[name]["package"])]
    env = dict(os.environ, RUSTC=str(prefix / "bin/rustc"), RUSTDOC=str(prefix / "bin/rustdoc"),
               CARGO_HOME=cfg["cargo_home"], CARGO_TARGET_DIR=str(root / "target"), CARGO_INCREMENTAL="0",
               AROS_EXPECTED_COMPILER=COMPILER, LIGHTCRAFT_BUILD_ABI="ABIv1", AROS_CC=cfg["aros_gcc"], AROS_GCC=cfg["aros_gcc"],
               AROS_AR=cfg["aros_ar"], AROS_SDK=cfg["aros_sdk"])
    # Only the generated lock may change; application libc must match the selected SDK bindings.
    update = command + ["update", "-p", "libc", "--precise", spec["version"], "--manifest-path", str(src / "Cargo.toml")]
    if not args.online:
        update.append("--offline")
    lc.run(update, cwd=src, env=env)
    command += ["--config", 'profile.release.panic="abort"']
    if args.lto == "fat":
        command += ["--config", 'profile.release.lto="fat"']
    command += ["build", "--release", "--manifest-path", str(src / "Cargo.toml")]
    if not args.online:
        command.append("--offline")
    if args.no_default_features:
        command.append("--no-default-features")
    if args.features:
        command += ["--features", args.features]
    packages = args.package or list(lc.PACKAGES)
    for name in packages:
        if name not in lc.PACKAGES:
            raise Failure("unsupported application package: " + name)
        command += ["-p", name]
    out = root / "out" / (datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:8])
    out.mkdir(parents=True)
    record = dict(status="building", abi="x86_64 ABIv1", runtime="UNTESTED: requires matching fd51/posixc0.41/pthread2 residents",
                  compiler_commit=COMPILER, installation_generation=installation["generation"], installation=installation,
                  repository_head=lc.git(lc.REPO, "rev-parse", "HEAD"), work_head=head, work_dirty=bool(dirty),
                  path_mode="-nix", stack_bytes=16777216, renderers={"gui":"CPU", "image":"CPU"},
                  source_lock_sha256=original_lock, derived_lock_sha256=lc.sha256_file(src / "Cargo.lock"),
                  command=command, crates=crates, egui_aros=egui_record, pthread=pthread_record)
    (out / "manifest.json").write_text(json.dumps(record, indent=2) + "\n")
    print("Building x86_64 ABIv1: " + str(out), flush=True)
    with (out / "build.log").open("wb") as log:
        result = subprocess.run(command, cwd=src, env=env, stdout=log, stderr=subprocess.STDOUT)
    if result.returncode:
        record["status"] = "failed"
        (out / "manifest.json").write_text(json.dumps(record, indent=2) + "\n")
        raise Failure("v1 build failed; see " + str(out / "build.log"))
    binaries = {}
    for package in packages:
        name = lc.PACKAGES[package]
        binary = root / "target" / TRIPLE / "release" / name
        data = binary.read_bytes()
        if data[:6] != b"\x7fELF\x02\x01" or data[7] != 15 or data[8] != 1 or int.from_bytes(data[18:20], "little") != 62:
            raise Failure("binary does not identify x86_64 AROS ABIv1: " + name)
        shutil.copy2(binary, out / name)
        nm = str(Path(cfg["aros_ar"]).with_name(Path(cfg["aros_ar"]).name.removesuffix("-ar") + "-nm"))
        undefined = lc.run([nm, "-u", binary]).stdout.decode().split()
        if undefined:
            raise Failure("unresolved symbols in " + name + ": " + str(undefined[:10]))
        binaries[name] = {"sha256": lc.sha256_file(binary), "bytes": len(data), "undefined_symbols": undefined}
    record.update(status="built-not-run", binaries=binaries)
    (out / "manifest.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps({"output": str(out), "binaries": binaries, "runtime": record["runtime"]}, indent=2))
