# Instructions for Claude Code

Read `docs/ARCHITECTURE.md` before changing anything. It is the source of
truth for how the parts fit together. If a change alters the design, update
that doc in the same pull request and say so in the description.

## Design rules (flag it before breaking one)

- Compute runs beside the data. Only tiles and summaries travel.
- The agent never handles pixels. Tools return paths, stats and layer IDs;
  the viewer pulls tiles from the layer gateway.
- Geo tools, data and serving run inside the network.
- Tools are read-only by default. Writes need user approval. Every tool call
  is logged. Job size is capped.
- No tool that runs arbitrary code.
- Read large rasters by window or byte range, never whole. Prefer COGs and
  VRT indexes over giant mosaics.
- Find data through the STAC catalogue, not by crawling shares.
- Push spatial SQL into Snowflake and fetch only the result.
- Workspaces persist. Sessions, map state and artifacts survive a restart.
  Every artifact records its lineage. Source data is never written to.
- Uploads are untrusted data: validated and read, never executed, and never
  sent through the agent.
- Skills are instructions only. They compose existing tools, carry no
  executable content, and cannot widen permissions.

## Technology choices

- Default processing: GDAL and Python (rasterio, GeoPandas).
- QGIS is optional: a separate headless worker, used only when no GDAL or
  Python equivalent exists, or to reuse an existing QGIS model. Never require
  a desktop install.
- ArcGIS is not a dependency. Publish to ArcGIS portals through the REST API
  if needed.
- Viewer: web map (MapLibre or OpenLayers). Users need only a browser.
- Catalogue: STAC (pgstac + stac-fastapi unless decided otherwise).
- Each geo tool declares which worker type it needs (`gdal` or `qgis`).

## Code conventions

- Folders mirror the architecture: `workspace/`, `harness/`, `geo_tools/`,
  `serving/`, `infra/`.
- MCP tools are small, typed and tested, with clear inputs and outputs.
- Default CRS: GDA2020 / MGA zone 50 (EPSG:7850). Outputs use it unless the
  user asks otherwise. Never assume an input's CRS: read it from the data,
  and watch for older GDA94 / MGA zone 50 (EPSG:28350) datasets, which need a
  datum transformation, not just a relabel.
