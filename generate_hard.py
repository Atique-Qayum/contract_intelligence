"""Generate 8 HARDER synthetic contracts written as prose with varied wording, date and currency formats.
These are what a regex baseline struggles with and an LLM should handle. Fictional parties only.
Run: python generate_hard.py  -> data/contracts_hard/*.docx + data/ground_truth_hard.json"""
import json
from datetime import date, timedelta
from pathlib import Path
from docx import Document

ROOT = Path(__file__).parent
OUT = ROOT / "data" / "contracts_hard"; OUT.mkdir(parents=True, exist_ok=True)
MONTHS = ["January","February","March","April","May","June","July","August","September","October","November","December"]
def ordinal(n): return f"{n}{'th' if 11<=n%100<=13 else {1:'st',2:'nd',3:'rd'}.get(n%10,'th')}"
DATE_FMT = [lambda d: f"{d.day} {MONTHS[d.month-1]} {d.year}",
            lambda d: f"{MONTHS[d.month-1]} {d.day}, {d.year}",
            lambda d: f"{ordinal(d.day)} {MONTHS[d.month-1]} {d.year}"]
MONEY_FMT = {"EUR": [lambda v: f"EUR {v:,.0f}", lambda v: f"€{v:,.2f}"],
             "USD": [lambda v: f"USD {v:,.2f}", lambda v: f"US${v:,.0f}"],
             "SGD": [lambda v: f"SGD {v:,.0f}", lambda v: f"S${v:,.2f}"]}
PAY = ["Invoices are payable within 45 days of receipt.",
       "A 30% deposit is due on signing and the balance two weeks before the programme starts.", None]
CAN = ["If the Client withdraws fewer than 21 days before the start, the full fee remains payable.",
       "Cancellations received at least 8 weeks in advance are fully refundable.", None]

# id, legal name, canonical client, programme, start, participants, currency, value, pay idx, cancel idx, date fmt, money fmt
ROWS = [
 ("EE-2026-014","Orion Retail Holdings Ltd","Orion Retail Holdings","Leading Digital Transformation",date(2026,3,3),18,"EUR",126000,0,0,0,0),
 ("EE-2026-015","Orion Retail Holdings Ltd","Orion Retail Holdings","Strategic Finance for Leaders",date(2026,6,15),12,"USD",96000,1,1,1,0),
 ("EE-2026-016","Pacific Cargo Corp","Pacific Cargo","Advanced Management Programme",date(2026,9,7),25,"SGD",275000,2,0,2,1),
 ("EE-2026-017","Nordic Health plc","Nordic Health","Leading Digital Transformation",date(2026,10,12),20,"EUR",168000,0,2,1,1),
 ("EE-2026-018","Sahara Energy Inc","Sahara Energy","Advanced Management Programme",date(2026,2,2),30,"USD",345000,1,0,0,1),
 ("EE-2026-019","Sahara Energy Inc","Sahara Energy","Strategic Finance for Leaders",date(2026,11,9),10,"EUR",89500,2,2,2,1),
 ("EE-2026-020","Lumen Telecom Group","Lumen Telecom","Leading Digital Transformation",date(2026,4,13),16,"SGD",132000,0,1,0,0),
 ("EE-2026-021","Lumen Telecom Group","Lumen Telecom","Advanced Management Programme",date(2026,5,18),22,"EUR",242000,1,2,1,0),
]
truth = {}
for i, (cid, legal, canon, prog, start, n, cur, val, pi, ci, df, mf) in enumerate(ROWS, 1):
    end = start + timedelta(days=4); D, M = DATE_FMT[df], MONEY_FMT[cur][mf]
    doc = Document()
    doc.add_heading("Letter of Engagement", 1)
    doc.add_paragraph(f"Our reference: {cid}")
    doc.add_paragraph(f"This agreement is made between the Business School and {legal} (the \"Client\").")
    doc.add_paragraph(f"The Client engages the School to deliver \"{prog}\" for {n} participants, "
                      f"running from {D(start)} to {D(end)}.")
    doc.add_paragraph(f"The total fee is {M(val)}, exclusive of taxes. " + (PAY[pi] or ""))
    if CAN[ci]: doc.add_paragraph(CAN[ci])
    doc.add_paragraph("Participant travel and accommodation are not included.")
    name = f"H-{i:02d}_{canon.replace(' ', '_')}.docx"; doc.save(str(OUT / name))
    truth[name] = dict(contract_id=cid, client_name=canon, programme=prog, start_date=start.isoformat(),
        end_date=end.isoformat(), participants=n, currency=cur, contract_value=float(val),
        payment_terms_present=PAY[pi] is not None, cancellation_terms_present=CAN[ci] is not None)
(ROOT / "data" / "ground_truth_hard.json").write_text(json.dumps(truth, indent=2))
print(f"Generated {len(ROWS)} hard contracts")
