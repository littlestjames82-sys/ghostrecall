"""GhostRecall CLI: scan / recall / explain / bundle / check / mcp."""
from __future__ import annotations
import argparse, json, sys

from . import __version__
from .bundle import build_bundle, check_bundle
from .dashboard import render_panel
from .profile import load_profile
from .recall import explain, select
from .sources import assert_project_root, collect_items
from .tokens import estimate

def _items(project):
    root = assert_project_root(project)
    profile = load_profile(root)
    items = collect_items(root, include_git=bool(profile.get("include_git", True)),
                          git_limit=int(profile.get("git_limit", 200)))
    return root, profile, items

def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="ghostrecall",
                                description="Project memory slicer paired with GhostSlice (estimates labelled, local only)")
    p.add_argument("--version", action="version", version=f"ghostrecall {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("scan", help="list project memory items by estimated token cost")
    sp.add_argument("project"); sp.add_argument("--json", action="store_true")

    sp = sub.add_parser("recall", help="TF-IDF task-focused recall")
    sp.add_argument("project"); sp.add_argument("--task", required=True)
    sp.add_argument("--explain", action="store_true", help="also list what was NOT selected and why")
    sp.add_argument("--json", action="store_true")

    sp = sub.add_parser("explain", help="explain one item for a task")
    sp.add_argument("project"); sp.add_argument("item"); sp.add_argument("--task", required=True)

    sp = sub.add_parser("bundle", help="build a combined bundle (memory, plus a Slice bundle if given)")
    sp.add_argument("project"); sp.add_argument("-o", "--out", required=True)
    sp.add_argument("--task", default=""); sp.add_argument("--fit", type=int, default=None)
    sp.add_argument("--slice-bundle", default=None)
    sp.add_argument("--mode", default=None, choices=["full", "decision-only", "headings", "recent", "exclude"])

    sp = sub.add_parser("check", help="verify a bundle against its manifest")
    sp.add_argument("bundle")

    sp = sub.add_parser("panel", help="print the dashboard panel HTML for a task")
    sp.add_argument("project"); sp.add_argument("--task", default="")

    sub.add_parser("mcp", help="run the stdio MCP server")

    args = p.parse_args(argv)
    try:
        if args.cmd == "scan":
            _r, _pf, items = _items(args.project)
            rows = sorted(items, key=lambda i: -estimate(i.text))
            if args.json:
                print(json.dumps([{"id": i.id, "title": i.title, "source_type": i.source_type,
                                   "path": i.provenance.path, "line": i.provenance.line,
                                   "date": i.date, "status": i.status, "blocked": i.blocked,
                                   "tokens_estimate": estimate(i.text)} for i in rows], indent=2))
            else:
                print(f"{'TOKENS(est)':>12}  TYPE         STATUS     SOURCE")
                for i in rows:
                    print(f"{estimate(i.text):>12}  {i.source_type:<12} {i.status:<10} "
                          f"{i.provenance.path}:{i.provenance.line or ''} {i.title[:60]}")
                print(f"\n{len(rows)} items, {sum(estimate(i.text) for i in rows)} estimated tokens total")
            return 0
        if args.cmd == "recall":
            _r, profile, items = _items(args.project)
            selected, not_selected, conflicts = select(items, args.task, profile)
            if args.json:
                print(json.dumps({
                    "selected": [{"id": e["item"].id, "title": e["item"].title,
                                  "score": e["score"], "pinned": e["pinned"],
                                  "tokens_estimate": e.get("tokens", estimate(e["item"].text)),
                                  "provenance": e["item"].provenance.to_dict()} for e in selected],
                    "not_selected": [{"id": e["item"].id, "reason": e["reason"]} for e in not_selected],
                    "conflicts": conflicts}, indent=2))
            else:
                for e in selected:
                    pin = " [pinned rule]" if e["pinned"] else ""
                    print(f"{e.get('tokens', estimate(e['item'].text)):>7} est  score={e['score']:.4f}{pin}  "
                          f"{e['item'].title} ({e['item'].provenance.path})")
                for c in conflicts:
                    print(f"CONFLICT: {c['type']}: {c.get('current','')} - {c['note']}")
                if args.explain:
                    print("\nNot selected:")
                    for e in not_selected:
                        print(f"  - {e['item'].title}: {e['reason']}")
            return 0
        if args.cmd == "explain":
            _r, profile, items = _items(args.project)
            print(json.dumps(explain(items, args.task, args.item, profile), indent=2))
            return 0
        if args.cmd == "bundle":
            mf = build_bundle(args.project, args.out, task=args.task, fit=args.fit,
                              slice_bundle=args.slice_bundle, mode=args.mode)
            print(f"bundle written to {args.out}: {mf['totals']}")
            if mf["conflicts"]:
                print(f"conflicts/superseded flagged: {len(mf['conflicts'])} (see RECALL.md)")
            return 0
        if args.cmd == "check":
            ok, problems = check_bundle(args.bundle)
            if ok:
                print(f"OK: {args.bundle} matches its manifest")
                return 0
            for prob in problems:
                print(f"FAIL: {prob}")
            return 1
        if args.cmd == "panel":
            _r, profile, items = _items(args.project)
            selected, not_selected, _c = select(items, args.task, profile)
            total = sum(e.get("tokens", estimate(e["item"].text)) for e in selected)
            print(render_panel(selected, not_selected, total))
            return 0
        if args.cmd == "mcp":
            from .mcp_server import serve
            return serve()
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    return 2

if __name__ == "__main__":
    raise SystemExit(main())
