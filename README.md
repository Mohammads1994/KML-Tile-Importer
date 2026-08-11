# KML Tile Importer v0.1

A Blender add-on for importing geographically positioned COLLADA (`.dae`) tiles described by KML, with tile selection and local East-North-Up placement.

## v0.1 scope

- Select a master KML file.
- Discover first-level tile KMLs through KML `NetworkLink` references.
- Select individual tiles by ID.
- Select the highest available LOD for each selected tile.
- Import the referenced DAE using Blender's COLLADA importer when available.
- Keep each imported tile in its own Blender collection.
- Preserve geographic position using a local tangent-plane approximation:
  - X = East
  - Y = North
  - Z = Up
- Keep the KML latitude/longitude/altitude and LOD information as Blender custom properties.
- Do not merge tiles or LODs.

## Important v0.1 assumption

The supplied ContextCapture sample uses `Z_UP`, has no KML `<Orientation>`, and has locally centered DAE geometry. v0.1 therefore treats the DAE local axes as East-North-Up and applies the KML model location relative to a project origin. This should be validated against a known feature before relying on the orientation for survey-grade work.

## Blender compatibility

v0.1 targets Blender 4.4's native COLLADA importer. The code isolates DAE importing in `addon/dae/importer.py` so a Blender 5.x backend (for example AssetKit) can be added without rewriting the KML/geographic logic.

## Install

1. In Blender: `Edit > Preferences > Add-ons > Install...`
2. Select `kml_tile_importer_v0_1.zip`.
3. Enable **KML Tile Importer**.
4. Open the **Scene Properties** tab and use **KML Tile Importer**.

## Use

1. Choose the master KML, e.g. `NajafCitySelected_KML.kml`.
2. Click **Discover Tiles**.
3. Select one or more tile IDs.
4. Choose the project origin. By default the first imported tile is used.
5. Click **Import Selected Tiles**.

The importer expects the master KML and its referenced tile folders/files to remain in their original relative paths.

## Git

This directory is a Git repository. The initial commit is tagged `v0.1.0`.
