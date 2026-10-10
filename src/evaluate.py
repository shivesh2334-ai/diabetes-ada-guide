"""Reference rule engine v2 for ada2026_prescription_kb.json (ADA 2026 Sections 2, 3, 5, 6, 9, 10, 11, 12).

    from evaluate import evaluate, diagnose, glycemic_targets, ckd_stage, foot_risk
    result = evaluate(patient_dict, kb)

Missing boolean fields are treated as False. Decision support only: clinician must verify.
"""
import json, os

# ------------------------------------------------------------ rule DSL
def _cmp(pv, op, v, patient):
    if op == "above_goal_by":
        goal = patient.get("a1c_goal")
        return pv is not None and goal is not None and (pv - goal) >= v
    if pv is None and isinstance(v, bool):
        pv = False
    if pv is None:
        return False
    if op == "==": return pv == v
    if op == "!=": return pv != v
    if op == "<": return pv < v
    if op == "<=": return pv <= v
    if op == ">": return pv > v
    if op == ">=": return pv >= v
    if op == "between": return v[0] <= pv <= v[1]
    if op == "in": return pv in v
    raise ValueError(op)

def _eval(node, patient):
    if "all" in node: return all(_eval(n, patient) for n in node["all"])
    if "any" in node: return any(_eval(n, patient) for n in node["any"])
    if node["op"] == "!=" and node["value"] == "none":
        return patient.get(node["field"]) not in (None, "none")
    if node["field"] == "on_acei_arb" and patient.get("on_acei_arb") is None:
        patient = dict(patient, on_acei_arb=bool(patient.get("on_acei") or patient.get("on_arb")))
    return _cmp(patient.get(node["field"]), node["op"], node["value"], patient)

# ------------------------------------------------------------ derived calculators
def diagnose(p):
    """Section 2 / Tables 2.1-2.2. Inputs: a1c, fpg, ogtt_2h, random_glucose, classic_symptoms, crisis, a1c_unreliable."""
    if not any(p.get(key) is not None for key in ("a1c", "fpg", "fasting_glucose", "ogtt_2h", "random_glucose")):
        return {"status": "insufficient_data", "criteria_met": [], "note": "No diagnostic glucose or A1C measurements supplied.", "caveat": ""}
    a1c = None if p.get("a1c_unreliable") else p.get("a1c")
    fpg, og, rnd = p.get("fpg", p.get("fasting_glucose")), p.get("ogtt_2h"), p.get("random_glucose")
    dm = []
    if a1c is not None and a1c >= 6.5: dm.append("A1C >=6.5%")
    if fpg is not None and fpg >= 126: dm.append("FPG >=126")
    if og is not None and og >= 200: dm.append("2-h OGTT >=200")
    unequivocal = bool(rnd is not None and rnd >= 200 and (p.get("classic_symptoms") or p.get("crisis")))
    pre = []
    if a1c is not None and 5.7 <= a1c <= 6.4: pre.append("A1C 5.7-6.4%")
    if fpg is not None and 100 <= fpg <= 125: pre.append("IFG")
    if og is not None and 140 <= og <= 199: pre.append("IGT")
    if unequivocal:
        status, note = "diabetes", "Random glucose >=200 with symptoms/crisis: diagnostic without repeat."
    elif len(dm) >= 2 or (dm and p.get("repeat_confirmed")):
        status, note = "diabetes", "Confirmed by two abnormal results."
    elif dm:
        status, note = "probable_diabetes_needs_confirmation", "One abnormal test: repeat same test or another test promptly (repeat the abnormal one if discordant)."
    elif pre:
        status, note = "prediabetes", "Retest at least annually; lifestyle/DPP (Section 3)."
    else:
        status, note = "normal", "Rescreen at least every 3 years (sooner with risk change)."
    if a1c is not None and abs((a1c or 0) - 6.5) <= 0.2:
        note += " Result near threshold: counsel on symptoms, repeat in 3-6 months."
    return {"status": status, "criteria_met": dm or pre, "note": note,
            "caveat": "A1C ignored (unreliable): use plasma glucose." if p.get("a1c_unreliable") else ""}

def gdm_one_step(fasting, h1, h2):
    hits = [n for n, v, t in (("fasting", fasting, 92), ("1h", h1, 180), ("2h", h2, 153)) if v is not None and v >= t]
    return {"gdm": bool(hits), "values_met": hits}

