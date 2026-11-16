# Contributing

## One-time setup

```
make setup
```

This installs the tools (pinned in `uv.lock`) and the git hooks. You need
[uv](https://docs.astral.sh/uv/) installed first.

## Before every commit

```
make fix
```

Formats the code and applies safe lint fixes. Then commit. The pre-commit
hook runs the same format and lint on the files you staged, plus hygiene
checks: no files over 500 kB, no private keys, no merge-conflict markers.

If the hook changes a file, the commit stops. Look at the change, stage it,
and commit again.

## Before every pull request

```
make check
```

Verifies without changing anything: format, lint, types. It must pass before
you open a pull request. The pre-push hook runs the type check, and CI runs
`make check` on every pull request, so a failure blocks the merge.

Then confirm:

- [ ] `make check` passes locally.
- [ ] The pull request has one purpose.
- [ ] Behaviour changes have a behavioural test.
- [ ] A design change updates `docs/ARCHITECTURE.md` in the same pull request.

## Rules

- Never skip the hooks with `--no-verify`.
- Never silence a rule inline to get a commit through. Fix the code, or
  change the rule in `pyproject.toml` in its own pull request with a reason.
- The formatter decides layout. Do not hand-format against it.

## What is checked

| Check | Tool | When |
| --- | --- | --- |
| Formatting | `ruff format` | commit, CI |
| Lint, import order, docstrings, annotations | `ruff check` | commit, CI |
| Types, strict mode | `pyright` | push, CI |
| Large files, private keys, whitespace | `pre-commit-hooks` | commit |

TypeScript checks (ESLint, Prettier, `tsc`) join `make check` when the web
app is scaffolded.
