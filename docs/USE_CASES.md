# Use cases

The north star for this app, in a mining context. Every feature should serve
one of these. If it serves none, question why it is being built.

Build order is top to bottom. Start small: the first release is use cases 1
and 2 only.

## How to read each use case

- **Asks:** things a user would actually type.
- **The app:** what happens, in order.
- **Needs:** the tools and data required.
- **Done when:** observable behaviour. These become the behavioural tests.

## First release

### 1. Discover data

**Asks**
- "What elevation data do we have over the north waste dump?"
- "What is the latest survey of pit 3, and what did it cover?"
- "Show every drone survey from the last 30 days."

**The app**
1. Resolves the place named in the ask to an area (see "Location
   descriptions" below).
2. Searches the catalogue for datasets that intersect it, filtered by type
   and date.
3. Shows the footprints on the map and a short list: name, date, resolution,
   CRS, source.

**Needs:** location resolver, catalogue search, map viewer. No pixels move,
and nothing is written.

**Done when**
- A named place returns the datasets that cover it, newest first.
- An area with no data says so plainly and shows the nearest coverage.
- Every result states its date, resolution and CRS.
- A dataset on the old GDA94 datum is labelled as such.

### 2. Crop by location description

**Asks**
- "Crop the latest DEM to the north waste dump."
- "Give me the March survey within 500 m of the ROM pad."
- "Clip the lidar DEM to tenement M 12/345."
- "Crop to this box", after drawing on the map.

**The app**
1. Resolves the location to an area and outlines it on the map.
2. Finds the source dataset (use case 1), or uses the one the user named.
3. States what it will do: source, area, output size estimate, output CRS.
4. Waits for the user to approve, because a crop writes a new file.
5. Submits the crop as a job and says so at once, with its place in the
   queue. The user can keep chatting or start other work.
6. A worker runs the crop, reading only the windows it needs, and reports
   progress.
7. Writes a COG to the workspace, registers it in the catalogue with its
   lineage, and adds it to the map when it finishes.

**Needs:** location resolver, catalogue search, raster clip, publish layer,
approvals, the job queue, a job worker (GDAL only), a workspace.

**Done when**
- The cropped layer appears on the map and matches the outlined area.
- The output is a COG in the default CRS with nodata preserved.
- The result records its source dataset, area and date.
- An area that is partly outside the data is cropped to the overlap, and the
  user is told how much was missing.
- An area entirely outside the data produces no file and a clear message.
- A crop over the job size cap is refused before any work starts.
- Nothing is written unless the user approves.
- The chat stays usable while the crop runs, and progress is visible.
- Closing the browser does not stop the job; the layer is in the
  workspace on return.
- Asking for the same crop twice does not run it twice.
- A cancelled crop stops and leaves no partial file.
- With several users cropping at once, each job finishes and no user's
  jobs are starved by another's.

### Location descriptions

Both use cases depend on turning words into an area. Supported forms:

| Form | Example |
| --- | --- |
| Named site feature | "north waste dump", "pit 3", "ROM pad" |
| Tenement or lease ID | "M 12/345" |
| Distance from a feature | "within 500 m of the ROM pad" |
| Coordinates | MGA easting and northing, or latitude and longitude |
| Drawn on the map | a box or polygon |
| Current map view | "what I'm looking at" |

Rules:
- **Never guess.** If a name matches several features, show the candidates
  on the map and ask. If it matches none, say so and suggest the closest
  names.
- **Always show the resolved area** on the map before acting on it.
- **Coordinates state their CRS.** If the user gives bare numbers, infer
  only when unambiguous, and say which CRS was assumed.
- **Buffers are in metres**, computed in the default projected CRS.

## Next

### 3. Terrain products for an area
"Slope, hillshade and 1 m contours for pit 3." A crop plus derived layers,
shown in 3D. Reuses everything from use case 2.

### 4. Stockpile and pit volumes
"Volume of each stockpile from Friday's survey." "How much did we move in
pit 3 this month?" Differences two surveys and reports volumes, compared
with production records in Snowflake. Every figure carries its survey date,
resolution and method. Tonnes require a bulk density supplied by the site.

### 5. Design versus as-built
Compares a surveyed surface with the design for a pit, dump or haul road and
maps where it is over or under. Depends on design surfaces being exportable
from the mine planning package in a readable format.

### 6. Haul road gradients
Flags road segments steeper than the site limit, from road centrelines and
a DEM.

## Later

- **Disturbance and rehabilitation reporting:** cleared area per tenement
  against approved limits, and rehabilitation progress year on year.
- **Drill pad and access screening:** candidate locations by slope, buffers
  and distance to tracks.
- **Pit drainage and ponding:** catchments and flow paths. Likely needs the
  optional QGIS worker.
- **Tailings and wall monitoring:** freeboard, crest heights, settlement
  between surveys. Decision support only; it never replaces engineering
  sign-off.

## Not in scope

- Certified survey outputs. The app reports estimates with their provenance.
- Editing source data. Sources are read-only; results are new files.
- Mine planning or scheduling.

## Open questions

- **Where do named site features live?** The location resolver needs an
  authoritative table of pits, dumps, pads and tenements with geometries.
  This could be a Snowflake table or a maintained vector file.
- **Is a local mine grid in use?** If so, grid transformation becomes a
  required tool for coordinates and outputs.
- **Which survey types come first?** Drone photogrammetry, lidar, or both.
