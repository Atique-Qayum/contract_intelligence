"""Extract contract fields -> validate with Pydantic -> flag problems -> outputs/extracted.jsonl
Run:  python extract.py                (rules mode: offline, no API key)
      python extract.py --mode llm     (LLM mode; default provider = free local Ollama; UNTESTED here)
Rules: missing data stays null; the model never calculates; every value is checked against the source text."""
import argparse, json, logging, os, re
from datetime import date, datetime
from pathlib import Path
from typing import Optional
from docx import Document
from pydantic import BaseModel, ValidationError, field_validator
from pypdf import PdfReader
from config import ALLOWED_CURRENCIES, FX_TO_EUR, HIGH_VALUE_EUR, REQUIRED_FIELDS

log = logging.getLogger("extract")
ROOT = Path(__file__).parent

class Evidence(BaseModel):
    page: int
    text: str

class ContractRecord(BaseModel):
    source_file: str
    extraction_mode: str
    contract_id: Optional[str] = None
    client_name_raw: Optional[str] = None
    client_name: Optional[str] = None
    programme: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    participants: Optional[int] = None
    currency: Optional[str] = None
    contract_value: Optional[float] = None
    schedule_total: Optional[float] = None
    payment_terms: Optional[str] = None
    cancellation_terms: Optional[str] = None
    evidence: dict[str, Evidence] = {}
    flags: list[str] = []

    @field_validator("currency")
    @classmethod
    def _cur(cls, v):
        if v is not None and v not in ALLOWED_CURRENCIES: raise ValueError(f"unsupported currency {v}")
        return v

    @field_validator("contract_value", "schedule_total")
    @classmethod
    def _pos(cls, v):
        if v is not None and v <= 0: raise ValueError("must be positive")
        return v

# ---------- 1. read files (page-aware) ----------
def read_pages(path: Path) -> list[str]:
    if path.suffix.lower() == ".pdf":
        return [p.extract_text() or "" for p in PdfReader(str(path)).pages]
    if path.suffix.lower() == ".docx":
        pages, cur = [], []
        for p in Document(str(path)).paragraphs:
            if 'w:br w:type="page"' in p._p.xml: pages.append(cur); cur = []
            if p.text.strip(): cur.append(p.text)
        pages.append(cur)
        return ["\n".join(x) for x in pages]
    raise ValueError(f"unsupported file type {path.suffix}")  # .xlsx is a planned extension

# ---------- 2a. rules extractor (offline baseline) ----------
NUM = r"([A-Z]{3})\s*([\d,]+(?:\.\d+)?)"
PATTERNS = {
    "contract_id": r"^(?:Contract Reference|Agreement No\.?)\s*:\s*(.+)$",
    "client_name_raw": r"^Client\s*:\s*(.+)$",
    "programme": r"^Programme\s*:\s*(.+)$",
    "dates": r"^Programme Dates\s*:\s*(.+?)\s+to\s+(.+)$",
    "participants": r"^Number of Participants\s*:\s*(\d+)",
    "value": rf"^Contract Value\s*:\s*{NUM}",
    "schedule": rf"^Fee Schedule Total\s*:\s*{NUM}",
    "payment_terms": r"^(?:Payment Terms|Terms of Payment)\s*:\s*(.+)$",
    "cancellation_terms": r"^Cancellation\s*:\s*(.+)$",
}
def _find(text, key):
    m = re.search(PATTERNS[key], text, re.M | re.I)
    return m.groups() if m else None

def _d(s):
    try: return datetime.strptime(s.strip(), "%d %B %Y").date().isoformat()
    except Exception: return None

def extract_rules(text: str) -> dict:
    g = lambda k: (_find(text, k) or [None])[0]
    dates, val, sch = _find(text, "dates"), _find(text, "value"), _find(text, "schedule")
    return dict(contract_id=g("contract_id"), client_name_raw=g("client_name_raw"), programme=g("programme"),
        start_date=_d(dates[0]) if dates else None, end_date=_d(dates[1]) if dates else None,
        participants=int(g("participants")) if g("participants") else None,
        currency=val[0] if val else None, contract_value=float(val[1].replace(",", "")) if val else None,
        schedule_total=float(sch[1].replace(",", "")) if sch else None,
        payment_terms=g("payment_terms"), cancellation_terms=g("cancellation_terms"))

