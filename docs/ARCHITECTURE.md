# Architecture

Compute runs beside the data. Only tiles and summaries travel.

The visual version of this document is the "Geospatial AI harness
architecture" whiteboard. Keep the two in step.

## Parts

### 1. Workspace (web app) — `workspace/`
- **Chat and commands:** prompts and quick actions for common workflows.
- **Layer panel:** catalogue browsing and layer styles.
- **Approvals and jobs:** confirm writes, see job progress.
- **Map viewer:** 2D layers and 3D terrain. Users need only a browser.

### 2. Agent harness — `harness/`
- **Agent loop:** Claude with the Agent SDK.
- **Context:** skills, CRS rules, the data catalogue.
- **Guardrails:** permissions, approvals, audit log, job-size caps.
- **Session state:** jobs, history, loaded layers.

### 3. Geo tools (MCP servers) — `geo_tools/`
- **Raster and DEM tools:** clip, mosaic, reproject, terrain, zonal stats.
- **Vector and SQL tools:** spatial queries, pushed down to Snowflake.
- **Location resolver:** turn a place description (named site feature,
  tenement ID, distance from a feature, coordinates) into an area. It never
  guesses: ambiguous names come back as candidates for the user to choose.
- **Catalogue search:** find datasets through the STAC catalogue.
- **Publish layer:** register a result so the viewer can show it.

### 4. Data and compute — `infra/`
- **Job workers:** GDAL and Python by default. A separate QGIS worker starts
  only for tools that declare they need it.
- **Snowflake:** vectors and tables.
- **Asset catalogue:** STAC index of what data exists, where, and what it
  covers.
- **Network storage:** DEMs, COGs and other rasters. Files stay where they are.

### 5. Serving (view path) — `serving/`
- **Tile services:** raster, terrain and vector tiles, read by byte range.
- **Tile cache:** fast repeat views.
- **Layer gateway:** auth, styles, legends. The only thing the viewer talks to
  for map data.

## Flows

**Request path**
1. The user sends a request from the workspace to the agent loop.
2. The agent calls geo tools over MCP.
3. Tools run jobs on workers, SQL in Snowflake, or searches in the catalogue.
4. Tools return paths, stats and layer IDs. Never pixels.
5. Writes pause at the guardrails until the user approves them.

**View path**
1. The publish tool registers a result as a new layer.
2. The agent tells the map viewer to add that layer.
3. The viewer requests tiles from the layer gateway.
4. Tile services read only the needed ranges from storage, via the cache.

## Trust boundary

Geo tools, data and compute, and serving all run inside the network. The
agent sees metadata and summaries only.

## Open decisions

- Where the named site features used by the location resolver are kept.
- Hosting, identity provider and scaling.
- Viewer library: MapLibre or OpenLayers.
- Catalogue stack: pgstac + stac-fastapi is the working assumption.
