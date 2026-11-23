# LightCraft for AROS

An AROS port of [LightCraft](https://github.com/storytold/lightcraft), a photo library and raw developer. It keeps a catalogue of your photos with ratings, keywords and albums, develops JPEG, PNG, TIFF, WebP, JPEG XL, PSD and camera raw files without changing the originals, and exports the results.

## Download and run

[Download 0.21.1](https://github.com/tomaszstaniak/aros-lightcraft/releases/tag/v0.21.1) for one of these systems, or install `lightcraft` with arospkg:

| Package | System |
|---|---|
| `LightCraft-0.21.1-aros-x86_64-abiv11-pc.zip` | AROS x86_64, ABIv11 distributions |
| `LightCraft-0.21.1-aros-x86_64-abiv1-pc.zip` | AROS x86_64, mainline ABIv1 (nightly 2026-11-06 or later) |
| `LightCraft-0.21.1-aros-aarch64-abiv1-raspi.zip` | AROS on Raspberry Pi, AArch64 ABIv1 (mainline nightly 2026-11-06 or later) |

Each package runs only on the system it was built for and includes LightCraft and `lightcraft-cli`. Unpack the archive anywhere writable and double-click the LightCraft icon; from a Shell, run `LightCraft [file or drawer]`. The program takes the stack it needs itself. `ReadMe.txt` in the drawer describes installation, the command line, where the library is kept and the interface renderer.

## Known limitations

Developing and exporting run on the processor. AI Denoise, AI masks and HEIC/HEIF import are not built in, and a library should be used by one LightCraft at a time. Changes of the whole window (scrolling, zooming) redraw all of it and follow with a delay on slow machines and in emulators. The Raspberry Pi build was tested only in an emulator. The [release notes](docs/releases/v0.21.1.md) list the rest.

## Build from source

This repository contains source revisions, AROS patches and build scripts. See [Building](docs/development.md), [Patch workflow](docs/patching.md) and [Source revisions](upstreams.json). The window, clipboard and start-up code use [egui-aros](https://github.com/tomaszstaniak/egui-aros), pinned in `upstreams.json`, which also holds the build tools shared by the Craft ports; the Rust standard library for AROS comes from [rust-aros](https://github.com/tomaszstaniak/rust-aros).

The repository holds the build recipe and patches; the source archive of each release adds the pinned upstream inputs. Licenses and author notices are in the source and application archives.
