# LightCraft 0.21.1 for AROS, revision 1

The AROS port of LightCraft 0.21.1, a photo library and raw developer. It keeps a catalogue of your photos, develops JPEG, PNG, TIFF, WebP, JPEG XL, PSD and camera raw files without changing the originals, and exports the results. It is built from the LightCraft 0.21.1 release (tag `v0.21.1`), for three AROS systems.

## Downloads

| File | System |
|---|---|
| `LightCraft-0.21.1-aros-x86_64-abiv11-pc.zip` | AROS x86_64, ABIv11 distributions (unchanged, from the 0.21.1 release) |
| `LightCraft-0.21.1-r1-aros-x86_64-abiv1-pc.zip` | AROS x86_64, mainline ABIv1 (nightly 2026-11-24 or later) |
| `LightCraft-0.21.1-r1-aros-aarch64-abiv1-raspi.zip` | AROS on Raspberry Pi, AArch64 ABIv1 (mainline nightly 2026-11-24 or later) |
| `LightCraft-0.21.1-r1-source.zip` | Port sources, patches, pinned inputs and build recipe |

Each package runs only on the system it was built for. `SHA256SUMS` lists the checksums. The packages can also be installed with the AROS package manager: `apkg install lightcraft`.

## What is new in revision 1

Revision 1 is a rebuild of the mainline x86_64 and Raspberry Pi packages for AROS nightly builds from 2026-11-24 on. The programs have no other changes. `LightCraft --version` prints `0.21.1-r1`.

- The nightly of 2026-11-24 changed a system structure that programs are built against. Packages built before it do not start on that nightly or a later one, and these packages do not start on an earlier one.
- On a nightly before 2026-11-24, keep LightCraft 0.21.1.
- The ABIv11 package is not affected and stays at 0.21.1.

With the package manager: `apkg upgrade lightcraft`. Settings and data in `LightCraftData` are kept.

Checked for this revision on the mainline x86_64 nightly of 2026-11-24, in an emulator: installation and verification with the package manager and a start from Workbench. The Raspberry Pi package was built the same way and not run for this revision.

## What was new in 0.21.1

This release moves from LightCraft 0.13.0 to LightCraft 0.21.1. For the changes in the program itself, see the release notes of LightCraft upstream. On the AROS side:

- A package for the Raspberry Pi, besides ABIv11 distributions and mainline x86_64.
- The window is drawn by egui-aros, as in the other Craft programs: with the CPU only the parts of the window that changed are drawn again; in the emulators used for testing, a typical frame takes 0.015 to 0.03 s.
- OpenGL can draw the window. The `GUI_RENDERER` ToolType in the icon, or `--gui-renderer` in a Shell, chooses `AUTO` (the default), `CPU` or `GPU`. `AUTO` uses OpenGL only when it is not Mesa's software renderer. The `IMAGE_COMPUTE` setting of 0.13.0 is gone: developing always runs on the processor.
- The program takes the stack it needs itself; `Stack` is no longer needed before a Shell start.
- `lightcraft-cli mcp`, the MCP server, is available.
- Settings, the default library and the log file `LightCraft.log` are kept in `LightCraftData` in the program drawer, as in 0.13.0; an upgrade keeps the library.

With the package manager: `apkg upgrade lightcraft`.

## Installation

Unpack the archive for your system anywhere writable and double-click LightCraft. From a Shell, run `LightCraft [--gui-renderer CPU|AUTO|GPU] [file or drawer]`; files and drawers named are imported. To upgrade by hand, unpack the new version to a new place and move `LightCraftData` into it. The archive also holds a `.arospkg` drawer with the arospkg description; after unpacking by hand it can be deleted.

`LightCraft --version` and the first line of `LightCraft.log` name the build (`0.21.1` and the target); please include them when you report a problem.

## Known limitations

- Developing and exporting run on the processor; the GPU setting has no effect. Large raw files and the generated demo photos take time on slow machines and in emulators.
- Not built in: AI Denoise, AI masks and HEIC/HEIF import. AVIF files can be exported but not imported.
- Use a library in one LightCraft (window or `lightcraft-cli`) at a time: the library cannot be locked against a second program on AROS.
- Links, other programs (Edit In, Open With) and folder windows are not opened from LightCraft. The low-disk warning is not shown.
- Chinese, Japanese and Korean fonts are not built in; such text shows as boxes.
- Changes of the whole window (scrolling, zooming, opening a dialog) redraw all of it; on slow machines and in emulators these follow with a delay.
- Not tested on AROS in this release: Workbench start, the file requesters, the clipboard, keyboard layouts other than the US one, printing, the slideshow, Lightroom import and the MCP server beyond its handshake.
- ABIv11: AROS One 1.3 has only Mesa's software renderer, so `AUTO` uses the CPU there. `GPU` works with it but draws a frame in seconds.
- Mainline x86_64: `AUTO` uses the CPU, because a program that has opened OpenGL there leaves its log file in use after it ends (seen on nightly 2026-11-10). `GPU` still opens OpenGL; with VirGL in an emulator it drew correctly. Hardware OpenGL drivers have not been tested.
- Raspberry Pi: tested in an emulator only. OpenGL has not been tested on Pi hardware, so `AUTO` uses the CPU; save your work before you try `GPU`.

Licences and notices for LightCraft, the fonts built into it and everything else linked into it are in the `Licenses` drawer of each package.
