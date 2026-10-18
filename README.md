# GhostRecall

**Give your agent the project's memory, sliced like its code.**

GhostSlice gives an agent the code, sliced to what a task needs. It
says almost nothing about *why* the code is that way: decisions made
last month, routes already tried and rejected, standing rules that
live in a founder's head. GhostRecall slices that project memory -
decisions, notes, changelogs, git history - with the same discipline:
token costs up front, modes per item, provenance on everything, and a
manifest you can verify.

By Ghost Developer Studio. Working name (PLAN.md). Design target:
zero dependencies, Python standard library only, local-first: no
network, no embeddings, no telemetry, your project memory never
leaves the machine.

Position in the Ghost stack: GhostSlice governs what an agent reads
about the *code*, GhostRecall governs what it reads about the
*project*, GhostVerify checks the combined bundle was enough, Agent
Seatbelt governs what an agent *does*.

## What it reads (project-local only)

- `DECISIONS.md` in the documented format below (parsed into
  individual decision records)
- Markdown / text notes, ADRs, `docs/` trees, `CHANGELOG.md`
- Build / audit / roadmap reports the project itself saved
- Local git history (commit messages; local git only, no hosting API)

Boundary rule, not a setting: GhostRecall only reads inside the
project root you point it at. It never imports an assistant's private
memory, chat transcripts outside the project, or email. If a source
is outside the project, it is not a source.

## The DECISIONS.md format

```markdown
## D-001 (2026-01-15)
Decision: The demo shop ships orders every weekday at 4pm.
Reason: The carrier pickup is scheduled for 4:30pm.
Supersedes: none
Status: current
Tags: rule, shipping
```

- Tag a decision `rule` and it becomes a standing rule: pinned into
  bundles for its scope even when ranking would have skipped it, and
  marked pinned in the manifest (never disguised as a ranked hit).
- A newer decision names what it replaces in `Supersedes:`; the old
  one is then shown as superseded or excluded, never silently served
  as current. Contradictions inside one bundle are flagged as
  conflicts, not quietly resolved.
- Every record carries provenance: source file, line, date. A
  decision with no provenance is not exported.

Freeform notes still work as plain sources; they just do not get
per-decision structure.

## Modes (per memory item)

| Mode | What is kept |
|---|---|
| `full` | Whole note / decision with reason |
| `decision-only` | Decision line + date only, reason stripped (cheap default for settled rules) |
| `headings` | Headings + first paragraph under each (same treatment as GhostSlice Markdown) |
| `recent` | Last N decisions / entries for a file or topic, N from the profile |
| `exclude` | Kept out, and recorded as excluded in the manifest so the absence is auditable |

## Usage

```bash
# Ranked, task-focused memory with token costs
ghostrecall recall <project> --task "How does local storage work?"

# Show what was NOT selected, and why (misses stay visible)
ghostrecall explain <project> --task "How does local storage work?"

# Combined code + memory bundle under one token budget.
# Code comes from GhostSlice; memory downgrades to decision-only
# before anything is dropped. The default budget split is
# 80% code / 20% memory - a default, not a finding.
ghostrecall bundle <project> --task "..." --fit 20000 -o <bundle>

# Verify a bundle against its merged manifest
ghostrecall check <bundle>
```

A combined bundle contains a merged `PROMPT.md` and one merged
`manifest.json`: per item, source type (`code` / `decision` / `note`
/ `commit`), mode, original tokens, sliced tokens, sha256, and - for
memory items - provenance and status. A memory-only export lands in
`.ghost_memory/` with the same manifest discipline.

## Profile

GhostRecall extends the project's existing `.ghostslice.json` with a
`recall` section (no second config file to drift). Unknown keys in
that section fail loudly, the same rule as GhostSlice profiles.

## Secrets guard

Every memory source is scanned with the GhostSlice secrets guard
before export. Memory files are *more* likely than code to contain
keys and private notes, so a finding blocks that item by default.
Findings are reported as path + line + type only - the value is
never printed, logged, or exported.

## MCP

Same stdio pattern as the GhostSlice MCP server, capped payloads:

- `recall_search` - ranked memory items for a task
- `recall_bundle` - build a combined bundle
- `recall_explain` - why an item was included, pinned, or left out

## Honest limits

- Selection is TF-IDF keyword ranking (the method proven in
  `ghostslice task`), not semantic search. It will miss paraphrases;
  `explain` exists so a miss is visible instead of silent.
- Memory goes stale in a way code does not. Dates, superseded
  handling, and provenance are core features for that reason.
- Extractive only: GhostRecall never summarises with a model and
  never writes decisions for you. A human (or an agent acting under
  Agent Seatbelt approval) writes `DECISIONS.md`.
- Token counts are estimates from the GhostSlice estimator; costs
  come from the same local, dated price table and are labelled
  estimates.

## Examples and tests

- `examples/sample_project/` - a tiny project with rules, notes, a
  changelog, and a superseded decision pair. See `examples/README.md`.
- `tests/` - pytest suite against the CLI and bundle formats,
  including the PLAN.md verification bar: provenance completeness,
  superseded decisions never served as current, and a planted-secret
  note fixture that must be blocked and redacted everywhere.

## Status

v0.1 in build (Oct 2026). No public release, no PyPI publish, and no
announcement - those are separate gates, same as GhostSlice.
Pricing is not decided: the design target is an MIT core CLI in the
GhostSlice / Agent Seatbelt / Ghost Hands pattern.
