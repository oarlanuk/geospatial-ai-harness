# Geospatial AI harness

A web app where users chat with a Claude agent that runs GIS processing and
shows the results as map layers (vectors, rasters, DEMs, 3D terrain).

**Status:** skeleton only. No component is implemented yet.

## Layout

| Folder | Part of the architecture |
| --- | --- |
| `workspace/` | Web app: chat, layer panel, approvals, map viewer |
| `harness/` | Agent loop, context, guardrails, session state |
| `geo_tools/` | MCP servers: raster/DEM, vector/SQL, catalogue search, publish |
| `serving/` | Tile services, tile cache, layer gateway |
| `infra/` | Worker images, deployment, STAC catalogue setup |
| `docs/` | Architecture and decisions |

Start with [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). Rules for AI coding
agents are in [CLAUDE.md](CLAUDE.md).

## The one rule

Compute runs beside the data. Only tiles and summaries travel.
