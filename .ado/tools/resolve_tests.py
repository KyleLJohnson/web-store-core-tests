
# .ado/tools/resolve_tests.py
#!/usr/bin/env python3
import argparse, json, sys, os, pathlib

def eprint(*a): print(*a, file=sys.stderr)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mapping", required=True)
    ap.add_argument("--caseIds", default="")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    # Parse case IDs
    requested = set()
    if args.caseIds.strip():
        for token in args.caseIds.replace(",", " ").split():
            if token.strip().isdigit():
                requested.add(int(token.strip()))
            else:
                eprint(f"[WARN] Ignoring non-numeric caseId token: {token}")

    # Load mapping
    try:
        spec = json.load(open(args.mapping, encoding="utf-8"))
    except FileNotFoundError:
        eprint(f"[ERROR] Mapping file not found: {args.mapping}")
        sys.exit(2)

    mappings = spec.get("mappings", [])
    if not mappings:
        eprint("[ERROR] No 'mappings' array found in mapping file.")
        sys.exit(2)

    # Build selection
    selected = []
    for row in mappings:
        try:
            tcid = int(row["testCaseId"])
            path = row["path"]
        except Exception as ex:
            eprint(f"[ERROR] Bad row (missing testCaseId/path): {row}")
            sys.exit(3)

        if requested and tcid not in requested:
            continue

        # Minimal sanity check: file exists
        file_part = path.split("::", 1)[0]
        if not pathlib.Path(file_part).exists():
            eprint(f"[ERROR] File not found for testCaseId={tcid}: {file_part}")
            continue

        selected.append(path)

    if requested and not selected:
        eprint(f"[ERROR] None of the requested caseIds {sorted(requested)} resolved to valid paths.")
        sys.exit(4)

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write("\n".join(selected if selected else [m["path"] for m in mappings]))

    print("=== Resolved Selectors ===")
    for s in (selected if selected else [m["path"] for m in mappings]):
        print(s)
    print("==========================")

if __name__ == "__main__":
    main()
