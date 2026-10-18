# GhostRecall examples

## sample_project/

A tiny fictional demo shop with every GhostRecall source type:

- `DECISIONS.md` - four decisions in the documented format, including
  a standing rule pair (D-001 shipping cutoff, D-002 refunds) and a
  superseded pair (D-003 held the spring sale, D-004 lifted the hold).
- `docs/shipping-notes.md` - a freeform note (plain source).
- `CHANGELOG.md` - history source.
- `src/shop.py` - code whose comments cite the decisions, so the
  combined bundle has something to pair memory with.

### Try it (once the core CLI is installed)

```bash
# Ranked memory for a task, with token costs
ghostrecall recall examples/sample_project --task "When do orders ship?"

# Combined code + memory bundle under a 2,000 token budget
ghostrecall bundle examples/sample_project \
  --task "When do orders ship and who approves a refund?" \
  --fit 2000 -o /tmp/shop-bundle

# Verify the bundle against its manifest
ghostrecall check /tmp/shop-bundle
```

What to look for in the output:

- D-003 appears only as superseded (or not at all), D-004 is the
  current spring-sale decision.
- D-001 and D-002 are pinned standing rules: they show up even for a
  task whose words do not match them, and the manifest marks them
  pinned rather than TF-IDF ranked.
- Every memory item in `manifest.json` carries provenance: source
  file, line, and date.

## DECISIONS.example.md

A blank starter in the documented `DECISIONS.md` format. Copy it to
the root of a real project and fill it in.
