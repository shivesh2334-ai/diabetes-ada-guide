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

## Notes
See `NOTICE.md` for licensing and clinical-use cautions.
