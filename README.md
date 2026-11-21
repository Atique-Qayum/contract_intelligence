# Contract Intelligence & Financial Analytics (prototype, synthetic data)

Portfolio project. NOT an INSEAD system; all parties, contracts and figures are fictional.
Flow: contracts (PDF/DOCX) -> extraction -> Pydantic validation + flags -> SQLite -> SQL answers -> report.

## Windows quick start (PowerShell, VS Code terminal)
    python -m venv .venv
    .venv\Scripts\Activate.ps1      # if blocked: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
    pip install -r requirements.txt
    .\run_all.ps1                   # runs every step below in order

## Run step by step (Python 3.10+)
    pip install -r requirements.txt
    python generate_data.py   # synthetic contracts + finance CSVs + ground truth
    python extract.py         # -> outputs/extracted.jsonl (rules mode, no API key)
    python load_db.py         # -> outputs/pipeline.db
    python report.py          # -> prints + outputs/report.md

## Business questions answered (sql/queries.sql)
Q1 contracts per client | Q2 total contracted revenue | Q3 payment terms per programme |
Q4 outstanding payments | Q5 cancellation conditions | Q6 contracted vs received | Q7 profitability by programme/client

## What was tested
Ran end to end on the 12 synthetic contracts: 5 files flagged, 1 duplicate detected, accuracy 119/120 fields.
The one miss is deliberate: C-008 labels payment terms "Fee Payment Arrangement", which the regex baseline
does not recognise; it is flagged MISSING_FIELD instead of guessed.

## Two test sets
- `data/contracts` (12 templated files): regex baseline 119/120 fields. Flatters the baseline.
- `data/contracts_hard` (8 prose letters, mixed date/currency formats): regex baseline 5/80 (6%), and every file is
  flagged for review rather than silently wrong. This is the gap an LLM has to close.
    python generate_hard.py
    python extract.py --input data/contracts_hard --output outputs/extracted_hard_rules.jsonl
    python evaluate.py --pred outputs/extracted_hard_rules.jsonl --truth data/ground_truth_hard.json --label "rules / hard set"

## Free LLM run (you do this; it has NOT been run yet)
1. Install Ollama (free, local) and pull a model of your choice; set `OLLAMA_MODEL` to its name.
2. `python extract.py --mode llm --input data/contracts_hard --output outputs/extracted_hard_llm.jsonl`
3. `python evaluate.py --pred outputs/extracted_hard_llm.jsonl --truth data/ground_truth_hard.json --label "LLM / hard set"`
Paid option: `LLM_PROVIDER=anthropic` with `pip install anthropic` and an API key. Small local models can be weak at
extraction; the validation and flags exist for exactly that. Report whatever score you actually get.

## Tests
`python tests/test_pipeline.py` uses a FAKE LLM to prove the safety logic works (hallucinated values flagged,
bad currency nulled, conflicts flagged, missing stays null). It does not measure model quality.

## Not tested / limitations (be honest about these)
- `--mode llm` is written but NOT run against any real model. Real LLM accuracy is unmeasured.
- Rules mode scores high because the synthetic contracts are templated. Real contracts are messier;
  that is the case for the LLM mode, and why validation + human review exist.
- FX rates in config.py are illustrative assumptions. Revenue is CONTRACTED, not recognised.
- Costs are invented; real profitability needs agreed cost-allocation rules with Finance.
- Excel contracts, scanned/OCR files, PostgreSQL, Power BI and RAG search are planned next steps.
- SQLite is used for portability; SQL ports to PostgreSQL with small changes.

## Design rules
Missing data stays null; the LLM never calculates or approves figures; each value is checked against the source
text (UNGROUNDED flag) with page evidence; conflicts and duplicates are flagged, not silently resolved;
contracts >= EUR 300k always go to human review.
