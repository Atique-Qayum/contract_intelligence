"""Answer the seven business questions, show data-quality flags, and measure extraction accuracy.
Run: python report.py   -> prints and saves outputs/report.md"""
import json, os, re, sqlite3
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).parent

def main():
    con = sqlite3.connect(os.environ.get("CI_DB", ROOT / "outputs" / "pipeline.db"))
    out = ["# Contract Intelligence demo report (synthetic data)\n"]
    blocks = re.split(r"^-- (Q\w+): (.+)$", (ROOT / "sql" / "queries.sql").read_text(), flags=re.M)[1:]
    for i in range(0, len(blocks), 3):
        out.append(f"## {blocks[i]}: {blocks[i+1]}\n```\n{pd.read_sql(blocks[i+2].strip().rstrip(';'), con).to_string(index=False)}\n```\n")
    out.append("## Data-quality flags needing human review\n```\n" +
        pd.read_sql("SELECT source_file, contract_id, flag FROM review_flags ORDER BY source_file", con).to_string(index=False) + "\n```\n")
    truth = json.load(open(ROOT / "data" / "ground_truth.json"))
    recs = {json.loads(l)["source_file"]: json.loads(l) for l in open(ROOT / "outputs" / "extracted.jsonl")}
    fields, ok, miss = list(next(iter(truth.values())).keys()), {}, []
    for sf, t in truth.items():
        for f in fields:
            good = recs.get(sf, {}).get(f) == t[f]
            ok.setdefault(f, []).append(good)
            if not good: miss.append(f"{sf}: {f}")
    acc = "\n".join(f"{f:<20} {sum(v)}/{len(v)}" for f, v in ok.items())
    out.append(f"## Extraction accuracy vs hand-written ground truth\n```\n{acc}\nMisses: {miss or 'none'}\n```\n")
    text = "\n".join(out); (ROOT / "outputs" / "report.md").write_text(text); print(text)

if __name__ == "__main__":
    main()
