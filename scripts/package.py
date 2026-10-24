#!/usr/bin/env python3
"""Package one `lc.py build` output as the release archive described in packaging/release.json.

    package.py BUILD_OUTPUT [--dist DIR]

Writes, into DIR (default: dist/ of this repository), the binary archive, the source archive
(this repository at HEAD: pins, patches, scripts, recipe), the release notes and SHA256SUMS.
Refuses to replace a file that is already there, a build that is not from a clean, committed
work copy, a build made with other features, binaries whose bytes differ from the build
manifest, and a repository whose patch series is not the one the build used.

The binary archive is a ZIP that unpacks to one drawer and its icon:

    LightCraft.info              drawer icon
    LightCraft/LightCraft        the editor (Workbench icon LightCraft.info, with its stack)
    LightCraft/lightcraft-cli    command line and MCP server
    LightCraft/README.md         installation and use
    LightCraft/SOURCE.txt        what the binaries were built from
    LightCraft/Licenses/...      LightCraft's licenses and notices, AROS-NOTICE.txt and
                                 THIRD-PARTY.txt (every crate linked into the binaries)

Entries are sorted, dated with the repository's HEAD commit time and carry Unix modes (0755
for the programs), so the same inputs give the same bytes.
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import time
import tomllib
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lcconfig  # noqa: E402

REPO = lcconfig.REPO
WORK = REPO / "work" / "lightcraft"
PACKAGING = REPO / "packaging"
LICENSE_NAMES = re.compile(r"^(LICEN[CS]E|COPYING|NOTICE|COPYRIGHT|UNLICENSE)", re.I)


class Failure(Exception):
    pass


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def git(*args, cwd=REPO):
    return subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True).stdout


def check_build(build, release):
    manifest = json.loads((build / "manifest.json").read_text())
    if manifest.get("status") not in ("built-not-run", "accepted"):
        raise Failure(f"{build}: build status is {manifest.get('status')!r}, not a finished build")
    if manifest["work_dirty"] or manifest["source"] != "committed HEAD":
        raise Failure(f"{build}: built from a dirty or uncommitted work copy")
    command = manifest["command"]
    features = release["build"]["features"]
    if not any(command[i:i + len(features)] == features for i in range(len(command))):
        raise Failure(f"{build}: not built with {' '.join(features)}")
    if release["build"].get("lto") == "fat" and 'profile.release.lto="fat"' not in command:
        raise Failure(f"{build}: not built with --lto fat")
    if manifest["toolchain"]["panic"] != release["build"]["panic"] or manifest["abi"] != release["build"]["abi"]:
        raise Failure(f"{build}: profile {manifest['abi']} / panic={manifest['toolchain']['panic']} is not the release profile")
    if "linked_packages" not in manifest:
        raise Failure(f"{build}: the manifest has no linked_packages (rebuild with the current lc.py)")
    for name, info in manifest["binaries"].items():
        if sha256((build / name).read_bytes()) != info["sha256"]:
            raise Failure(f"{build / name}: bytes differ from the build manifest")
    series_dir = REPO / "patches" / "lightcraft"
    current = {n: sha256((series_dir / n).read_bytes()) for n in (series_dir / "series").read_text().split()}
    if current != manifest["series"]:
        raise Failure("patches/lightcraft is not the series this build used")
    if git("status", "--porcelain").strip():
        raise Failure("commit this repository first: the source archive is made from HEAD")
    version = tomllib.loads((WORK / "Cargo.toml").read_text())["workspace"]["package"]["version"]
    if version != release["version"]:
        raise Failure(f"work copy version {version} is not the release version {release['version']}")
    return manifest


# apkg 0.6 accepts one file of up to 128 MiB unpacked (64 MiB before 0.6).
MEMBER_LIMIT = 128 << 20


def stripped(data, name):
    """The program with unneeded symbols and .comment removed: the form verified to load on AROS
    (a full strip loses the relocations AROS applies at load time)."""
    cfg = lcconfig.load(["aros_strip"])
    with tempfile.TemporaryDirectory() as tmp:
        src, dst = Path(tmp) / "in", Path(tmp) / "out"
        src.write_bytes(data)
        subprocess.run([cfg["aros_strip"], "--strip-unneeded", "--remove-section", ".comment", "-o", str(dst), str(src)], check=True)
        out = dst.read_bytes()
    if len(out) > MEMBER_LIMIT:
        raise Failure(f"{name} is {len(out)} bytes after stripping, over apkg's 128 MiB limit for one file")
    return out


def third_party(manifest):
    """Every package linked into the binaries, except LightCraft's own (covered by its license),
    with its license expression and license files."""
    parts = ["Third-party Rust packages linked into LightCraft and lightcraft-cli",
             "=" * 68, "",
             "Built with the Rust standard library and these packages. Each entry gives the",
             "package, its version, its declared license and the license files it ships.", ""]
    own = str(WORK.resolve())
    entries = []
    for package_id, manifest_path in manifest["linked_packages"].items():
        crate_dir = Path(manifest_path).parent
        meta = tomllib.loads(Path(manifest_path).read_text()).get("package", {})
        name, version = meta.get("name", "?"), meta.get("version", "?")
        if isinstance(version, dict) or isinstance(meta.get("license"), dict):
            # workspace-inherited fields: a member of a workspace (the Rust library or LightCraft)
            root = crate_dir
            while root != root.parent and not ((root / "Cargo.toml").exists() and "workspace" in tomllib.loads((root / "Cargo.toml").read_text())):
                root = root.parent
            ws = tomllib.loads((root / "Cargo.toml").read_text()).get("workspace", {}).get("package", {})
            version = ws.get("version", "?") if isinstance(version, dict) else version
            meta = {**meta, "license": ws.get("license", meta.get("license"))}
        if str(crate_dir.resolve()).startswith(own) or "/build/v11/src/" in str(crate_dir):
            continue
        license_expr = meta.get("license") or ("see " + meta["license-file"] if meta.get("license-file") else "not declared")
        files = sorted(p for p in crate_dir.iterdir() if p.is_file() and LICENSE_NAMES.match(p.name))
        if not files and "/lib/rustlib/src/rust/" in str(crate_dir):
            # The standard library's crates carry no license files; the Rust tree's root has them.
            rust = Path(str(crate_dir).split("/lib/rustlib/src/rust/")[0] + "/lib/rustlib/src/rust")
            files = sorted(p for p in rust.iterdir() if p.is_file() and LICENSE_NAMES.match(p.name))
            license_expr = license_expr if license_expr != "not declared" else "MIT OR Apache-2.0 (the Rust project)"
        entries.append((name, version, license_expr, files, package_id))
    entries.sort()
    for name, version, license_expr, files, package_id in entries:
        parts += ["-" * 68, f"{name} {version}", f"License: {license_expr}", ""]
        for f in files:
            parts += [f"--- {f.name} ---", f.read_text(errors="replace").rstrip(), ""]
        if not files:
            parts += ["(the package ships no separate license file)", ""]
    vendored = Path(manifest["linked_packages"].get(next((k for k in manifest["linked_packages"] if "#libc@" in k), ""), "")).parent
    for rel in ["csrc/vendor/jitterentropy/LICENSE.bsd", "csrc/vendor/arospkg-entropy/LICENSE"]:
        path = vendored / rel
        if path.is_file():
            parts += ["-" * 68, f"libc-aros: {rel}", "", path.read_text(errors="replace").rstrip(), ""]
    return "\n".join(parts) + "\n", [(n, v, l) for n, v, l, _, _ in entries]


def rust_docs(manifest):
    """The Rust toolchain's own license notices for its standard library (share/doc/rust of the
    rustc the build used, which must report the build's version)."""
    cfg = lcconfig.load(["toolchain"])
    wrapper = Path(subprocess.run(["rustup", "which", "rustc", "--toolchain", cfg["toolchain"]], check=True,
                                  capture_output=True, text=True).stdout.strip())
    # The private toolchain's rustc is a script that runs the host nightly's rustc on its sysroot.
    found = re.search(r"exec (\S+/bin/rustc)", wrapper.read_text(errors="replace")) if wrapper.stat().st_size < 4096 else None
    rustc = Path(found.group(1)) if found else wrapper
    version = subprocess.run([rustc, "-V"], check=True, capture_output=True, text=True).stdout.strip()
    if version != manifest["toolchain"]["rustc"]:
        raise Failure(f"{rustc} reports {version!r}, not the build's {manifest['toolchain']['rustc']!r}")
    doc = rustc.parent.parent / "share" / "doc" / "rust"
    out = {"Rust/COPYRIGHT-library.html": (doc / "COPYRIGHT-library.html").read_bytes()}
    for f in sorted((doc / "licenses").iterdir()):
        out[f"Rust/licenses/{f.name}"] = f.read_bytes()
    return out


