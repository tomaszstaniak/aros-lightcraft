# Private libc adjustments

The base is rust-aros `7b00bb2aab0622788e60601f39f5cf79b63c3509`.
These patches are applied to a generated private source tree, never Cargo's cache or a shared sysroot.

1. Declare memchr, required by the selected dependency graph.
2. Serialize Rust filesystem path entry points and descriptor allocation/close in the selected v11 CRT. Its `posixc/__upath.c` reuses one conversion buffer; `open.c` and `close.c` explicitly exclude threaded use. Concurrent independent-file operations reproduced errors on all four native probe workers; serial operations and moving a File between threads succeeded. The GUI failure included JPEG bytes under `catalog.snap`, so suppressing rename errors or deleting the destination would not repair the cause.

Distinct `rs_fs_*` wrappers call the original CRT symbols while holding one pthread mutex. Internal CRT calls do not re-enter the wrappers. The wrappers preserve errno around unlocking. Socket tagging/ownership remains separate. Blocking reads/writes do not hold the filesystem gate; application callers synchronize shared File access. This is a compatibility boundary for LightCraft, not a change to the SDK's public guarantees.

