# geo_tools

MCP servers that wrap the GIS work: raster and DEM tools, vector and spatial
SQL tools, catalogue search, and publish layer.

Rules for every tool:
- Read-only unless the user approves a write.
- Returns paths, stats and layer IDs, never raster data.
- Declares its worker type: `gdal` (default) or `qgis`.
- No arbitrary code execution.

Not implemented yet.
