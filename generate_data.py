"""Generate FULLY SYNTHETIC contracts (PDF/DOCX) and finance CSVs. No real data.
Run: python generate_data.py
Deliberate problems are built in: missing terms, conflicting values, duplicate file,
client-name variants, an unusual label wording, an unpaid invoice, a short payment."""
import csv, json, random
from datetime import date, timedelta
from pathlib import Path
from docx import Document
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from config import FX_TO_EUR

random.seed(42)
ROOT = Path(__file__).parent
CON, FIN = ROOT / "data" / "contracts", ROOT / "data" / "finance"
CON.mkdir(parents=True, exist_ok=True); FIN.mkdir(parents=True, exist_ok=True)

AMP, LDT, SFL = "Advanced Management Programme", "Leading Digital Transformation", "Strategic Finance for Leaders"
CA = "More than 60 days before start: full refund. 30 to 60 days: 50% fee. Under 30 days: 100% fee."
CB = "Written notice 45 days or more before start: full refund. Later cancellation: 75% of fees payable."
PA = "50% on signing; 50% within 30 days of programme start."
PB = "Net 30 days from invoice date."
PC = "100% payable 60 days before programme start."
H = [(0.5, "full"), (0.5, "full")]  # two invoices

def S(id, legal, canon, prog, start, n, cur, value, pay, cancel, fmt, inv, **kw):
    return dict(id=id, legal=legal, canon=canon, prog=prog, start=start, end=start + timedelta(days=4),
                n=n, cur=cur, value=value, pay=pay, cancel=cancel, fmt=fmt, inv=inv, **kw)

SPECS = [
 S("C-001", "Alpha Bank Ltd", "Alpha Bank", AMP, date(2026, 3, 9), 24, "EUR", 288000, PA, CA, "pdf", H),
 S("C-002", "Alpha Bank Ltd", "Alpha Bank", LDT, date(2026, 5, 18), 18, "EUR", 162000, PB, CB, "docx", [(1.0, "full")]),
 S("C-003", "Beta Logistics Group", "Beta Logistics", SFL, date(2026, 6, 8), 20, "USD", 240000, PA, CA, "pdf", [(0.5, "full"), (0.5, 0)]),
 S("C-004", "Beta Logistics Group", "Beta Logistics", LDT, date(2026, 9, 14), 16, "SGD", 210000, PC, CB, "docx", [(1.0, "full")]),
 S("C-005", "Gamma Energy", "Gamma Energy", AMP, date(2026, 4, 20), 30, "EUR", 330000, PA, CA, "pdf", [(0.5, "full"), (0.5, 160000)]),
 S("C-006", "Gamma Energy Corp", "Gamma Energy", LDT, date(2026, 10, 5), 15, "EUR", 150000, PB, CB, "docx", [(1.0, "full")]),
 S("C-007", "Delta Telecom Inc", "Delta Telecom", SFL, date(2026, 7, 6), 14, "SGD", 175000, PB, CA, "pdf", [(1.0, 0)], cost_mult=1.7),
 S("C-008", "Delta Telecom Inc", "Delta Telecom", AMP, date(2026, 11, 2), 22, "USD", 300000, PA, CB, "docx", H,
   pay_label="Fee Payment Arrangement", cost_mult=1.5),
 S("C-009", "Epsilon Pharma Ltd", "Epsilon Pharma", LDT, date(2026, 8, 24), 12, "EUR", 120000, None, CA, "pdf", [(1.0, "full")]),
 S("C-010", "Epsilon Pharma Ltd", "Epsilon Pharma", AMP, date(2026, 2, 16), 26, "EUR", 270000, PA, CB, "docx", H,
   sched=252000, bill=252000),
 S("C-011", "Beta Logistics Group", "Beta Logistics", SFL, date(2026, 6, 8), 20, "USD", 240000, PA, CA, "docx", [],
   dup_of="C-003"),
 S("C-012", "Zeta Bank", "Zeta Bank", SFL, date(2026, 12, 1), 20, "EUR", 140000, PB, None, "pdf", [(1.0, "full")]),
]

def d(x): return f"{x.day} {x.strftime('%B %Y')}"