def glycemic_targets(p):
    """Section 6 Table 6.2/6.3, Fig 6.1."""
    h = p.get("older_health_status")
    complex_ = h in ("complex", "very_complex") or p.get("limited_life_expectancy") or p.get("severe_comorbidity")
    if h == "very_complex":
        return {"a1c": "no A1C goal; avoid symptomatic hypo/hyperglycemia", "cgm": None}
    if complex_:
        return {"a1c": "<8.0%", "preprandial": "80-130 mg/dL (relaxed as needed)", "cgm": {"TIR70-180": ">50%", "TBR<70": "<1%", "TBR<54": "<1%", "TAR>180": "<50%", "TAR>250": "<10%", "CV": "<=36%"}}
    lower = (not p.get("hypoglycemia_risk_high") and not p.get("level2_3_hypo_recent") and not p.get("hypoglycemia_unawareness")
             and not p.get("on_insulin") and not p.get("on_sulfonylurea") and p.get("diabetes_type") == "type2" and not p.get("ascvd"))
    return {"a1c": "<7.0% (<6.5% may be appropriate if good health and low treatment risk)" if lower else "<7.0%",
            "preprandial": "80-130 mg/dL", "peak_postprandial": "<180 mg/dL",
            "cgm": {"TIR70-180": ">70%", "TBR<70": "<4%", "TBR<54": "<1%", "TAR>180": "<25%", "TAR>250": "<5%", "CV": "<=36%"}}

def ckd_stage(egfr, uacr):
    """Section 11 Fig 11.1: G/A stage, monitoring per year."""
    if egfr is None or uacr is None: return None
    g = "G1" if egfr >= 90 else "G2" if egfr >= 60 else "G3a" if egfr >= 45 else "G3b" if egfr >= 30 else "G4" if egfr >= 15 else "G5"
    a = "A1" if uacr < 30 else "A2" if uacr < 300 else "A3"
    matrix = {"G1": (1, 1, 2), "G2": (1, 1, 2), "G3a": (1, 2, 3), "G3b": (2, 3, 3), "G4": (3, 3, 4), "G5": (4, 4, 4)}
    times = matrix[g][("A1", "A2", "A3").index(a)]
    ckd = egfr < 60 or uacr >= 30
    return {"stage": g + a, "ckd_present": ckd, "monitor_times_per_year": times,
            "refer_nephrology": g in ("G4", "G5") or (g == "G3b" and a == "A3")}

def foot_risk(p):
    """Section 12 Table 12.1 (IWGDF)."""
    lops, pad = bool(p.get("lops")), bool(p.get("pad"))
    hist = p.get("foot_ulcer_history") or p.get("amputation_history") or p.get("kidney_failure") or p.get("dialysis")
    if (lops or pad) and hist: cat, f = 3, "every 1-3 months"
    elif (lops and pad) or (lops and p.get("foot_deformity")) or (pad and p.get("foot_deformity")): cat, f = 2, "every 3-6 months"
    elif lops or pad: cat, f = 1, "every 6-12 months"
    else: cat, f = 0, "annually"
    return {"iwgdf_category": cat, "exam_frequency": f}

def lipid_plan(p):
    """Section 10 lipid recommendations."""
    age, ascvd = p.get("age"), bool(p.get("ascvd"))
    if ascvd:
        return {"statin": "high-intensity", "ldl_goal_mg_dl": 55, "reduction": ">=50%", "add_on": "ezetimibe/PCSK9 inhibitor if goal not met"}
    if age is None: return None
    if 40 <= age <= 75:
        extra = any(p.get(k) for k in ("hypertension", "obesity", "tobacco_or_vaping", "albuminuria", "high_cv_risk")) or (p.get("egfr") or 99) < 60
        return {"statin": "high-intensity" if extra else "moderate-intensity", "ldl_goal_mg_dl": 70 if extra else None,
                "add_on": "ezetimibe/PCSK9 inhibitor if LDL >=70 on max statin" if extra else None}
    if age > 75: return {"statin": "continue if on; else moderate-intensity after discussion"}
    if 20 <= age < 40: return {"statin": "consider moderate-intensity if extra risk factors"}
    return None

