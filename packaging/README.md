# LightCraft for AROS

Photo library and non-destructive RAW editor for AROS x86_64 ABIv11, based on LightCraft 0.13.0. The interface and image processing use the CPU.

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

PNG, JPEG, TIFF, WebP and JPEG XL import and export are included, along with RAW development and AVIF export. RAW support varies by camera. AVIF import, HEIF, neural denoise and SAM are unavailable in this build. MCP stdio and network model downloads are disabled. No models are downloaded at startup.

This release is for x86_64 ABIv11. It does not run on mainline ABIv1. Shell launches need a 16 MiB stack; the Workbench icon supplies it. Large images and procedural demo images can take time to process.

Paths accept AmigaDOS volumes and assigns. UTF-8 filenames are supported; native keyboard and clipboard conversion is limited to Latin-1. Export to the standard system disk and RAM: is supported. Writing directly to the root of some other volumes may return a system error; select a drawer on the destination volume.

Upstream: https://github.com/storytold/lightcraft (MIT OR Apache-2.0).
