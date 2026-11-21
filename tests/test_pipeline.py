"""Plumbing tests with a FAKE LLM (no model is called). They check validation/flag logic, not LLM quality.
Run: python tests/test_pipeline.py"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import extract

FILE = Path(__file__).resolve().parent.parent / "data" / "contracts" / "C-001_Alpha_Bank_Ltd.pdf"
GOOD = dict(contract_id="C-001", client_name_raw="Alpha Bank Ltd", programme="Advanced Management Programme",
            start_date="2026-03-09", end_date="2026-03-13", participants=24, currency="EUR", contract_value=288000,
            schedule_total=288000, payment_terms="50% on signing; 50% within 30 days of programme start.",
            cancellation_terms="More than 60 days before start: full refund. 30 to 60 days: 50% fee. Under 30 days: 100% fee.")

def run(**over):
    extract.extract_llm = lambda text: {**GOOD, **over}
    return extract.build_record(FILE, "llm")

def test_clean():
    r = run(); assert r.client_name == "Alpha Bank" and "UNGROUNDED:payment_terms" not in r.flags

def test_hallucinated_text_is_flagged():
    assert "UNGROUNDED:payment_terms" in run(payment_terms="Payment in full 90 days after the programme.").flags

def test_hallucinated_value_is_flagged():
    assert "UNGROUNDED:contract_value" in run(contract_value=999999).flags

def test_conflict_flagged():
    assert "VALUE_CONFLICT" in run(schedule_total=250000).flags

def test_bad_currency_nulled_and_flagged():
    r = run(currency="XYZ"); assert r.currency is None and "VALIDATION_ERROR:currency" in r.flags

def test_missing_stays_null():
    r = run(payment_terms=None); assert r.payment_terms is None and "MISSING_FIELD:payment_terms" in r.flags

if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"): f(); print("PASS", n)
