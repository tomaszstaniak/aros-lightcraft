"""One place for the port's paths and pins.

Values come from, in order of precedence: environment variables, the ignored
`local.json` beside `upstreams.json` (or the file named by LIGHTCRAFT_LOCAL),
and the defaults below. Workstation paths have no defaults: a missing value is
reported with the variable that sets it, never guessed.
"""
import json
import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ABI = "v11"

# key: (environment variable, default, description)
SETTINGS = {
    "aros_gcc": ("LIGHTCRAFT_AROS_GCC", None, "x86_64 AROS C compiler driver matching the SDK"),
    "aros_ar": ("LIGHTCRAFT_AROS_AR", None, "archiver from the same toolchain"),
    "aros_strip": ("LIGHTCRAFT_AROS_STRIP", None, "strip from the same toolchain (optional)"),
    "aros_sdk": ("LIGHTCRAFT_AROS_SDK", None, "ABIv11 SDK used as --sysroot"),
    "rust_aros": ("LIGHTCRAFT_RUST_AROS", None, "rust-aros Git checkout (target template, libc-aros)"),
    "rust_aros_commit": ("LIGHTCRAFT_RUST_AROS_COMMIT", "7b00bb2aab0622788e60601f39f5cf79b63c3509",
                         "rust-aros commit whose target template and libc-aros are used"),
    "aros_src": ("LIGHTCRAFT_AROS_SRC", None, "deadwood2/AROS (ABIv11) Git checkout; read-only source of the pthread link library"),
    "aros_src_commit": ("LIGHTCRAFT_AROS_SRC_COMMIT", "5376f09bc1ed0c36a12fbb096406013f8a046e89",
                        "commit whose compiler/pthread matches the SDK's libpthread.a"),
    "egui_aros": ("LIGHTCRAFT_EGUI_AROS", None, "egui-aros Git checkout; its commit pinned in upstreams.json is built"),
    "egui_upstream_root": ("LIGHTCRAFT_EGUI_UPSTREAM_ROOT", None, "read-only prepared egui-aros upstream repositories"),
    "toolchain": ("LIGHTCRAFT_TOOLCHAIN", None, "rustup name of the private AROS std toolchain"),
    "rustc_version": ("LIGHTCRAFT_RUSTC_VERSION", "rustc 1.100.0-nightly (0dfb098f3 2026-08-31)",
                      "exact `rustc --version` the toolchain must report"),
    "cargo_home": ("LIGHTCRAFT_CARGO_HOME", "deps/v11/cargo-home", "private CARGO_HOME (relative: to the repository)"),
    "build_root": ("LIGHTCRAFT_BUILD_ROOT", "build/v11", "build outputs (relative: to the repository)"),
    "panic": ("LIGHTCRAFT_PANIC", "unwind", "native panic profile: unwind or abort"),
}


class ConfigError(Exception):
    pass


def _local():
    path = Path(os.environ.get("LIGHTCRAFT_LOCAL", REPO / "local.json"))
    if not path.exists():
        return {}, None
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError) as error:
        raise ConfigError(f"{path}: {error}") from error
    unknown = set(data) - set(SETTINGS)
    if unknown:
        raise ConfigError(f"{path}: unknown keys {sorted(unknown)}")
    return data, path


def load(required=()):
    """Returns the resolved settings; raises ConfigError naming what is missing."""
    local, local_path = _local()
    out = {}
    for key, (env, default, _) in SETTINGS.items():
        value = os.environ.get(env) or local.get(key) or default
        out[key] = value
    paths = ("aros_gcc", "aros_ar", "aros_strip", "aros_sdk", "rust_aros", "aros_src", "egui_aros", "egui_upstream_root", "cargo_home", "build_root")
    for key in paths:
        if out[key] and not os.path.isabs(out[key]):
            base = REPO if os.environ.get(SETTINGS[key][0]) or key not in local else (local_path.parent if local_path else REPO)
            out[key] = str(base / out[key])
    missing = [key for key in required if not out.get(key)]
    if missing:
        lines = [f"  {k}: set {SETTINGS[k][0]} or \"{k}\" in local.json ({SETTINGS[k][2]})" for k in missing]
        raise ConfigError("missing configuration:\n" + "\n".join(lines))
    if out["panic"] not in ("unwind", "abort"):
        raise ConfigError("panic must be unwind or abort")
    return out


def describe():
    local, path = _local()
    rows = []
    for key, (env, default, text) in SETTINGS.items():
        source = "env" if os.environ.get(env) else ("local" if key in local else ("default" if default else "unset"))
        rows.append(f"{key:18} {source:8} {env}  ({text})")
    return f"local file: {path or 'none'}\n" + "\n".join(rows)
