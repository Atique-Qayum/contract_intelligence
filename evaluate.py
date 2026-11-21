"""Score an extraction run against hand-written ground truth.
Run: python evaluate.py --pred outputs/x.jsonl --truth data/ground_truth_hard.json --label "rules / hard set"
Fields ending in _present check only that the terms were found (not their wording)."""
import argparse, json
from pathlib import Path

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--pred", required=True); ap.add_argument("--truth", required=True)
    ap.add_argument("--label", default="run"); a = ap.parse_args()
    truth = json.load(open(a.truth)); pred = {}
    for l in open(a.pred): r = json.loads(l); pred[r["source_file"]] = r
    fields = list(next(iter(truth.values())).keys()); ok = {f: 0 for f in fields}; misses = []
    for sf, t in truth.items():
        r = pred.get(sf, {})
        for f in fields:
            got = (r.get(f[:-8]) is not None) if f.endswith("_present") else r.get(f)
            if got == t[f]: ok[f] += 1
            else: misses.append(f"{sf}: {f} expected={t[f]!r} got={got!r}")
    total, hit = len(truth) * len(fields), sum(ok.values())
    lines = [f"## {a.label}: {hit}/{total} fields correct ({100*hit/total:.0f}%)"] + \
            [f"{f:<28}{ok[f]}/{len(truth)}" for f in fields] + (["Misses:"] + misses if misses else ["No misses"])
    print("\n".join(lines))

if __name__ == "__main__":
    main()