# ---------- 2b. LLM extractor (UNTESTED in this build) ----------
PROMPT = """Extract these fields from the contract text. Use null for anything not stated. Never guess.
Copy payment_terms and cancellation_terms verbatim. Dates as YYYY-MM-DD. Amounts as plain numbers.
Return ONLY JSON with keys: contract_id, client_name_raw, programme, start_date, end_date, participants,
currency, contract_value, schedule_total, payment_terms, cancellation_terms.
If a fee-schedule total differs from the contract value, report both.

CONTRACT TEXT:
"""
def _parse_json(raw: str) -> dict:
    return json.loads(raw[raw.index("{"): raw.rindex("}") + 1])

def extract_llm(text: str) -> dict:
    """Provider chosen by env LLM_PROVIDER: 'ollama' (free, local) or 'anthropic' (paid API). UNTESTED against real models here."""
    provider = os.environ.get("LLM_PROVIDER", "ollama")
    if provider == "ollama":  # needs Ollama running locally and a pulled model: OLLAMA_MODEL=<name>
        import urllib.request
        body = json.dumps({"model": os.environ.get("OLLAMA_MODEL", "llama3.1"), "prompt": PROMPT + text,
                           "stream": False, "format": "json"}).encode()
        req = urllib.request.Request(os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate"),
                                     data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=300) as r:
            return _parse_json(json.loads(r.read())["response"])
    import anthropic  # needs `pip install anthropic` and ANTHROPIC_API_KEY
    msg = anthropic.Anthropic().messages.create(model=os.environ.get("EXTRACTION_MODEL", "claude-sonnet-5-5"),
                                 max_tokens=1500, messages=[{"role": "user", "content": PROMPT + text}])
    return _parse_json(msg.content[0].text)

# ---------- 3. evidence, validation, flags ----------
def normalise_client(name):
    if not name: return None
    prev = None
    while prev != name:
        prev, name = name, re.sub(r"\s+(Ltd|Limited|Group|Corp|Corporation|Inc|plc|LLC)\.?$", "", name.strip(), flags=re.I)
    return name.strip()

def locate(pages, needle):
    for i, t in enumerate(pages, 1):
        if needle and needle in t: return i
    return None

def build_record(path: Path, mode: str) -> ContractRecord:
    pages = read_pages(path)
    fields = (extract_llm if mode == "llm" else extract_rules)("\n".join(pages))
    flags = []
    for _ in range(2):  # on a validation error, null the bad field, flag it, retry once
        try:
            rec = ContractRecord(source_file=path.name, extraction_mode=mode, **fields); break
        except ValidationError as e:
            for err in e.errors():
                f = err["loc"][0]; fields[f] = None; flags.append(f"VALIDATION_ERROR:{f}")
    rec.client_name = normalise_client(rec.client_name_raw)
    ev = {}
    for f in ["contract_id", "client_name_raw", "programme", "payment_terms", "cancellation_terms"]:
        v = getattr(rec, f)
        if v is None: continue
        pg = locate(pages, v)
        if pg: ev[f] = Evidence(page=pg, text=v[:200])
        else: flags.append(f"UNGROUNDED:{f}")  # value not found in source text
    if rec.contract_value:
        for s in (f"{rec.contract_value:,.2f}", f"{rec.contract_value:,.0f}"):
            pg = locate(pages, s)
            if pg: ev["contract_value"] = Evidence(page=pg, text=f"{rec.currency} {s}"); break
        else: flags.append("UNGROUNDED:contract_value")
    rec.evidence = ev
    flags += [f"MISSING_FIELD:{f}" for f in REQUIRED_FIELDS if getattr(rec, f) is None]
    if rec.contract_value and rec.schedule_total and abs(rec.contract_value - rec.schedule_total) > 0.01:
        flags.append("VALUE_CONFLICT")
    if rec.contract_value and rec.currency and rec.contract_value * FX_TO_EUR[rec.currency] >= HIGH_VALUE_EUR:
        flags.append("HIGH_VALUE_REVIEW")
    rec.flags = flags
    return rec

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--mode", choices=["rules", "llm"], default="rules")
    ap.add_argument("--input", default="data/contracts"); ap.add_argument("--output", default="outputs/extracted.jsonl")
    a = ap.parse_args(); mode = a.mode
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    out = ROOT / "outputs"; out.mkdir(exist_ok=True)
    files = sorted(p for p in (ROOT / a.input).iterdir() if p.suffix.lower() in {".pdf", ".docx"})
    n_flag = 0
    with open(ROOT / a.output, "w") as f:
        for p in files:
            try: rec = build_record(p, mode)
            except Exception as e: log.error("FAILED %s: %s", p.name, e); continue
            f.write(rec.model_dump_json() + "\n"); n_flag += bool(rec.flags)
            log.info("%-36s flags=%s", p.name, rec.flags or "-")
    log.info("Done: %d files, %d with flags -> %s", len(files), n_flag, a.output)

if __name__ == "__main__":
    main()
