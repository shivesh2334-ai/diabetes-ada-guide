# ADA 2026 Prescription Knowledge Base

Structured database and rule engine for a prescription-writing platform. Given a patient record it returns
alerts, drug suggestions with ADA recommendation references, derived targets, and patient-facing instructions
to attach to the prescription.

## Layout
- `data/ada2026_prescription_kb.json` - full knowledge base (v2.0)
- `data/ada2026_prescription_kb.sqlite` - same content as SQL tables
- `src/extend_data.py`, `src/build.py` - source data and builder (`python src/build.py` regenerates `data/`)
- `src/evaluate.py` - reference rule engine

## Contents
Recommendations (Sections 2, 3, 5, 6, 9, 10, 11, 12), drug classes and agents (dose limits, renal thresholds, adverse
effects, US cost), insulin dosing rules, ~127 decision rules, ~59 prescription instruction templates, monitoring
schedule, referral triggers, fasting-risk score and dose adjustments, and reference tables (diagnostic criteria,
glycemic/CGM goals, hypoglycemia levels, CKD staging matrix, statin intensity, foot risk, neuropathic-pain drugs).

## Usage
```python
import json
from src.evaluate import evaluate
kb = json.load(open("data/ada2026_prescription_kb.json"))
patient = {"diabetes_type": "type2", "age": 62, "a1c": 8.9, "egfr": 42, "uacr": 420, "ascvd": True}
result = evaluate(patient, kb)
print(result["prescription_instructions"])
```
Run the demo: `python src/evaluate.py`. Missing yes/no fields are treated as `False`.

### Rule format
Each rule in `kb["rules"]` has `when` (nested `all`/`any` of `{field, op, value}`), `severity`
(`contraindication`, `warning`, `preferred`, `info`), `recommend`, `avoid`, `flags`, `instructions`, and the
ADA recommendation reference in `rec`. Patient fields are defined in `kb["patient_fields"]`.

## Vercel deployment
The `api/evaluate.py` Python function is served at `/api/evaluate`. Deploy the repository root as the Vercel project
root; Vercel detects the function automatically. No third-party Python packages are required.

Send a `POST` request with a JSON object containing a `patient` object:
```json
{
  "patient": {
    "diabetes_type": "type2",
    "age": 62,
    "a1c": 8.9,
    "egfr": 42,
    "uacr": 420,
    "ascvd": true
  }
}
```
The endpoint returns the evaluation result as JSON and accepts request bodies up to 1 MiB. The endpoint does not
provide authentication or store requests; do not send personally identifiable health information. This is clinical
decision-support output, not medical advice; clinicians must verify every recommendation.

## Notes
See `NOTICE.md` for licensing and clinical-use cautions.

### Web interface and deployment settings
- Homepage: `/`, with all 129 supported clinical parameters, example input, results and print support.
- Vercel Framework Preset: **Other**; Root Directory: repository root; Output Directory: `public`.
- Leave Build Command and Install Command at their defaults. No Node build or API key is needed.
- `vercel.json` includes the JSON knowledge base and `src/` in the Python function bundle.
- The legacy ZIP is an original source snapshot. Deploy the current repository files, not that archive.
- API inputs require `Content-Type: application/json`. Unknown fields, invalid types, non-finite numbers and invalid enum options return 400; oversized bodies return 413.
- Missing yes/no inputs retain the original engine's false assumption; review unknown history before using outputs. The clinical content has not been independently revalidated in this deployment update.

### Verification
```bash
python -m unittest discover -s tests -v
python -m compileall -q api src
node --check public/app.js
python src/build.py
```
The database builder regenerates the same knowledge-base JSON. SQLite integrity and rule-to-instruction references are checked separately. The API stores no patient requests; authentication and rate limiting are not implemented.