def pages_for(s):
    p1 = ["EXECUTIVE EDUCATION PROGRAMME AGREEMENT", "(Synthetic sample - fictional parties)", "",
          f"Contract Reference: {s.get('dup_of', s['id'])}", f"Client: {s['legal']}", f"Programme: {s['prog']}",
          f"Programme Dates: {d(s['start'])} to {d(s['end'])}", f"Number of Participants: {s['n']}",
          f"Contract Value: {s['cur']} {s['value']:,.2f}"]
    if s["pay"]: p1.append(f"{s.get('pay_label', 'Payment Terms')}: {s['pay']}")
    p2 = ["SCHEDULE AND CONDITIONS"]
    if s["cancel"]: p2.append(f"Cancellation: {s['cancel']}")
    p2 += ["Expenses: Participant travel and accommodation are not included.",
           f"Fee Schedule Total: {s['cur']} {s.get('sched', s['value']):,.2f} excluding taxes."]
    return [p1, p2]

def write_pdf(path, pages):
    c = canvas.Canvas(str(path), pagesize=A4)
    for pg in pages:
        y = 800; c.setFont("Helvetica", 11)
        for line in pg:
            c.drawString(50, y, line); y -= 18
        c.showPage()
    c.save()

def write_docx(path, pages):
    doc = Document()
    for i, pg in enumerate(pages):
        for line in pg: doc.add_paragraph(line)
        if i < len(pages) - 1: doc.add_page_break()
    doc.save(str(path))

truth, inv_rows, pay_rows, cost_rows = {}, [], [], []
for s in SPECS:
    slug = s["legal"].replace(" ", "_")
    name = f"{s['id']}_{slug}{'_copy' if s.get('dup_of') else ''}.{s['fmt']}"
    (write_pdf if s["fmt"] == "pdf" else write_docx)(CON / name, pages_for(s))
    truth[name] = dict(contract_id=s.get("dup_of", s["id"]), client_name=s["canon"], programme=s["prog"],
        start_date=s["start"].isoformat(), end_date=s["end"].isoformat(), participants=s["n"],
        currency=s["cur"], contract_value=float(s["value"]), payment_terms=s["pay"], cancellation_terms=s["cancel"])
    if s.get("dup_of"): continue
    bill = s.get("bill", s["value"])
    for k, (frac, paid) in enumerate(s["inv"], 1):
        iid = f"INV-{s['id'][2:]}-{k}"; amt = round(bill * frac, 2)
        issue = s["start"] - timedelta(days=60 if k == 1 else 0)
        inv_rows.append([iid, s["id"], amt, s["cur"], issue.isoformat(), (issue + timedelta(days=30)).isoformat()])
        paid_amt = amt if paid == "full" else float(paid)
        if paid_amt > 0:
            pay_rows.append([f"PAY-{iid[4:]}", iid, s["id"], paid_amt, s["cur"], (issue + timedelta(days=35)).isoformat()])
    eur = s["value"] * FX_TO_EUR[s["cur"]]; m = s.get("cost_mult", 1.0)
    for t, lo, hi in [("faculty", .22, .28), ("venue", .10, .15), ("travel", .05, .09),
                      ("delivery_staff", .04, .07), ("materials", .02, .04)]:
        cost_rows.append([s["id"], t, round(eur * random.uniform(lo, hi) * m, 2)])

def wcsv(name, header, rows):
    with open(FIN / name, "w", newline="") as f:
        csv.writer(f).writerows([header] + rows)
wcsv("invoices.csv", ["invoice_id", "contract_id", "amount", "currency", "issue_date", "due_date"], inv_rows)
wcsv("payments.csv", ["payment_id", "invoice_id", "contract_id", "amount", "currency", "payment_date"], pay_rows)
wcsv("costs.csv", ["contract_id", "cost_type", "amount_eur"], cost_rows)
(ROOT / "data" / "ground_truth.json").write_text(json.dumps(truth, indent=2))
print(f"Generated {len(SPECS)} contract files, {len(inv_rows)} invoices, {len(pay_rows)} payments, {len(cost_rows)} cost lines")
