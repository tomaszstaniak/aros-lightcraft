# LightCraft 0.13.0 for AROS

First AROS x86_64 ABIv11 release, with a CPU interface and CPU image processing.

Open images, adjust development settings, preview changes and export a copy. The catalog preserves non-destructive edits between sessions. PNG, JPEG, TIFF, WebP and JPEG XL import and export are included, along with RAW development and AVIF export.

The GUI_RENDERER and IMAGE_COMPUTE ToolTypes and command-line arguments select CPU, AUTO or GPU independently. Both default to CPU. This build contains CPU backends only; AUTO logs its CPU fallback and GPU reports an error.

Unpack the program archive to a writable drawer and double-click LightCraft. Shell launches require `Stack 16777216`. Keep LightCraftData when upgrading. The package is also available as `lightcraft` through arospkg.

## Feature availability

LightCraft uses its own codec libraries. The following restrictions have different causes:

| Feature | Reason in this release |
|---|---|
| AVIF import | LightCraft 0.13.0 recognizes the format but has no decoder. AVIF export works. Import needs an upstream decoder integration. |
| HEIF/HEIC | The optional upstream Rust decoder is not enabled. AROS compatibility still needs to be established. |
| Neural denoise | The optional inference feature is not enabled. Upstream has a CPU implementation; dependencies, local models, memory and processing time need further work. CPU rendering does not require this feature to be disabled. |
| SAM segmentation | The optional Candle-based feature is not enabled. Upstream supports CPU execution; model loading, memory use and processing time remain to be established on AROS. |
| MCP stdio | The port explicitly blocks startup until the stdin reader can be interrupted and finished safely, including when the output connection breaks. |
| Model downloads | The port explicitly blocks downloads pending verification of DNS cancellation and worker shutdown. This does not establish a lack of network support. |

MCP follow-up includes EOF, broken output and closing during a running tool, in addition to handshake and tool discovery. Denoise can first use a locally supplied model; download support can be addressed separately. HEIF uses an existing optional decoder, whereas AVIF import requires a decoder integration. See [feature status and follow-up work](https://github.com/tomaszstaniak/aros-lightcraft/blob/main/docs/features.md).

This build requires x86_64 ABIv11. Native keyboard and clipboard conversion is limited to Latin-1. RAW compatibility varies by camera. Writing directly to the root of some volumes may fail; choose a destination drawer. No models are downloaded at startup.

The source archive contains pinned upstream sources, patches, dependency inputs and the build recipe. Licenses and notices are included in the program archive.
