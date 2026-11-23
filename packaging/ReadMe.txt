LightCraft @VERSION@ for AROS
===========================

LightCraft is a photo library and raw developer. It keeps a catalogue of
your photos with ratings, flags, keywords, albums and searches, develops
JPEG, PNG, TIFF, WebP, JPEG XL, PSD and camera raw files without changing
the originals, and exports the results. This is its AROS port, based on
LightCraft @UPSTREAM_VERSION@.

This package is for: @SYSTEM@.
It does not run on other AROS systems; use the package made for yours.

The drawer holds two programs:

  LightCraft       the library and developer
  lightcraft-cli   the command-line program: develops one file and exports
                   it, runs library and editing commands, and serves an MCP
                   automation interface over standard input and output

Installation
------------

Unpack the archive anywhere writable, for example to Work:. It creates the
drawer LightCraft and its icon. Both programs use only libraries that come
with AROS; nothing in the system is replaced or added.

To upgrade, unpack the new version to a new place (not over the old drawer),
then move the drawer LightCraftData from the old LightCraft drawer into the
new one to keep your settings and your library.

Starting
--------

Workbench: double-click LightCraft. The program takes the stack it needs
itself; it also works from a Shell with the default stack.

Shell:

  LightCraft [--gui-renderer CPU|AUTO|GPU] [--library drawer] [file or drawer ...]
  LightCraft --memory

At the first start LightCraft makes a library in LightCraftData/Library
with a few generated demo photos; --no-demo starts it empty. Files and
drawers named on the command line are imported into the library. --library
opens another library drawer, or makes a new one there. --memory starts a
session in memory with the demo photos that writes nothing. Import, Open
Library and the other file choices use the standard file requester. To
close LightCraft, use the window's close gadget.

  lightcraft-cli render photo.dng -o photo.jpg --set light.exposure=0.5 --size 1600
  lightcraft-cli run --library Work:Photos/Library library.state
  lightcraft-cli --help

render writes the format given by the output name's extension (jpg, png,
tif, webp, avif, jxl, psd, dng). In the AROS Shell an asterisk inside quotes
starts an escape, so write ** for a * in a command's text.

lightcraft-cli mcp runs an MCP server on standard input and output for a
client that starts it as a child process. It works on its own session or
library, not on the one open in the LightCraft window.

Settings and log
----------------

Settings, the default library and the log file LightCraft.log are kept in
the drawer LightCraftData inside the LightCraft drawer; it is created at
the first start. The variable LIGHTCRAFT_CONFIG_DIR names another drawer
instead, LIGHTCRAFT_LIBRARY another library, LIGHTCRAFT_LOG another log
file.

Interface renderer
------------------

The ToolType GUI_RENDERER in the program's icon, or the Shell argument
--gui-renderer, chooses how the interface is drawn. A Shell argument takes
priority; the icon is not read when the program is started from the Shell.
Values ignore letter case.

  AUTO  OpenGL if it opens and is not Mesa's software renderer, otherwise
        CPU; the reason is written to LightCraft.log (default)
  CPU   the processor draws the interface; OpenGL is not opened
  GPU   OpenGL (the software renderer too), or the program stops with an
        error

Developing and exporting photos always run on the processor.

Known limitations
-----------------

@LIMITATIONS@

Licences
--------

LightCraft is available under the MIT license or the Apache License 2.0, at
your option. The texts, the licences of the fonts built into the programs,
and the licences of everything linked into the programs are in the Licenses
drawer. BUILD.txt identifies this build.

LightCraft: https://github.com/storytold/lightcraft
AROS port: https://github.com/tomaszstaniak/aros-lightcraft
