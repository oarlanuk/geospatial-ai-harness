# Architecture

Compute runs beside the data. Only tiles and summaries travel.

The visual version of this document is the "Geospatial AI harness
architecture" whiteboard. Keep the two in step.

## Parts

### 1. Web app — `web/`

Naming: "workspace" means a user's persistent project space (see
"Workspaces" below), not this part.

- **Chat and commands:** prompts and quick actions for common workflows.
- **Layer panel:** catalogue browsing and layer styles.
- **Approvals and jobs:** confirm writes, see job progress.
- **Map viewer:** 2D layers and 3D terrain. Users need only a browser.

### 2. Agent harness — `harness/`
- **Agent loop:** Claude with the Agent SDK.
- **Context:** skills, CRS rules, the data catalogue.
- **Guardrails:** permissions, approvals, audit log, job-size caps.
- **Session state:** jobs, history, loaded layers.
- **Workspace service:** owns workspaces, their sessions, artifacts,
  uploads and sharing.
- **Skill registry:** stores reusable skills and supplies the right ones to
  each session.

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
- **Postgres and PostGIS:** one shared database for the catalogue, job
  queue and job records, workspaces and sessions, the audit log, and
  published vector results.
- **Asset catalogue:** STAC index of what data exists, where, and what it
  covers.
- **Network storage:** DEMs, COGs and other rasters. Files stay where they are.
- **Workspace storage:** a separate, writable area for artifacts and
  uploads, one folder per workspace. Source data is never written to.

### 5. Serving (view path) — `serving/`
- **Tile services:** raster, terrain and vector tiles, read by byte range.
- **Tile cache:** fast repeat views.
- **Layer gateway:** auth, styles, legends. The only thing the viewer talks to
  for map data.

## Flows

**Request path**
1. The user sends a request from the web app to the agent loop.
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
   to the user's web app. The layer appears, and the agent summarises the
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

## Workspaces

A workspace is a user's persistent project space. Closing the browser loses
nothing: the user returns to the same conversations, map and files.

**A workspace holds**
- **Sessions:** conversations with the agent. A workspace has many, and any
  can be resumed.
- **Map state:** loaded layers, their order and styles, and the view.
- **Artifacts:** files the harness produced (rasters, vectors, tables,
  reports) and files the user uploaded.
- **Job history:** every job, linked to the artifacts it made.
- **Enabled skills:** which skills are switched on here.

**Where things live**
- Metadata (workspaces, sessions, map state, artifact records, sharing) is
  in the database.
- Files are in workspace storage, inside the network.
- Every spatial artifact is also registered in the catalogue, scoped to its
  workspace, so discovery and tile serving treat it like any other dataset.

**Artifacts**
- **Lineage is mandatory.** A produced artifact records its sources, tool,
  inputs, job, and skill version if one was used. It can be regenerated
  from that record.
- **Sources are referenced, not copied.** A workspace points at source
  datasets and stores only what is new.
- **The agent sees summaries.** It gets a list of the workspace's artifacts
  with their metadata, never their contents.

**Uploads**
- Files go from the browser straight to workspace storage. They never pass
  through the agent or leave the network.
- Each upload runs an ingest job: check the type against an allow-list,
  check the size cap, read the CRS (ask the user if it is missing), convert
  rasters to COG, then register the artifact.
- Uploads are untrusted data. They are validated and read, never executed.

**Ownership and sharing**
- Private to the owner by default.
- The owner can share with people or groups, as viewer or editor.
- Jobs and artifacts follow the workspace's permissions.

**Lifecycle**
- Each workspace has a storage quota.
- Deleting an artifact or a workspace needs approval and is logged.

## Skills

A skill is a reusable, named way of doing a task: instructions for the
agent, the tools to use, and the parameters to ask for. Examples: "monthly
stockpile volumes", "standard pit crop".

**Skills are instructions, not code.** A skill composes existing geo tools.
It cannot carry scripts or anything executable, and it cannot widen
permissions: writes still need approval, and size caps still apply. A new
capability means a new reviewed tool, not a skill. This keeps the "no
arbitrary code" rule intact.

**Scopes**
- **Built-in:** shipped in this repo and reviewed like code.
- **Organisation:** published for everyone by an administrator.
- **Workspace:** created by a user, often by saving a session that went
  well ("save this as a skill"). Usable in that workspace and shareable
  with it.

**How they work**
- A skill is a `SKILL.md` file: a name and description saying when to use
  it, then the steps.
- Only names and descriptions are loaded into a session. The full skill is
  read when it is used, so many skills cost little.
- The skill registry stores skills and writes the enabled ones into the
  session's skills folder before the session starts.
- Skills are versioned. An artifact made with a skill records the version.
- User-written skills are untrusted text. They are checked on save (no
  executable content) and never override the design rules.

## Open decisions

- Where the named site features used by the location resolver are kept.
- Hosting, identity provider and scaling.
- Viewer library: MapLibre or OpenLayers.
- Workspace storage technology (object store or network share), quotas and
  retention.
- How agent sessions persist when the harness runs as several instances.
- Upload formats to accept first.
- Catalogue stack: pgstac + stac-fastapi is the working assumption.
- Job queue numbers: per-user limit, queue size, job time limit, and the
  threshold between the small and heavy lanes. The queue technology is
  tracked in `TECH_STACK.md`.
