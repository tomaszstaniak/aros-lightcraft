# LightCraft 0.13.0 for AROS

First AROS x86_64 ABIv11 release, with a CPU interface and CPU image processing.

Open images, adjust development settings, preview changes and export a copy. The catalog preserves non-destructive edits between sessions. PNG, JPEG, TIFF, WebP and JPEG XL import and export are included, along with RAW development and AVIF export.

The GUI_RENDERER and IMAGE_COMPUTE ToolTypes and command-line arguments select CPU, AUTO or GPU independently. Both default to CPU. This build contains CPU backends only; AUTO logs its CPU fallback and GPU reports an error.

Unpack the program archive to a writable drawer and double-click LightCraft. Shell launches require `Stack 16777216`. Keep LightCraftData when upgrading.

This build requires x86_64 ABIv11. AVIF import, HEIF, neural denoise, SAM, MCP stdio and network model downloads are unavailable. Keyboard and clipboard conversion is limited to Latin-1. RAW compatibility varies by camera. A write directly to the root of some volumes may fail; choose a destination drawer.

The source archive contains pinned upstream sources, patches, dependency inputs and the build recipe. Licenses and notices are included in the program archive.
