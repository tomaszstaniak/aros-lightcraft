# Optional features and current limitations

LightCraft decodes images with its own codec libraries. The availability below follows the pinned LightCraft 0.13.0 sources and the features selected for this AROS build.

| Feature | Current state and reason |
|---|---|
| AVIF import | The pinned upstream recognizes AVIF but has no AV1 image decoder and returns an unsupported-format error. AVIF export is included. Adding import requires choosing and integrating a decoder upstream. |
| HEIF/HEIC import | Upstream provides the optional `heif` feature using the Rust `heic-rs` decoder. This build does not enable it. Compatibility with AROS has not been established; no platform incompatibility has been demonstrated. |
| Neural denoise | The inference feature is not compiled into this build. Upstream has a pure-Rust CPU implementation. CPU rendering and CPU image processing do not prevent denoise; dependencies, a suitable model, memory use and processing time still need to be checked. |
| SAM segmentation | The optional segmentation feature is not compiled into this build. Upstream uses Candle and supports CPU execution. The AROS port has not established model loading, memory requirements or usable processing times. |
| MCP stdio | The port explicitly refuses startup on AROS until it can safely interrupt and finish the stdin reader. The server can otherwise return after an output failure while that reader remains blocked. Closing must finish all workers before the process unloads. |
| Model downloads | The port explicitly blocks network downloads until cancellation during DNS resolution and worker shutdown have been verified. This restriction does not establish a lack of AROS networking support. |

The CPU/AUTO/GPU settings select rendering and image computation. They do not enable optional codecs or inference features that were omitted when the program was built. Model installation and network downloads are separate concerns.

## Work for later builds

1. **MCP:** compare the transports used by the earlier Craft ports and implement bounded stdin-reader shutdown. Cover handshake and tool discovery, EOF, a broken output connection, and closing while a tool is running. A successful handshake alone does not establish safe shutdown.
2. **HEIF:** enable the existing decoder and exercise representative HEIC/HEIF files, including error handling and colour conversion.
3. **Denoise:** enable CPU inference with a model supplied locally. Check model licensing, dependencies, memory use, image output and processing time. Network downloading can be addressed independently.
4. **SAM:** evaluate CPU segmentation separately, measuring peak memory and processing time with the required model.
5. **AVIF import:** select and integrate an AV1 image decoder as an upstream extension.
6. **Downloads:** verify cancellation during DNS, connection establishment and transfer, then verify that the download worker finishes before shutdown. Keep partial files separate from completed models.

These are follow-up tasks; the current release does not include them. No model is downloaded automatically.

## Source references

- [Codec feature selection](https://github.com/storytold/lightcraft/blob/23e181283cb448205d865e8cd288b56afe987986/crates/codecs/Cargo.toml)
- [CPU denoise implementation](https://github.com/storytold/lightcraft/blob/23e181283cb448205d865e8cd288b56afe987986/crates/denoise/src/runtime.rs)
- [SAM device selection](https://github.com/storytold/lightcraft/blob/23e181283cb448205d865e8cd288b56afe987986/crates/segment/src/lib.rs)
- The AROS MCP and download guards are recorded in this repository's LightCraft patch series.
