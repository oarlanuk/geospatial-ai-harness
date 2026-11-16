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
- **Job queue:** durable queue of processing tasks, shared by all users.
  One lane per worker type. See "Asynchronous jobs" below.
- **Job workers:** GDAL and Python by default. A separate QGIS worker starts
  only for tools that declare they need it. Workers pull from the queue.
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
3. Tools submit jobs to the queue, run SQL in Snowflake, or search the
   catalogue.
4. Tools return job IDs, paths, stats and layer IDs. Never pixels.
5. Writes pause at the guardrails until the user approves them.

**View path**
1. The publish tool registers a result as a new layer.
2. The agent tells the map viewer to add that layer.
3. The viewer requests tiles from the layer gateway.
4. Tile services read only the needed ranges from storage, via the cache.

## Asynchronous jobs

The app serves many users at once, and raster work can take minutes. So
processing never runs inside a chat turn.

**Rule:** a tool that does processing submits a job and returns a job ID at
once. Only quick lookups (catalogue search, location resolving, job status)
answer directly.

**Job path**
1. A tool validates the request, checks the size cap, and creates a job
   record. Writes wait for the user's approval first.
2. The job joins the queue for its worker type (`gdal` or `qgis`).
3. A free worker takes it, reports progress, and writes the result.
4. On completion the result is registered as a layer and an event is sent
   to the user's workspace. The layer appears, and the agent summarises the
   outcome if the user is still in the session.

**States:** awaiting approval, queued, running, succeeded, failed, cancelled.

**Many users, one queue**
- **Fair turns:** workers take jobs across users in rotation, so one user's
  large batch cannot starve everyone else.
- **Per-user limit:** a cap on how many of a user's jobs run at once. The
  rest wait in the queue.
- **Two lanes:** small interactive jobs do not wait behind heavy ones.
- **Backpressure:** when the queue is full, new jobs are refused with a
  clear message rather than accepted and stalled.
- **Visibility:** users see their queue position and progress. They see
  only their own jobs and results unless something is shared.

**Robustness**
- **Durable:** jobs and their state are stored, not held in memory. A
  restart loses nothing, and a user can close the browser and come back.
- **No duplicate work:** the same tool with the same inputs maps to the
  same job. Asking twice returns the existing job or its result.
- **Safe retries:** workers write to a temporary path and rename on
  success, so a retried job never leaves a half-written file. Only
  transient failures are retried, a limited number of times.
- **Lost workers:** a running job whose worker stops reporting is returned
  to the queue.
- **Cancel and timeout:** a user can cancel their own job; every job has a
  time limit.

## Trust boundary

Geo tools, data and compute, and serving all run inside the network. The
agent sees metadata and summaries only.

## Open decisions

- Where the named site features used by the location resolver are kept.
- Hosting, identity provider and scaling.
- Viewer library: MapLibre or OpenLayers.
- Catalogue stack: pgstac + stac-fastapi is the working assumption.
- Job queue technology, and the numbers: per-user limit, queue size, job
  time limit, and the threshold between the small and heavy lanes.