def source_txt(release, manifest, archive_names, packaged=None):
    up = manifest["upstreams"]
    lines = [release["title"], "", "Built from:",
             f"  LightCraft {up['lightcraft']['url']} at {up['lightcraft']['commit']}",
             f"  with the {len(manifest['series'])} patches in patches/lightcraft/series of the source archive",
             f"  rust-aros libc-aros at {manifest['libc_aros']['rust_aros_commit']}",
             f"  AROS compiler/pthread at {manifest['pthread']['aros_src_commit'] if 'aros_src_commit' in manifest['pthread'] else manifest['pthread']}",
             f"  Rust {manifest['toolchain']['rustc']}",
             f"  {manifest['toolchain']['gcc']}, x86_64 ABIv11 SDK",
             "", "Source archive: " + archive_names["source"],
             "Rebuild: see docs/development.md in the source archive.",
             "", "SHA-256 of the programs:"]
    for name, info in sorted(manifest["binaries"].items()):
        lines.append(f"  {info['sha256']}  {name}")
    if packaged:
        lines += ["", "As packaged (strip --strip-unneeded --remove-section .comment):"]
        lines += [f"  {sha}  {name}" for name, sha in sorted(packaged.items())]
    return "\n".join(lines) + "\n"


def zip_entry(z, name, data, mode, date):
    info = zipfile.ZipInfo(name, date_time=date)
    info.create_system = 3
    info.external_attr = (mode & 0xFFFF) << 16
    info.compress_type = zipfile.ZIP_DEFLATED
    z.writestr(info, data, compresslevel=9)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("build", type=Path)
    p.add_argument("--dist", type=Path, default=REPO / "dist")
    p.add_argument("--packaging", type=Path, default=PACKAGING,
                   help="directory with release.json, README.md and RELEASE-NOTES.md (default: packaging/);"
                        " AROS-NOTICE.txt always comes from packaging/")
    a = p.parse_args()
    release_dir = a.packaging.resolve()
    release = json.loads((release_dir / "release.json").read_text())
    try:
        manifest = check_build(a.build.resolve(), release)
        names = {"archive": release["archive"], "source": release["source_archive"], "notes": release["release_notes"]}
        a.dist.mkdir(parents=True, exist_ok=True)
        for n in names.values():
            if (a.dist / n).exists():
                raise Failure(f"{a.dist / n} exists; a delivered file is never replaced")

        head_time = int(git("log", "-1", "--format=%ct").decode().strip())
        date = time.gmtime(head_time)[:6]
        drawer = release["drawer"]
        files = {}  # archive path -> (bytes, mode)
        for name in manifest["binaries"]:
            data = (a.build / name).read_bytes()
            if release["build"].get("strip"):
                data = stripped(data, name)
            files[f"{drawer}/{name}"] = (data, 0o100755)
        with tempfile.TemporaryDirectory() as tmp:
            source = WORK / release["icon_source"].removeprefix("work:")
            subprocess.run([sys.executable, str(REPO / "scripts" / "icons.py"), str(source), tmp, drawer, str(release["stack"])], check=True)
            import icons
            w, h, rows = icons.decode_rgba(source)
            (Path(tmp) / drawer / f"{drawer}.info").write_bytes(icons.icon(w, h, rows, icons.ICON_TOOL, release["stack"], ["GUI_RENDERER=CPU", "IMAGE_COMPUTE=CPU"]))
            files[f"{drawer}.info"] = ((Path(tmp) / f"{drawer}.info").read_bytes(), 0o100644)
            files[f"{drawer}/{drawer}.info"] = ((Path(tmp) / drawer / f"{drawer}.info").read_bytes(), 0o100644)
        files[f"{drawer}/README.md"] = ((release_dir / "README.md").read_bytes(), 0o100644)
        packaged = {n: sha256(files[f"{drawer}/{n}"][0]) for n in manifest["binaries"]} if release["build"].get("strip") else None
        files[f"{drawer}/SOURCE.txt"] = (source_txt(release, manifest, names, packaged).encode(), 0o100644)
        public_manifest = json.loads(json.dumps(manifest))
        replacements = [(str(REPO), "/port"), (str(Path(manifest["toolchain"]["sysroot"])), "/rust"), (str(Path(lcconfig.load()["aros_sdk"])), "/sdk"), (str(Path.home()), "/host")]
        def sanitize(value):
            if isinstance(value, str):
                for old, new in replacements: value = value.replace(old, new)
                return value
            if isinstance(value, list): return [sanitize(v) for v in value]
            if isinstance(value, dict): return {sanitize(k): sanitize(v) for k,v in value.items()}
            return value
        public_manifest = sanitize(public_manifest)
        public_manifest["packaged_binaries"] = {name: {"sha256": sha256(files[f"{drawer}/{name}"][0]), "unstripped_sha256": info["sha256"], "bytes": len(files[f"{drawer}/{name}"][0])} for name,info in manifest["binaries"].items()}
        files[f"{drawer}/BUILD.json"] = ((json.dumps(public_manifest,indent=2)+"\n").encode(),0o100644)
        for name, info in manifest["binaries"].items():
            debug = a.dist / "debug" / (name + ".unstripped")
            debug.parent.mkdir(exist_ok=True)
            if debug.exists(): raise Failure(f"{debug} exists")
            import shutil
            shutil.copyfile(a.build / name, debug)
            if sha256(debug.read_bytes()) != info["sha256"]: raise Failure("debug copy mismatch")
        renames = release.get("notice_renames", {})
        for rel in release["lightcraft_notices"]:
            files[f"{drawer}/Licenses/LightCraft/{renames.get(rel, rel)}"] = ((WORK / rel).read_bytes(), 0o100644)
        if renames:
            note = "".join(f"{Path(new).name} is {old} in ATTRIBUTION.md, renamed to fit a 30-character AmigaDOS name.\n"
                           for old, new in renames.items())
            files[f"{drawer}/Licenses/LightCraft/RENAMED.txt"] = (note.encode(), 0o100644)
        files[f"{drawer}/Licenses/AROS-NOTICE.txt"] = ((PACKAGING / "AROS-NOTICE.txt").read_bytes(), 0o100644)
        files[f"{drawer}/Licenses/AROS-LICENSE.txt"] = (git("show", manifest["pthread"]["aros_src_commit"] + ":LICENSE", cwd=Path(lcconfig.load()["aros_src"])), 0o100644)
        text, crates = third_party(manifest)
        files[f"{drawer}/Licenses/THIRD-PARTY.txt"] = (text.encode(), 0o100644)
        for rel, data in rust_docs(manifest).items():
            files[f"{drawer}/Licenses/{rel}"] = (data, 0o100644)

        # Classic FFS volumes take names of up to 30 characters.
        long_names = sorted({part for n in files for part in n.split("/") if len(part) > 30})
        if long_names:
            raise Failure(f"archive names longer than 30 characters: {long_names}")
        archive = a.dist / names["archive"]
        partial = archive.with_name(archive.name + ".partial")
        with zipfile.ZipFile(partial, "x") as z:
            dirs = sorted({str(Path(n).parent) for n in files if "/" in n} | {d for n in files for d in
                          ["/".join(n.split("/")[:i]) for i in range(1, n.count("/"))]})
            for d in dirs:
                zip_entry(z, d + "/", b"", 0o40755, date)
            for n in sorted(files):
                zip_entry(z, n, files[n][0], files[n][1], date)
        partial.rename(archive)

        src = a.dist / names["source"]
        prefix = names["source"].removesuffix(".zip") + "/"
        excludes = [f":(exclude){x}" for x in release["source_archive_exclude"]]
        subprocess.run(["git", "-C", str(REPO), "archive", "--format=zip", f"--prefix={prefix}", "-o", str(src), "HEAD", "--", ".", *excludes], check=True)
        import io, lzma, tarfile
        with zipfile.ZipFile(src, "a", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
            inputs = [
                ("lightcraft-upstream", REPO / "upstream/lightcraft", manifest["upstreams"]["lightcraft"]["commit"], []),
                ("egui-aros", Path(lcconfig.load()["egui_aros"]), manifest["upstreams"]["egui-aros"]["commit"], []),
                ("aros-pthread", Path(lcconfig.load()["aros_src"]), manifest["pthread"]["aros_src_commit"], ["compiler/pthread", "LICENSE"]),
                ("rust-aros-inputs", Path(lcconfig.load()["rust_aros"]), manifest["libc_aros"]["rust_aros_commit"], ["std-groundwork/libc-aros", "std-groundwork/std-patch", "x86_64-aros.json.in"]),
            ]
            for label, checkout, commit, paths in inputs:
                data = git("archive", "--format=tar", commit, *paths, cwd=checkout)
                bundle.writestr(prefix + "sources/" + label + ".tar.xz", lzma.compress(data))
            std_source = Path(manifest["toolchain"]["sysroot"]) / "lib/rustlib/src/rust"
            packed = io.BytesIO()
            with tarfile.open(fileobj=packed, mode="w:xz") as tar:
                tar.add(std_source, arcname="rust", recursive=True)
            bundle.writestr(prefix + "sources/rust-std.tar.xz", packed.getvalue())
            active_crates = {(info["package"], info["version"]) for info in manifest["crates"].values()}
            for spec in json.loads((REPO / "patches/crates/crates.json").read_text())["crates"]:
                if (spec["name"], spec["version"]) not in active_crates:
                    continue
                name = f"{spec['name']}-{spec['version']}.crate"
                crate = next(Path(lcconfig.load()["cargo_home"]).glob("registry/cache/*/"+name))
                bundle.writestr(prefix + "sources/crates/" + name, crate.read_bytes())
        (a.dist / names["notes"]).write_bytes((release_dir / "RELEASE-NOTES.md").read_bytes())

        sums = a.dist / "SHA256SUMS"
        existing = sums.read_text().splitlines() if sums.exists() else []
        listed = {line.split()[-1] for line in existing if line.strip()}
        added = [f"{sha256((a.dist / n).read_bytes())}  {n}" for n in [names["archive"], names["source"], *["debug/" + p.name for p in sorted((a.dist / "debug").iterdir())]] if n not in listed]
        sums.write_text("\n".join(existing + added) + "\n")

        record = {"release": release["title"], "build": str(a.build.resolve()), "build_id": manifest["build_id"],
                  "repository_head": git("rev-parse", "HEAD").decode().strip(), "work_head": manifest["work_head"],
                  "archive": {"name": names["archive"], "sha256": sha256(archive.read_bytes()), "bytes": archive.stat().st_size,
                              "entries": {n: sha256(d) for n, (d, _) in sorted(files.items())}},
                  "source_archive": {"name": names["source"], "sha256": sha256(src.read_bytes())},
                  "crates": len(crates)}
        (a.build / f"package-{release['label']}.json").write_text(json.dumps(record, indent=2) + "\n")
        print(json.dumps({k: record[k] for k in ("release", "build_id", "repository_head", "crates")} |
                         {"archive": str(archive), "sha256": record["archive"]["sha256"], "source_archive": str(src)}, indent=2))
    except Failure as e:
        sys.exit(f"package: {e}")


if __name__ == "__main__":
    main()