def bp_plan(p):
    s, d = p.get("systolic_bp"), p.get("diastolic_bp")
    if s is None and d is None: return None
    htn = (s or 0) >= 130 or (d or 0) >= 80
    two = (s or 0) >= 150 or (d or 0) >= 90
    goal = "<130/80 (SBP <120 if high CV/kidney risk)"
    return {"hypertension": htn, "goal": goal,
            "drug_therapy": ("start two drugs or single-pill combination" if two else "start and titrate drug therapy") if htn else
                            ("lifestyle (elevated BP)" if (s or 0) > 120 else "none needed")}

# ------------------------------------------------------------ main
CLASS_FLAGS = {"on_metformin": "METFORMIN", "on_sglt2i": "SGLT2I", "on_glp1ra": "GLP1RA", "on_dual_gip_glp1": "TIRZEPATIDE",
               "on_dpp4i": "DPP4I", "on_pioglitazone": "TZD", "on_sulfonylurea": "SU", "on_insulin": "INSULIN_ANALOG",
               "on_acei_arb": "ACEI_ARB", "on_nsmra": "NSMRA", "on_statin": "STATIN"}

def evaluate(patient, kb):
    patient = {key: value for key, value in patient.items() if value is not None}
    if "fpg" not in patient and "fasting_glucose" in patient:
        patient["fpg"] = patient["fasting_glucose"]
    if "repeat_confirmed" not in patient and "hba1c_ge_6_5_repeat_confirmed" in patient:
        patient["repeat_confirmed"] = patient["hba1c_ge_6_5_repeat_confirmed"]
    if "on_acei_arb" not in patient and any(key in patient for key in ("on_acei", "on_arb")):
        patient["on_acei_arb"] = bool(patient.get("on_acei") or patient.get("on_arb"))
    ins = {i["id"]: i for i in kb["instructions"]}
    fired, instr_ids = [], []
    for r in kb["rules"]:
        if _eval(r["when"], patient):
            fired.append(r)
            for i in r.get("instructions", []):
                if i not in instr_ids: instr_ids.append(i)
    active = [c for f, c in CLASS_FLAGS.items() if patient.get(f)]
    for i in kb["instructions"]:
        if i["category"] == "Medication" and any(c in active for c in i["class_ids"]) and i["id"] not in instr_ids:
            instr_ids.append(i["id"])
    if patient.get("diabetes_type") in ("type2", "prediabetes"):
        for i in ("INS-ACTIVITY-150", "INS-EAT-PATTERN", "INS-WATER"):
            if i not in instr_ids: instr_ids.append(i)
    if "INS-FOLLOWUP" not in instr_ids: instr_ids.append("INS-FOLLOWUP")
    sev_order = {"contraindication": 0, "warning": 1}
    alerts = sorted([{"rule": r["id"], "severity": r["severity"], "title": r["title"], "flags": r.get("flags", []),
                      "avoid": r.get("avoid", []), "source": r["rec"]} for r in fired if r["severity"] in sev_order],
                    key=lambda a: sev_order[a["severity"]])
    derived = {"diagnosis": diagnose(patient) if any(k in patient for k in ("fpg", "ogtt_2h")) or patient.get("diabetes_type") in ("unknown", None) else None,
               "glycemic_targets": glycemic_targets(patient),
               "ckd": ckd_stage(patient.get("egfr"), patient.get("uacr")),
               "foot_risk": foot_risk(patient), "lipids": lipid_plan(patient), "blood_pressure": bp_plan(patient)}
    return {"alerts": alerts,
            "suggestions": [{"rule": r["id"], "title": r["title"], "recommend": r.get("recommend", []), "note": r.get("note", ""), "source": r["rec"]}
                            for r in fired if r.get("recommend")],
            "derived": {k: v for k, v in derived.items() if v},
            "prescription_instructions": [ins[i]["text"] for i in instr_ids if i in ins],
            "evidence": sorted({r["rec"] for r in fired})}

if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    kb = json.load(open(os.path.join(here, "..", "data", "ada2026_prescription_kb.json")))
    demo = dict(diabetes_type="type2", age=62, a1c=8.9, a1c_goal=7.0, egfr=42, uacr=420, albuminuria=True, obesity=True, bmi=33, ascvd=True,
                hypertension=True, systolic_bp=148, diastolic_bp=88, potassium=4.4, ldl=92, on_metformin=True, on_sulfonylurea=True,
                on_acei=True, lops=True, retinopathy_stage="moderate_npdr", years_diabetes=14, sex_childbearing_potential=False)
    print(json.dumps(evaluate(demo, kb), indent=1))
    print(json.dumps(diagnose(dict(a1c=6.8, fpg=118)), indent=1))
