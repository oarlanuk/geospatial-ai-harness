# Coding guidelines

Lean on purpose. Where this document is silent, follow the Google style guide
for the language. Where the two disagree, this document wins.

- Python: [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- TypeScript: [Google TypeScript Style Guide](https://google.github.io/styleguide/tsguide.html)
- Shell: [Google Shell Style Guide](https://google.github.io/styleguide/shellguide.html)

## General (all languages)

### Explicit over compact

1. **Every conditional and loop gets a full block.** Braces always, body on
   its own lines, closing brace on its own line. No one-line `if`.
2. **No boolean shortcuts as control flow.** Do not use `&&`, `||` or `and`,
   `or` to run a statement.
3. **Prefer `if`/`else` to ternaries.** A ternary is allowed only to choose
   between two simple values on one line. Never nest them.
4. **Compare explicitly** when the meaning is not obvious: `count === 0`,
   `value is None`. Do not rely on truthiness for numbers or strings.
5. **Name the condition** when it has more than two parts. Put it in a
   well-named variable, then test the variable.

```ts
// No
if (!layer) return;
isReady && render();
const label = count ? (count > 1 ? "layers" : "layer") : "none";

// Yes
if (layer === undefined) {
  return;
}

if (isReady) {
  render();
}
```

```python
# No
if layer is None: return
result = compute() if ready else None

# Yes
if layer is None:
    return

if ready:
    result = compute()
else:
    result = None
```

### Structure

- Functions do one thing and fit on a screen. Return early on bad input.
- No magic numbers or strings. Name them as constants, with units in the
  name: `MAX_JOB_PIXELS`, `timeout_seconds`.
- Types on every public function, in every language.
- Names are full words: `elevation_raster`, not `elev_rst`.
- Comments explain why, not what. Delete commented-out code.
- No dead code, and no abstractions for needs that do not exist yet.

### Errors and logging

- Fail loudly. Never swallow an exception or return a default that hides it.
- Error messages say what failed, with which input, and what to do next.
- Use structured logs (key and value), never `print` or `console.log`.
- Never log secrets, tokens or full connection strings.

### Tests and changes

- Every tool and every bug fix comes with a test.
- Tests use small fixture data checked into the repo, never production shares.
- Small pull requests, one purpose each. Formatters and linters run in CI;
  do not argue with them by hand.

## Python (harness, geo tools, serving)

- Format and lint with `ruff`; type-check with `pyright` in strict mode.
- Google-style docstrings on public functions: summary, `Args`, `Returns`,
  `Raises`.
- Data crossing a boundary (tool inputs, API bodies, config) is a Pydantic
  model, not a `dict`.
- Use `pathlib.Path`, not string paths. Use `with` for every file, dataset
  and connection.
- No mutable default arguments. No bare `except`. No wildcard imports.
- `async` for network and I/O in services; keep CPU-heavy raster work in
  job workers, not in request handlers.
- Comprehensions are fine for a simple map or filter on one line. Anything
  with a condition and a transform, or nesting, becomes a loop.

Lint rule that enforces the block style: `E701` (no statement on the same
line as `if`, `for` or `while`).

## TypeScript and React (workspace)

- `strict` mode on. No `any`; use `unknown` and narrow it.
- `const` by default. `===` always. Named exports only.
- Function components and hooks. One component per file.
- Keep state as local as possible. Server data goes through one data layer,
  not ad hoc `fetch` calls in components.
- Map code lives behind a small wrapper module, so components never call
  the map library directly.
- In JSX, do not render with `cond && <X />`. Compute the element above the
  `return` with an `if` block, or extract a component.

Lint rules that enforce the block style: `curly: all`,
`brace-style: 1tbs` with single-line blocks off, `no-nested-ternary`,
`no-unused-expressions`.

## Geospatial code

- Never assume a CRS. Read it from the data and fail if it is missing.
- Output in the project default CRS unless the caller asks otherwise.
  Reprojection is always an explicit, logged step.
- Read rasters by window or overview. Never load a whole large raster.
- Handle nodata explicitly on every read and write.
- Write rasters as COGs, with compression and overviews.
- State units in names: `buffer_metres`, `resolution_metres`.
- Check estimated job size against the cap before starting work.

## MCP tools

- One tool, one verb: `clip_raster`, `search_catalogue`.
- Typed inputs and outputs with a description on every field. The
  descriptions are the agent's only documentation.
- Return paths, statistics and layer IDs. Never pixel data or large
  geometries.
- Read-only by default. A tool that writes says so in its name and
  description, and goes through approval.
- Declare the worker type (`gdal` or `qgis`).
- Errors returned to the agent are short and actionable.

## SQL (Snowflake and Postgres)

- Keywords in upper case, one clause per line, one column per line in long
  `SELECT` lists.
- Always use bound parameters. Never build SQL by joining strings.
- No `SELECT *`. Name the columns.
- Filter spatially and by attribute in the database. Fetch only the result.
- Read-only roles for queries. Schema changes go through migrations.

## Containers and config

- Pin base image versions. One process per container. Run as a non-root user.
- Configuration comes from environment variables, validated at start-up.
- No secrets in images, code or the repo.
- Shell scripts start with `set -euo pipefail`. Anything longer than about
  30 lines becomes Python.
