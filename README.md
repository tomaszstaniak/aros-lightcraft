# LightCraft for AROS

Photo library and non-destructive RAW editor for AROS x86_64 ABIv11 and ABIv1, based on LightCraft 0.13.0. The interface and image processing use the CPU.

## Install

Download the program ZIP from [Releases](https://github.com/tomaszstaniak/aros-lightcraft/releases), then unpack it to a writable drawer. Double-click LightCraft in Workbench. From Shell, set `Stack 16777216` and run `LightCraft [image]`.

With arospkg 0.6 or later:

```
apkg update
apkg install lightcraft
apkg run lightcraft
```

Edits and settings are stored in `LightCraftData` inside the program drawer. Keep this drawer when upgrading. Export writes a separate image and protects the original. `lightcraft-cli --help` lists batch commands.

## Rendering

| Workbench ToolType | Shell argument | Values |
|---|---|---|
| GUI_RENDERER | --gui-renderer | CPU, AUTO, GPU |
| IMAGE_COMPUTE | --image-compute | CPU, AUTO, GPU |

Both settings default to CPU, including in the supplied icon. Values ignore letter case. Explicit arguments take priority over Workbench ToolTypes, followed by the defaults. Shell startup does not read the icon. Unknown values stop startup.

CPU uses only the CPU and does not probe or initialize a GPU. AUTO tries an available GPU backend and otherwise uses the CPU, recording the reason. GPU requires a backend and reports an error if it is unavailable.

This build includes CPU backends only. AUTO therefore selects CPU with a logged reason; GPU stops startup with an error. GUI rendering and image computation are independent settings. Legacy GPU environment variables cannot override an explicit CPU choice.

Example:

```
LightCraft --gui-renderer CPU --image-compute CPU "Work:Photos/My Photo.png"
```

Requested and selected modes are recorded in `LightCraft.log` inside the program drawer. `LIGHTCRAFT_LOG_FILE` selects another log file. Workbench startup errors also appear in a requester.

## Supported files and limitations

PNG, JPEG, TIFF, WebP and JPEG XL import and export are included, along with RAW development and AVIF export. RAW support varies by camera. LightCraft uses its own codec libraries.

The limitations have separate causes:

- **AVIF import:** the pinned upstream has no decoder. AVIF export works.
- **HEIF/HEIC:** the optional upstream Rust decoder is not enabled in this build; AROS compatibility remains to be established.
- **Neural denoise and SAM:** optional inference features are not enabled. Upstream provides CPU execution; dependencies, local models, memory and processing time need further work.
- **MCP stdio:** the port blocks it until the stdin reader can be interrupted and shut down safely, including after a broken output connection.
- **Model downloads:** the port blocks them pending verification of DNS cancellation and worker shutdown. This is a lifecycle restriction, not a networking capability claim.

See [feature status and work for later builds](docs/features.md) for the individual causes and remaining tasks. No model is downloaded automatically.

Choose the archive matching the system ABI:

| ABI | Release | Runtime |
|---|---|---|
| v11 | 0.13.0-aros1 | Existing v11 runtime |
| v1 | 0.13.0-aros2 | Experimental coherent runtime: fd.library 51, posixc.library 0.41 and matching stdc.library and AROSTCP |

The v1 archive requires the runtime described in [the SDK recipe](docs/sdk-v1.md); current stock mainline does not contain all its prerequisites. The application archive does not replace system libraries. Shell launches need a 16 MiB stack; the Workbench icon supplies it. Large images and procedural demo images can take time to process.

Paths accept AmigaDOS volumes and assigns. UTF-8 filenames are supported; native keyboard and clipboard conversion is limited to Latin-1. Export to the standard system disk and RAM: is supported. Writing directly to the root of some other volumes may return a system error; select a drawer on the destination volume.

## Source

- [Build instructions](docs/development.md)
- [Mainline v1 build profile and requirements](docs/mainline-v1.md)
- [Coherent v1 SDK and runtime recipe](docs/sdk-v1.md)
- [Patch workflow](docs/patching.md)
- [Generated files](docs/cleanup.md)

Upstream: [storytold/lightcraft](https://github.com/storytold/lightcraft), version 0.13.0. LightCraft is licensed under MIT OR Apache-2.0. The program archive contains the dependency licenses and asset notices.
