"""Load validated extraction + finance CSVs into SQLite (outputs/pipeline.db).
SQLite keeps the demo runnable anywhere; the schema/SQL port to PostgreSQL with minor changes.
Run: python load_db.py   (after extract.py)"""
import json, os, sqlite3
from pathlib import Path
import pandas as pd
from config import FX_TO_EUR

ROOT = Path(__file__).parent
DB = Path(os.environ.get("CI_DB", ROOT / "outputs" / "pipeline.db"))  # CI_DB overrides the location

SCHEMA = """
DROP TABLE IF EXISTS contracts; DROP TABLE IF EXISTS review_flags; DROP TABLE IF EXISTS fx;
CREATE TABLE contracts (contract_id TEXT PRIMARY KEY, client_name TEXT, client_name_raw TEXT, programme TEXT,
  start_date TEXT, end_date TEXT, participants INTEGER, currency TEXT, contract_value REAL,
  payment_terms TEXT, cancellation_terms TEXT, source_file TEXT, status TEXT);
CREATE TABLE review_flags (source_file TEXT, contract_id TEXT, flag TEXT);
CREATE TABLE fx (currency TEXT PRIMARY KEY, rate_to_eur REAL);
"""

def main():
    recs = [json.loads(l) for l in open(ROOT / "outputs" / "extracted.jsonl")]
    con = sqlite3.connect(DB); con.executescript(SCHEMA)
    con.executemany("INSERT INTO fx VALUES (?,?)", FX_TO_EUR.items())
    by_id = {}
    for r in sorted(recs, key=lambda r: r["source_file"]):
        if not r["contract_id"]:
            con.execute("INSERT INTO review_flags VALUES (?,?,?)", (r["source_file"], None, "NO_CONTRACT_ID")); continue
        by_id.setdefault(r["contract_id"], []).append(r)
    for cid, group in by_id.items():
        keep, extra = group[0], group[1:]
        flags = {keep["source_file"]: list(keep["flags"])}
        for d in extra:  # same contract ID found in another file
            same = (d["client_name"], d["contract_value"]) == (keep["client_name"], keep["contract_value"])
            flags[d["source_file"]] = d["flags"] + ["DUPLICATE_IDENTICAL" if same else "DUPLICATE_CONFLICT"]
            if not same: flags[keep["source_file"]].append("DUPLICATE_CONFLICT")
        for sf, fl in flags.items():
            con.executemany("INSERT INTO review_flags VALUES (?,?,?)", [(sf, cid, f) for f in fl])
        status = "needs_review" if flags[keep["source_file"]] else "approved"
        con.execute("INSERT INTO contracts VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", (cid, keep["client_name"],
            keep["client_name_raw"], keep["programme"], keep["start_date"], keep["end_date"], keep["participants"],
            keep["currency"], keep["contract_value"], keep["payment_terms"], keep["cancellation_terms"],
            keep["source_file"], status))
    for name in ["invoices", "payments", "costs"]:
        pd.read_csv(ROOT / "data" / "finance" / f"{name}.csv").to_sql(name, con, if_exists="replace", index=False)
    con.commit()
    n = con.execute("SELECT COUNT(*) FROM contracts").fetchone()[0]
    print(f"Loaded {n} unique contracts from {len(recs)} files -> {DB}")

if __name__ == "__main__":
    main()
