
#!/usr/bin/env python3
import argparse, json, sys, os

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mapping", required=True)
    ap.add_argument("--caseIds", default="")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    case_ids = set()
    if args.caseIds:
        for part in args.caseIds.replace(",", " ").split():
            if part.strip().isdigit():
                case_ids.add(int(part.strip()))

    with open(args.mapping, "r", encoding="utf-8") as f:
        spec = json.load(f)

    # Build lookup from testCaseId -> test selector (path)
    rows = spec.get("mappings", [])
    selected = []
    for row in rows:
        tcid = int(row["testCaseId"])
        if not case_ids or tcid in case_ids:
            selected.append(row["path"])

    if not selected:
        print("No tests resolved from mapping; check case IDs and mapping file.", file=sys.stderr)
        sys.exit(2)

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write("\n".join(selected))

    print(f"Resolved {len(selected)} tests → {args.out}")

if __name__ == "__main__":
    main()
