# Tech stack

What each part of [the architecture](ARCHITECTURE.md) is built with, and why.

**Status key**
- **Decided:** agreed, build on it.
- **Proposed:** a recommendation awaiting confirmation. Do not treat as final.
- **Open:** depends on something not yet known.

## Principles

- **Python everywhere except the browser.** The GIS libraries are Python, so
  the harness, tools and serving use it too. TypeScript is for the web app only.
- **One Postgres.** Catalogue, published vector results, sessions, audit log
  and job queue share one Postgres/PostGIS instance in separate schemas. Split
  it later if load requires.
- **Open source and open standards first** (STAC, COG, OGC tiles, MCP).
- **Everything in containers**, so each part runs the same in dev and inside
  the network.

## 1. Workspace (web app)

| Concern | Choice | Status | Why |
| --- | --- | --- | --- |
| Language and build | TypeScript, React, Vite | Proposed | Largest ecosystem for map-heavy apps; no server rendering needed. |
| Map viewer | MapLibre GL JS | Proposed | Open source, GPU rendering, vector tiles, and 3D terrain from `raster-dem` tiles. |
| Chat streaming | Server-sent events from the harness API | Proposed | Simple one-way stream for agent output; plain HTTP for user actions. |

Trade-off: MapLibre draws in Web Mercator, so the tile services reproject
GDA2020 / MGA zone 50 data on the fly for display. Analysis still runs in the
native CRS. OpenLayers is the alternative if the map itself must display in
MGA coordinates or lean on WMS.

## 2. Agent harness

| Concern | Choice | Status | Why |
| --- | --- | --- | --- |
| Agent loop | Claude Agent SDK (Python) | Decided | Ready-made loop, sessions, permissions and hooks. |
| API | FastAPI | Proposed | Async, typed, and the same framework as the serving components. |
| Session state, audit log | Postgres | Proposed | Already required for the catalogue. |
| Model | Set in config, not hard-coded | Proposed | Models change; the harness should not care. |

Constraint: the Agent SDK ships with Claude Code's built-in tools, which
include file editing and shell commands. The harness must turn those off and
allow only the geo MCP tools, or the "no arbitrary code" rule is broken.
Verify the exact options in the SDK docs when building this.

## 3. Geo tools (MCP servers)

| Concern | Choice | Status | Why |
| --- | --- | --- | --- |
| Server framework | MCP Python SDK (FastMCP) | Proposed | Official SDK; typed tools from function signatures. |
| Transport | Streamable HTTP | Proposed | Tools run as network services beside the data, not as local subprocesses. |
| Inputs and outputs | Pydantic models | Proposed | Validation and clear schemas for the agent. |
| Raster processing | GDAL, rasterio | Decided | Windowed reads; covers clip, mosaic, reproject, terrain, zonal stats. |
| Vector processing | GeoPandas, Shapely | Decided | Standard Python vector stack. |
| Snowflake access | `snowflake-connector-python`, read-only role | Proposed | Push spatial SQL down; fetch only results. |
| QGIS algorithms | Separate headless worker image | Decided | Only when no GDAL or Python equivalent exists. |

## 4. Data and compute

| Concern | Choice | Status | Why |
| --- | --- | --- | --- |
| Catalogue | pgstac + stac-fastapi-pgstac | Proposed | STAC API on Postgres; widely used together. |
| Catalogue ingest | rio-stac, pystac | Proposed | Build STAC items by scanning existing rasters. |
| Raster outputs | COGs written to a results area on network storage | Proposed | Tile services can read them with no extra step. |
| Vector outputs | PostGIS tables (small results: GeoJSON) | Proposed | Lets the vector tile server publish results directly. |
| Job queue | DBOS Transact (Python), without Conductor | Proposed | Postgres only; per-user limits, priority, deduplication and timeouts are queue options; durable multi-step jobs. Conditional on the spike below. |
| Source data | Snowflake, network storage | Decided | Existing systems; data stays where it is. |

### Job queue: conditions and fallbacks

The queue sits behind a small interface in the harness (submit, cancel,
status), so the library can be swapped without touching tools or the web app.

**Spike before this becomes Decided.** Both must pass on a real DEM crop:
1. Cancel a running crop and confirm the worker stops promptly and leaves no
   partial file.
2. Kill a worker mid-job and confirm the job is recovered and completes.

**Known gaps**
- With several workers and no Conductor, recovery of a dead worker's jobs
  must be triggered by us (a small watchdog). Self-hosted Conductor does it
  automatically but needs a paid licence for production.
- No operator dashboard without Conductor. Our own jobs panel covers users.
- Strict turn-taking across users, beyond per-user limits, needs the
  two-queue pattern from the DBOS docs.

**Fallbacks, in order**
1. DBOS with a Conductor licence, if the watchdog proves fiddly.
2. Temporal (self-hosted), if the feature gaps bite. It needs its own
   service cluster.
3. Procrastinate, if DBOS itself is unsuitable. Postgres only, but per-user
   limits and multi-step jobs would be ours to build.

Celery with Redis was ruled out: long jobs risk duplicate delivery, and it
has no per-user concurrency control.

## 5. Serving (view path)

| Concern | Choice | Status | Why |
| --- | --- | --- | --- |
| Raster and terrain tiles | TiTiler | Proposed | Dynamic tiles straight from COGs and STAC items; no pre-tiling. |
| Mosaics from the catalogue | titiler-pgstac | Proposed | Tiles many DEM tiles as one layer via a STAC search. |
| Vector tiles | Martin | Proposed | Serves PostGIS tables as vector tiles for MapLibre. |
| Tile cache | nginx proxy cache | Proposed | TiTiler already sends cache headers; a proxy cache is enough to start. |
| Layer gateway | FastAPI service behind nginx | Proposed | One place for auth, the layer registry, styles and legends. |

To verify in a spike: TiTiler producing terrain tiles in the encoding
MapLibre's `raster-dem` source expects, from a real 1 m DEM.

## Cross-cutting

| Concern | Choice | Status | Why |
| --- | --- | --- | --- |
| Sign-in | OpenID Connect against the organisation's identity provider | Open | Depends on which provider is in use. |
| Packaging | Docker images; Docker Compose for local dev | Proposed | Same images everywhere. |
| Production hosting | Kubernetes or Compose on a VM | Open | Depends on what the network already runs. |
| Python tooling | uv, ruff, pyright, pytest | Proposed | Fast, typed, tested. |
| CI | GitHub Actions | Proposed | The repo is on GitHub. |
| Observability | Structured logs plus OpenTelemetry traces | Proposed | One trace per user request across agent, tools and jobs. |

## Effect on the architecture

Adopting this adds one component the architecture does not yet show: a
Postgres/PostGIS store in "Data and compute" holding the catalogue, published
vector results, sessions, audit log and job queue. Update `ARCHITECTURE.md`
and the whiteboard when this is confirmed.
