# Architecture

Compute runs beside the data. Only tiles and summaries travel.

The visual version of this document is the "Geospatial AI harness
architecture" whiteboard. Keep the two in step.

## Parts

### 1. Web app — `workspace/`

Naming: "workspace" now means a user's persistent project space (see
"Workspaces" below). This part is the web app. The folder keeps its old name
until it is renamed `web/`.

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
- **Catalogue search:** find datasets through the STAC catalogue.
- **Publish layer:** register a result so the viewer can show it.

### 4. Data and compute — `infra/`
- **Job workers:** GDAL and Python by default. A separate QGIS worker starts
  only for tools that declare they need it.
- **Snowflake:** vectors and tables.
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

- Hosting, identity provider and scaling.
- Viewer library: MapLibre or OpenLayers.
- Workspace storage technology (object store or network share), quotas and
  retention.
- How agent sessions persist when the harness runs as several instances.
- Upload formats to accept first.
- Rename the `workspace/` folder to `web/`.
- Catalogue stack: pgstac + stac-fastapi is the working assumption.
