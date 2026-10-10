import json, sqlite3, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "data")
os.makedirs(OUT, exist_ok=True)

META = {
    "name": "ADA 2026 Prescription Decision-Support Knowledge Base",
    "version": "2.0.0",
    "sources": [
        "ADA Standards of Care in Diabetes-2026, Section 9: Pharmacologic Approaches to Glycemic Treatment. Diabetes Care 2026;49(Suppl 1):S183-S215",
        "ADA Standards of Care in Diabetes-2026, Section 5: Facilitating Positive Health Behaviors and Well-being. Diabetes Care 2026;49(Suppl 1):S89-S131",
        "ADA Standards of Care in Diabetes-2026, Section 3: Prevention or Delay of Diabetes and Associated Comorbidities. Diabetes Care 2026;49(Suppl 1):S50-S60",
    ],
    "notes": [
        "Text is paraphrased/structured, not verbatim. ADA licence prohibits text/data mining and redistribution without written permission: obtain permission (permissions@diabetes.org) before commercial deployment.",
        "Prices are US AWP/NADAC (15 July 2025) from Table 9.3/9.4: relative cost only; replace with Indian market prices.",
        "Decision support only: a licensed clinician must confirm every recommendation against the patient and current product labels.",
        "Evidence grades A/B/C/E are the ADA grades attached to each recommendation.",
    ],
}

# ---------------- RECOMMENDATIONS (paraphrased) ----------------
# (id, section, grade, topic, summary)
RECS = [
 # Section 9
 ("9.1","9","A","T1D insulin","Most adults with T1D: CSII or multiple daily injections of basal + prandial insulin (injected or inhaled)."),
 ("9.2","9","A","T1D insulin","Prefer insulin analogs (or inhaled insulin) over human insulin in T1D to reduce hypoglycemia."),
 ("9.3","9","B","T1D education","Teach carb/fat/protein-matched mealtime dosing, correction doses, trend-based adjustment, sick-day and exercise management."),
 ("9.4","9","E","Insulin review","Reassess insulin plan and insulin-taking behavior every 3-6 months."),
 ("9.5","9","E","T2D drug choice","Use shared decision-making; weigh efficacy, CV/kidney/weight effects, hypoglycemia, cost/access, tolerability, preference."),
 ("9.6","9","A","T2D combination","Consider initial combination therapy to reach goals sooner."),
 ("9.7","9","A","ASCVD","T2D with ASCVD or high ASCVD risk: include GLP-1 RA and/or SGLT2i with proven CV benefit irrespective of A1C."),
 ("9.8","9","A","Heart failure","T2D with HF (HFrEF or HFpEF): SGLT2i irrespective of A1C."),
 ("9.9a","9","A","HFpEF","T2D + obesity + symptomatic HFpEF: dual GIP/GLP-1 RA (tirzepatide) with proven benefit."),
 ("9.9b","9","B","HFpEF","T2D + obesity + symptomatic HFpEF: GLP-1 RA (semaglutide) with proven symptom/HF-event benefit."),
 ("9.10","9","A","CKD","T2D with CKD (eGFR 20-60 and/or albuminuria): SGLT2i or GLP-1 RA with proven benefit. SGLT2i glucose-lowering weaker at eGFR <45."),
 ("9.11","9","B","Advanced CKD","eGFR <30: GLP-1 RA preferred (low hypoglycemia, CV benefit). Dialysis: GLP-1-based therapy not dependent on kidney clearance can be started/continued (grade C)."),
 ("9.12","9","A/B","MASLD","T2D + MASLD + overweight/obesity: GLP-1 RA with MASH benefit (A) or dual GIP/GLP-1 RA (B)."),
 ("9.13a","9","A/B","MASH","Biopsy-proven MASH or high fibrosis risk: GLP-1 RA preferred (A); pioglitazone or dual GIP/GLP-1 RA can be considered (B)."),
 ("9.13b","9","B","MASH","Pioglitazone + GLP-1 RA combination can be considered in MASH/high fibrosis risk."),
 ("9.14","9","E","Review","Re-evaluate medication plan and taking behavior every 3-6 months."),
 ("9.15","9","A","Therapeutic inertia","Do not delay intensification/deintensification when goals are unmet."),
 ("9.16","9","A","Modification","Choose changes by glycemic and weight goals, comorbidities and hypoglycemia risk."),
 ("9.17","9","A","Hypoglycemia","When adding a new agent, reassess need/dose of sulfonylureas, meglitinides and insulin."),
 ("9.18","9","B","Combination","Do not combine DPP-4 inhibitor with GLP-1 RA or dual GIP/GLP-1 RA (no added benefit)."),
 ("9.19","9","A","Weight","If weight goals unmet add weight-management interventions (lifestyle, programs, drugs, metabolic surgery)."),
 ("9.20","9","E","Insulin start","Consider insulin regardless of background therapy if symptomatic hyperglycemia, A1C >10% (>86 mmol/mol) or glucose >=300 mg/dL (>=16.7 mmol/L)."),
 ("9.21","9","A","GLP-1 vs insulin","Without severe hyperglycemia/crisis, prefer GLP-1-based therapy over insulin for initial or add-on injectable."),
 ("9.22","9","A","Insulin+GLP-1","If insulin is used, combine with GLP-1 RA/dual agonist; reassess insulin dose when GLP-1 RA is added or escalated."),
 ("9.23","9","A","Insulin start","When starting insulin continue other glucose-lowering agents unless contraindicated/not tolerated."),
 ("9.24","9","A","Foundations","Healthy behaviors, DSMES, avoiding therapeutic inertia and SDOH are essential parts of every glucose-lowering plan."),
 ("9.25","9","A/B","CGM","Offer CGM at onset and any time to adults on insulin (A), on hypoglycemia-causing non-insulin drugs (B), or when CGM aids management (B)."),
 ("9.26","9","E","Overbasalization","Watch for bedtime-to-morning or post- to pre-prandial glucose differential, hypoglycemia, variability; re-evaluate promptly."),
 ("9.27","9","A","AID","Offer automated insulin delivery to adults with T1D or T2D on insulin per preference."),
 ("9.28","9","A/B","Glucagon","Prescribe glucagon to everyone on insulin or at high hypoglycemia risk; teach family/caregivers; prefer no-reconstitution products (B)."),
 ("9.29","9","E","Cost","Routinely screen for financial barriers and act to reduce cost."),
 ("9.30","9","E","Cost","With cost barriers consider lower-cost drugs (metformin, sulfonylurea, TZD, human insulin) weighing their risks."),
 ("9.31a","9","C","Compounded drugs","Do not use non-FDA-approved compounded products (incl. incretins)."),
 ("9.31b","9","E","Shortage","If a drug is unavailable switch to another approved agent with similar efficacy."),
 ("9.31c","9","E","Shortage","When supply returns reassess whether to resume original drug."),
 ("9.32a","9","A/C","Pregnancy","Counsel people of childbearing potential on contraception and drug effects on contraceptive efficacy."),
 ("9.32b","9","A/E","Preconception","Shared preconception planning: glycemic goals, timing of stopping non-insulin drugs, optimal glycemic management."),
 ("9.33","9","C","Immunotherapy","Hyperglycemia on PD-1/PD-L1 inhibitors: assess urgently for insulin need (DKA risk)."),
 ("9.34","9","E","mTOR inhibitors","Metformin first-line for mTOR-inhibitor hyperglycemia."),
 ("9.35a","9","E","PI3K inhibitors","Metformin first-line for PI3K-alpha inhibitor hyperglycemia."),
 ("9.35b","9","E","PI3K inhibitors","Reserve insulin for severe hyperglycemia/crisis in PI3K-inhibitor therapy."),
 ("9.36","9","C","Glucocorticoids","Match glucose-lowering therapy to the steroid regimen; reassess frequently."),
 ("9.37","9","A","Transplant","Post-transplant diabetes/T2D: insulin preferred postoperatively; DPP-4i for mild hyperglycemia."),
 ("9.38a","9","C","Transplant","Non-insulin agents usable long term; choice depends on organ."),
 ("9.38b","9","C","Transplant","GLP-1 RA can be considered long term for cardiometabolic benefit."),
 ("9.38c","9","C","Transplant","Add insulin if goals not met with non-insulin therapy."),
 ("9.39","9","E","SGLT ketoacidosis","Educate at-risk SGLT-inhibitor users on DKA signs and mitigation, give ketone (beta-hydroxybutyrate) testing tools, discourage ketogenic diets."),
 # Section 5
 ("5.1","5","A","DSMES","Advise all people with diabetes to participate in DSMES."),
 ("5.2","5","E","DSMES","Provide DSMES at diagnosis, annually/when goals unmet, when complications arise, and at life/care transitions."),
 ("5.3","5","C","DSMES","Assess outcomes, health status and well-being on an individual timeframe."),
 ("5.4","5","A","Behavior","Use motivational interviewing, goal setting and problem-solving."),
 ("5.5","5","A","DSMES","Culturally/socially appropriate group or individual DSMES; share participation with the care team."),
 ("5.6","5","B","DSMES","Offer DSMES via telehealth/digital interventions."),
 ("5.7","5","B","DSMES","DSMES improves outcomes and reduces cost: payor reimbursement recommended."),
 ("5.8","5","E","DSMES","Identify and address barriers to DSMES."),
 ("5.9","5","C","SDOH","Assess social determinants to design DSMES."),
 ("5.10","5","A","MNT","Refer to a registered dietitian (RDN) for individualized MNT."),
 ("5.11","5","B/A/E","MNT","MNT saves cost and improves cardiometabolic outcomes: should be reimbursed."),
 ("5.12","5","A","Weight","Overweight/obesity: treatment plan aiming for at least 5-7% weight loss."),
 ("5.13","5","B","Meal plan","Individualized meal plans considering nutrient quality, calories, metabolic goals."),
 ("5.14","5","B","Eating pattern","Emphasize non-starchy vegetables, whole fruit, legumes, lean protein, whole grains, nuts/seeds, low-fat dairy; minimize red meat, sugary drinks, sweets, refined grains, ultra-processed food."),
 ("5.15","5","B","Carbohydrate","Consider reducing carbohydrate in some adults, best by limiting processed foods."),
 ("5.16","5","C","Supplements","Micronutrient or herbal supplements (magnesium, chromium, cinnamon, aloe) not recommended for glycemia; ask about use."),
 ("5.17","5","B","Supplements","Counsel against beta-carotene supplements."),
 ("5.18","5","B","Alcohol","Do not exceed recommended limits (<=1 drink/day women, <=2 men); abstainers should not start."),
 ("5.19","5","B","Alcohol","Counsel on delayed hypoglycemia and glucose monitoring after alcohol, esp. on insulin/secretagogues."),
 ("5.20","5","B","Sodium","Limit sodium to <2,300 mg/day as clinically appropriate."),
 ("5.21","5","A","Beverages","Encourage water over other beverages."),
 ("5.22","5","B","Sweeteners","Non-nutritive sweeteners acceptable in moderation, short term, in place of sugar."),
 ("5.23","5","E","Weight loss","Monitor nutrition adequacy (protein, micronutrients) during intentional weight loss."),
 ("5.24","5","B","Fiber","Choose minimally processed, high-fiber carbohydrate (>=14 g fiber per 1,000 kcal)."),
 ("5.25","5","B","Beverages","Replace sugar-sweetened drinks (incl. juices) with water/low- or no-calorie drinks."),
 ("5.26","5","E","SGLT ketoacidosis","SGLT-inhibitor users: ketoacidosis education, ketone tools, avoid ketogenic eating."),
 ("5.27","5","A/B","Insulin dosing","Teach glycemic impact of carbohydrate, fat and protein for mealtime insulin dosing."),
 ("5.28","5","B","Fixed insulin","Fixed-dose insulin: keep consistent carbohydrate timing/amount."),
 ("5.29","5","B","Protein","More plant-based protein (nuts, seeds, legumes)."),
 ("5.30","5","A/B","Mediterranean","Consider Mediterranean-style eating pattern."),
 ("5.31","5","B","Fat","Limit saturated fat."),
 ("5.32","5","B","Fasting","Religious fasting: use IDF-DAR risk assessment and fasting-focused education."),
 ("5.33","5","B","Fasting","Assess and optimize treatment plan, dose and timing well before fasting."),
 ("5.34","5","B/C","Activity","Assess baseline activity/sedentary time; encourage increase; break sitting every 30 min."),
 ("5.35","5","C/B","Activity","Children/adolescents: >=60 min/day moderate-vigorous activity, strengthening >=3 days/week, limit screen time."),
 ("5.36","5","C/B","Activity","Adults: >=150 min/week moderate-vigorous aerobic over >=3 days, no >2 consecutive inactive days (75 min vigorous may suffice if fit)."),
 ("5.37","5","C/B","Activity","Resistance exercise 2-3 sessions/week on non-consecutive days."),
 ("5.38","5","C","Activity","Older adults: flexibility and balance training 2-3 times/week."),
 ("5.39","5","C","Activity","On obesity drugs/after metabolic surgery: prioritize muscle-strengthening to preserve lean mass."),
 ("5.40","5","A","Tobacco","Ask about tobacco/vaping every visit; advise complete avoidance; provide counseling + pharmacotherapy."),
 ("5.41","5","C/E","Cannabis","T1D and others at DKA risk: advise against recreational cannabis."),
 ("5.42","5","A","Psychosocial","Provide psychosocial care to all people with diabetes."),
 ("5.43","5","C","Psychosocial","Screen at least annually and with changes in health/treatment/life."),
 ("5.44","5","B","Psychosocial","Refer to behavioral health professionals when indicated."),
 ("5.45","5","B","Distress","Screen for diabetes distress at least annually."),
 ("5.46","5","B","Anxiety","Screen for anxiety annually."),
 ("5.47","5","E/A","Fear of hypoglycemia","Screen those at high hypoglycemia risk annually; refer for evidence-based intervention."),
 ("5.48","5","B/A","Depression","Screen for depression at least annually."),
 ("5.49","5","B","Depression","Rescreen at complication diagnosis or major change in status."),
 ("5.50","5","B","Disordered eating","Screen with validated tools; review treatment for effects on hunger/intake."),
 ("5.51","5","B","Disordered eating","Reevaluate treatment plan with a qualified professional if disordered eating is present."),
 ("5.52","5","B","Serious mental illness","Provide enhanced monitoring/support for diabetes self-management."),
 ("5.53","5","C","Antipsychotics","Monitor weight, glycemia, lipids on second-generation antipsychotics."),
 ("5.54","5","B","Cognition","Monitor cognitive capacity across the life span."),
 ("5.55","5","E","Cognition","Refer for formal assessment if cognition suboptimal for self-management."),
 ("5.56","5","B","Sleep","Screen sleep health and sleep disorders; refer as needed."),
 ("5.57","5","A","Sleep","Counsel on sleep-promoting routines."),
 # Section 3
 ("3.1","3","E","Prediabetes","Monitor prediabetes for progression at least annually."),
 ("3.2","3","E","Presymptomatic T1D","A1C about every 6 months and 75-g OGTT annually."),
 ("3.3","3","A","DPP","Refer overweight/obese high-risk adults to a diabetes prevention program: >=5-7% weight loss, >=150 min/week activity."),
 ("3.4","3","B","Eating pattern","Prescribe evidence-based eating pattern (e.g., Mediterranean, low-carbohydrate) in prediabetes."),
 ("3.5","3","A/E","DPP","Offer DPP to high-risk adults; payors should cover."),
 ("3.6","3","B","DPP","Certified technology-assisted DPPs are an option."),
 ("3.7","3","A","Metformin prevention","Consider metformin for high risk: age 25-59, BMI >=35, FPG >=110 mg/dL, A1C >=6.0%, or prior GDM."),
 ("3.8","3","B","PI3K inhibitors","Consider metformin to prevent hyperglycemia on PI3K-alpha inhibitors."),
 ("3.9","3","B","Glucocorticoids","Consider metformin to prevent hyperglycemia in high-risk people on high-dose glucocorticoids."),
 ("3.10","3","B","B12","Periodically check vitamin B12 on long-term metformin (esp. anemia/neuropathy)."),
 ("3.11","3","B","CV risk","Prediabetes raises CV risk: screen and treat modifiable risk factors."),
 ("3.12","3","B","Statins","Statins may raise diabetes risk: monitor glucose, reinforce prevention, do not stop statins for this reason."),
 ("3.13","3","A/C","Pioglitazone","Prior stroke + insulin resistance/prediabetes: pioglitazone may be considered; weigh weight gain, edema, fractures."),
 ("3.14","3","B","Goals","Care goals: weight loss/maintenance, limit glycemic progression, CV risk attention."),
 ("3.15","3","A","Pharmacotherapy","Consider pharmacotherapy to support person-centered goals."),
 ("3.16","3","A","High risk","More intensive prevention if BMI >=35, FPG 110-125, 2-h glucose 173-199, A1C >=6.0%, or prior GDM."),
 ("3.17","3","B","Teplizumab","Discuss teplizumab with selected people aged >=8 years with stage 2 T1D."),
]

# ---------------- PATIENT DATA DICTIONARY ----------------
FIELDS = [
 ("diabetes_type","enum","type1|type2|prediabetes|presymptomatic_t1d|other|unknown"),
 ("age","number","years"),("sex_childbearing_potential","bool",""),
 ("a1c","number","%"),("a1c_goal","number","% individualized"),("random_glucose","number","mg/dL"),
 ("fasting_glucose","number","mg/dL"),("bmi","number","kg/m2"),("obesity","bool",""),
 ("egfr","number","mL/min/1.73m2"),("albuminuria","bool","ACR >=30 mg/g"),
 ("ascvd","bool",""),("high_cv_risk","bool","age>=55 + >=2 risk factors"),
 ("heart_failure","bool",""),("hf_type","enum","HFrEF|HFpEF"),
 ("masld","bool",""),("mash_or_high_fibrosis_risk","bool",""),("decompensated_cirrhosis","bool",""),
 ("pancreatitis_history","bool",""),("gastroparesis","bool",""),("gallbladder_disease","bool",""),
 ("dka_history","bool",""),("insulin_deficient","bool","T1D/LADA or insulin-deficient T2D"),
 ("symptomatic_hyperglycemia","bool","polyuria/polydipsia"),("catabolic_features","bool","weight loss/ketosis/hypertriglyceridemia"),
 ("on_insulin","bool",""),("on_sulfonylurea","bool",""),("on_meglitinide","bool",""),("on_glp1ra","bool",""),
 ("on_dual_gip_glp1","bool",""),("on_dpp4i","bool",""),("on_sglt2i","bool",""),("on_pioglitazone","bool",""),
 ("on_metformin","bool",""),("metformin_years","number",""),("on_oral_contraceptive","bool",""),
 ("planning_pregnancy","bool",""),("pregnant","bool",""),("hypoglycemia_risk_high","bool",""),
 ("cost_barrier","bool",""),("fasting_planned","bool","religious fasting"),
 ("very_low_carb_or_keto_diet","bool",""),("heavy_alcohol_use","bool",""),("alcohol_use","bool",""),
 ("tobacco_or_vaping","bool",""),("cannabis_use","bool",""),("disordered_eating","bool",""),
 ("on_glucocorticoid_high_dose","bool",""),("on_immune_checkpoint_inhibitor","bool",""),
 ("on_pi3k_inhibitor","bool",""),("on_mtor_inhibitor","bool",""),("transplant_recipient","bool",""),
 ("on_statin","bool",""),("prior_stroke_insulin_resistant","bool",""),("history_gdm","bool",""),
 ("bladder_cancer_active_or_prior","bool",""),("fracture_risk","bool",""),("retinopathy_high_risk","bool","older/long duration >=10 y"),
 ("chronic_lung_disease","bool","asthma/COPD"),("smoker_current_or_recent","bool",""),
 ("on_antipsychotic_sga","bool",""),("surgery_planned","bool",""),("anemia_or_neuropathy","bool",""),
 ("food_insecurity","bool",""),("sedentary","bool",""),("sleep_problem","bool",""),("shift_work","bool",""),
]

# ---------------- DRUG CLASSES ----------------
CLASSES = [
 dict(id="METFORMIN",name="Biguanide (metformin)",route="oral",glucose_efficacy="high",hypoglycemia_risk="no",weight="neutral (modest loss possible)",
      mace="potential benefit",hf="neutral",ckd_progression="neutral",mash="neutral",
      renal={"contraindicated_below_egfr":30,"do_not_initiate_below_egfr":45,"reduce_dose_below_egfr":45},
      adverse=["GI intolerance (bloating, abdominal discomfort, diarrhea): slow titration, extended-release, take with food","Vitamin B12 deficiency: periodic B12 testing","Lactic acidosis very rare, mainly eGFR <30 or overdose/acute kidney injury"],
      monitoring=["eGFR before and during treatment","Vitamin B12 periodically (annually if >4 years or at risk)"],
      notes="Historically first-line; inexpensive; IR twice daily or ER once daily."),
 dict(id="SGLT2I",name="SGLT2 inhibitors",route="oral",glucose_efficacy="intermediate to high",hypoglycemia_risk="no",weight="loss (intermediate)",
      mace="benefit: canagliflozin, empagliflozin",hf="benefit: canagliflozin, dapagliflozin, empagliflozin, ertugliflozin",
      ckd_progression="benefit: canagliflozin, empagliflozin, dapagliflozin",mash="unknown",
      renal={"start_for_cv_kidney_benefit_if_egfr_above":20,"minimal_glucose_lowering_below_egfr":45,"continue_until_dialysis":True},
      adverse=["DKA incl. euglycemic (rare in T2D; contraindicated in T1D use; avoid after DKA)","Genital mycotic infections","UTI/urosepsis/pyelonephritis","Fournier gangrene (rare)","Volume depletion/low BP","Stop 3-4 days before scheduled surgery, during critical illness or prolonged fasting"],
      monitoring=["eGFR/volume status at start","Ketone testing tools (beta-hydroxybutyrate) if DKA risk"],
      notes="Use for HF, CKD, ASCVD irrespective of A1C. Avoid ketogenic/very-low-carb diets and heavy alcohol."),
 dict(id="GLP1RA",name="GLP-1 receptor agonists",route="SC (semaglutide also oral)",glucose_efficacy="high to very high",hypoglycemia_risk="no",weight="loss (intermediate to very high)",
      mace="benefit: dulaglutide, liraglutide, semaglutide (SC and oral); neutral: exenatide QW, lixisenatide",hf="benefit: semaglutide (SC) in HFpEF with obesity",
      ckd_progression="benefit for kidney endpoints: dulaglutide, liraglutide, semaglutide; semaglutide SC shown to slow CKD progression",mash="benefit: semaglutide (SC)",
      renal={"no_dose_adjustment":["dulaglutide","liraglutide","semaglutide"],"avoid_lixisenatide_egfr_at_or_below":30,"avoid_exenatide_crcl_at_or_below":30},
      adverse=["Nausea/vomiting/diarrhea (esp. at start and dose increases): smaller meals, stop eating when full, avoid high-fat/spicy food, slower titration","Pancreatitis reported (do not start if high risk; stop if suspected)","Gallbladder disease","Retinopathy monitoring in high-risk","NAION (rare)","Thyroid C-cell tumors in rodents (human relevance undetermined); check product label","Hold before procedures (aspiration risk with anesthesia/sedation)","May impair absorption of oral drugs incl. oral contraceptives during titration","Not recommended in gastroparesis"],
      monitoring=["Kidney function if severe GI effects","Eye exam in retinopathy high-risk","Weight, GI tolerance"],
      notes="Preferred over insulin as first injectable when no severe hyperglycemia. Do not combine with DPP-4i."),
 dict(id="TIRZEPATIDE",name="Dual GIP/GLP-1 RA (tirzepatide)",route="SC weekly",glucose_efficacy="very high",hypoglycemia_risk="no",weight="loss (very high)",
      mace="under investigation",hf="benefit in HFpEF with obesity",ckd_progression="potential benefit",mash="potential benefit",
      renal={"no_dose_adjustment":True},
      adverse=["GI effects as for GLP-1 RA","Reduces oral contraceptive exposure: use a second contraceptive method on start/each dose increase until maintenance dose used >=4 weeks","Same class warnings as GLP-1 RA (pancreatitis, gallbladder, retinopathy, aspiration)"],
      monitoring=["Kidney function if severe GI effects","Weight"],notes="Highest glucose and weight efficacy with semaglutide."),
 dict(id="DPP4I",name="DPP-4 inhibitors",route="oral",glucose_efficacy="intermediate",hypoglycemia_risk="no",weight="neutral",
      mace="neutral (potential risk: saxagliptin)",hf="neutral (saxagliptin potential risk)",ckd_progression="unknown",mash="neutral",
      renal={"dose_adjust":["sitagliptin","saxagliptin","alogliptin"],"no_adjustment":["linagliptin"]},
      adverse=["Pancreatitis reported (stop if suspected)","Joint pain (consider stopping if debilitating)","Bullous pemphigoid (stop if suspected)"],monitoring=[],
      notes="Never combine with GLP-1 RA or dual agonist. Can be used for mild post-transplant hyperglycemia."),
 dict(id="TZD",name="Thiazolidinedione (pioglitazone)",route="oral",glucose_efficacy="high",hypoglycemia_risk="no",weight="gain",
      mace="potential benefit",hf="INCREASED RISK",ckd_progression="neutral",mash="potential benefit",
      renal={"no_dose_adjustment":True,"generally_not_recommended_in_kidney_impairment":True},
      adverse=["Fluid retention/HF: do not use in HF","Fractures","Bladder cancer: avoid in active; caution in prior","Weight gain/edema","Low dose may be better tolerated"],monitoring=["Edema, weight, HF symptoms"],
      notes="Option for MASH (alone or with GLP-1 RA) and post-stroke insulin resistance."),
 dict(id="SU",name="Sulfonylureas (2nd generation)",route="oral",glucose_efficacy="high",hypoglycemia_risk="yes",weight="gain",
      mace="neutral",hf="neutral",ckd_progression="neutral",mash="neutral",
      renal={"glyburide_generally_not_recommended_in_ckd":True},
      adverse=["Hypoglycemia (esp. with insulin, CKD, older age)","Weight gain","Glimepiride shown CV-safe; glyburide avoid in CKD; start glipizide/glimepiride conservatively"],monitoring=["Hypoglycemia symptoms, CGM/SMBG"],
      notes="Low cost; reduce/stop when adding GLP-1 RA, SGLT2i or insulin."),
 dict(id="INSULIN_HUMAN",name="Human insulin (regular, NPH, premixed 70/30)",route="SC (regular also inhaled)",glucose_efficacy="high to very high",hypoglycemia_risk="yes (higher than analogs)",weight="gain",
      mace="neutral",hf="neutral",ckd_progression="neutral",mash="neutral",renal={"lower_doses_with_falling_egfr":True},
      adverse=["Hypoglycemia (nocturnal with NPH; delayed post-meal with regular)","Weight gain","Injection-site reactions/lipohypertrophy"],monitoring=["SMBG/CGM","Injection sites"],notes="Least costly insulins."),
 dict(id="INSULIN_ANALOG",name="Insulin analogs (basal long-acting, rapid, ultra-rapid) and inhaled insulin",route="SC; inhaled option",glucose_efficacy="high to very high",hypoglycemia_risk="yes (lower than human)",weight="gain",
      mace="neutral",hf="neutral",ckd_progression="neutral",mash="neutral",renal={"lower_doses_with_falling_egfr":True},
      adverse=["Hypoglycemia","Weight gain","Overbasalization","Inhaled insulin: FEV1 decline; contraindicated in chronic lung disease; not for smokers/recent quitters; spirometry before and after start"],monitoring=["SMBG/CGM","Spirometry (inhaled)"],
      notes="Preferred in T1D. Degludec/glargine U-300 lower nocturnal hypoglycemia than glargine U-100."),
 dict(id="OTHER",name="Other agents (alpha-glucosidase inhibitors, meglitinides, bile acid sequestrant, bromocriptine, pramlintide)",route="oral/SC",glucose_efficacy="low to intermediate",hypoglycemia_risk="meglitinides yes",weight="neutral/modest",
      mace="unknown",hf="unknown",ckd_progression="unknown",mash="unknown",renal={},adverse=["Meglitinides: hypoglycemia, weight gain","Pramlintide: approved in T1D, A1C -0.3-0.4%"],monitoring=[],notes="Add-on options if preferred drugs unavailable/not tolerated."),
]

# ---------------- DRUGS (Table 9.3, US cost) ----------------
# (class, generic, strength/form, max daily dose, AWP, NADAC)
DRUGS = [
 ("METFORMIN","metformin IR","500 mg","2,000 mg (850 mg tab: 2,550 mg)",85,2),
 ("METFORMIN","metformin ER","500 mg / 1,000 mg","2,000 mg",89,3),
 ("SU","glimepiride","4 mg","8 mg",73,2),
 ("SU","glipizide IR","10 mg","40 mg",72,6),
 ("SU","glipizide XL/ER","10 mg","20 mg",48,9),
 ("SU","glyburide micronized","6 mg","12 mg",54,13),
 ("TZD","pioglitazone","45 mg","45 mg",348,4),
 ("OTHER","acarbose","100 mg","300 mg",106,22),
 ("OTHER","miglitol","100 mg","300 mg",294,183),
 ("OTHER","nateglinide","120 mg","360 mg",104,16),
 ("OTHER","repaglinide","2 mg","16 mg",878,28),
 ("DPP4I","alogliptin","25 mg","25 mg",234,143),
 ("DPP4I","linagliptin","5 mg","5 mg",630,504),
 ("DPP4I","saxagliptin","5 mg","5 mg",524,179),
 ("DPP4I","sitagliptin","100 mg","100 mg",341,303),
 ("SGLT2I","bexagliflozin","20 mg","20 mg",47,None),
 ("SGLT2I","canagliflozin","300 mg","300 mg",718,575),
 ("SGLT2I","dapagliflozin","10 mg","10 mg",664,345),
 ("SGLT2I","empagliflozin","25 mg","25 mg",629,604),
 ("SGLT2I","ertugliflozin","15 mg","15 mg",428,343),
 ("GLP1RA","dulaglutide","4.5 mg pen weekly","4.5 mg weekly",1185,953),
 ("GLP1RA","liraglutide","18 mg/3 mL pen daily","1.8 mg daily",929,577),
 ("GLP1RA","semaglutide SC","2 mg pen weekly","2 mg weekly",1197,966),
 ("GLP1RA","semaglutide oral","14 mg tablet daily","14 mg daily",1197,965),
 ("TIRZEPATIDE","tirzepatide","15 mg pen weekly","15 mg weekly",1296,1041),
 ("OTHER","colesevelam","625 mg tab","3.75 g",692,56),
 ("OTHER","bromocriptine","0.8 mg","4.8 mg",1188,957),
]
# Insulin cost per 1,000 units (AWP, NADAC)
INSULIN_COST = [
 ("aspart U-100 vial",87,70),("aspart U-100 pen",112,90),("lispro U-100 vial",30,24),("lispro U-100 pen",127,102),
 ("inhaled insulin cartridges",1578,1265),("regular human U-100 vial",56,44),("NPH human U-100 vial",58,45),
 ("NPH/regular 70/30 vial",56,45),("glargine U-100 vial",77,62),("glargine U-100 pen",77,62),("glargine U-300 pen",152,122),
 ("degludec pen",142,114),("degludec/liraglutide fixed-ratio pen (per 1,000 units basis as listed)",1073,859),
 ("glargine/lixisenatide fixed-ratio pen",713,571),
]

# ---------------- INSULIN DOSING PARAMETERS ----------------
INSULIN_RULES = [
 ("T1D total daily dose","Typical 0.4-1 unit/kg/day; 0.5 unit/kg/day typical start in metabolically stable adults; newly diagnosed adults 0.2-0.6 unit/kg/day; higher in puberty, late luteal phase, illness.","9 (Insulin therapy T1D)"),
 ("T1D basal share","About 30-50% of TDD basal, remainder prandial.","9 Table 9.1"),
 ("T2D basal start","Start 10 units/day or 0.1-0.2 unit/kg/day.","9 Fig 9.5; text"),
 ("T2D basal titration","Choose evidence-based algorithm, e.g., increase 2 units every 3 days to reach fasting glucose goal without hypoglycemia. If hypoglycemia: find cause; if none, lower dose 10-20%.","9 Fig 9.5"),
 ("T2D prandial start","4 units or 10% of basal dose with the largest meal / greatest post-meal excursion; then stepwise add doses.","9 Fig 9.5"),
 ("T2D prandial titration","Increase 1-2 units or 10-15% twice weekly; for hypoglycemia determine cause, else reduce 10-20%.","9 Fig 9.5"),
 ("Basal switching","Often unit-for-unit; reduce 10-20% when tight control/high hypoglycemia risk and when switching from NPH or U-300 glargine.","9 Basal insulin"),
 ("NPH to twice daily","One approach: total NPH = 80% of current bedtime dose, 2/3 morning and 1/3 bedtime.","9 Fig 9.5"),
 ("Overbasalization signals","Bedtime-to-morning glucose differential >=50 mg/dL (>=2.8 mmol/L), postprandial-to-preprandial differential, hypoglycemia, high variability: reassess and address prandial needs.","9"),
 ("Large prandial additions","When adding substantial prandial insulin (esp. evening) consider reducing basal.","9"),
 ("Needle length","4-mm pen needles lower risk of intramuscular injection; rotate sites; avoid lipohypertrophy.","9 Administration"),
 ("Starting insulin in T2D","Indications: symptoms, A1C >10%, glucose >=300 mg/dL, catabolism; consider GLP-1 RA first otherwise; continue metformin/SGLT2i/GLP-1 RA; limit sulfonylurea/meglitinide/DPP-4i.","9"),
 ("A1C-above-goal combination","If A1C >=1.5% above goal many need dual therapy or a more potent agent; each added oral class lowers A1C ~0.7-1.0%; GLP-1 RA/tirzepatide ~1% to >=2%.","9"),
]

# ---------------- RULES ----------------
def c(field, op, value=True):
    return {"field": field, "op": op, "value": value}

RULES = [
 dict(id="R-T2D-ASCVD",title="ASCVD or high CV risk",rec="9.7",severity="preferred",
   when={"all":[c("diabetes_type","==","type2"),{"any":[c("ascvd","=="),c("high_cv_risk","==")]}]},
   recommend=["GLP1RA (proven CV benefit: dulaglutide, liraglutide, semaglutide)","SGLT2I (proven CV benefit: canagliflozin, empagliflozin)"],
   note="Independent of A1C and of metformin use; consider initial GLP-1 RA + SGLT2i combination.",instructions=["INS-CV-RISK"]),
 dict(id="R-T2D-HF",title="Heart failure",rec="9.8",severity="preferred",
   when={"all":[c("diabetes_type","==","type2"),c("heart_failure","==")]},
   recommend=["SGLT2I (canagliflozin, dapagliflozin, empagliflozin, ertugliflozin)"],avoid=["TZD (pioglitazone)","DPP4I saxagliptin (potential HF risk)"],note="Regardless of A1C.",instructions=["INS-SGLT2I-SICK-DAY"]),
 dict(id="R-T2D-HFPEF-OB",title="Symptomatic HFpEF with obesity",rec="9.9a/9.9b",severity="preferred",
   when={"all":[c("diabetes_type","==","type2"),c("heart_failure","=="),c("hf_type","==","HFpEF"),c("obesity","==")]},
   recommend=["TIRZEPATIDE","GLP1RA semaglutide"],note="Plus SGLT2i for HF.",instructions=["INS-GLP1-TITRATION"]),
 dict(id="R-T2D-CKD",title="CKD eGFR 20-60 and/or albuminuria",rec="9.10",severity="preferred",
   when={"all":[c("diabetes_type","==","type2"),{"any":[c("egfr","between",[20,60]),c("albuminuria","==")]}]},
   recommend=["SGLT2I (empagliflozin, canagliflozin, dapagliflozin)","GLP1RA with CKD benefit (semaglutide first)"],
   note="SGLT2i glucose lowering weak at eGFR <45; still use for kidney/CV benefit if eGFR >=20.",instructions=["INS-KIDNEY-MONITOR"]),
 dict(id="R-T2D-CKD-ADV",title="Advanced CKD eGFR <30",rec="9.11",severity="preferred",
   when={"all":[c("diabetes_type","==","type2"),c("egfr","<",30)]},
   recommend=["GLP1RA (dulaglutide, liraglutide, semaglutide: no dose adjustment)"],avoid=["METFORMIN (contraindicated)","Lixisenatide / exenatide","Glyburide","TZD"],
   note="Insulin/sulfonylurea: high hypoglycemia risk, lower doses, close monitoring.",instructions=["INS-HYPO-RECOGNITION"]),
 dict(id="R-METFORMIN-EGFR-INIT",title="Metformin: do not start if eGFR <45",rec="9 text; Table 9.2",severity="warning",
   when={"all":[c("on_metformin","==",False),c("egfr","<",45)]},avoid=["Start METFORMIN"],note="Do not initiate if eGFR <45."),
 dict(id="R-METFORMIN-EGFR-REDUCE",title="Metformin: reduce dose eGFR <45, stop <30",rec="9 text; Table 9.2",severity="warning",
   when={"all":[c("on_metformin","=="),c("egfr","<",45)]},flags=["Reduce metformin dose when eGFR <45; STOP if eGFR <30."]),
 dict(id="R-METFORMIN-CONTRA",title="Metformin contraindicated eGFR <30",rec="Table 9.2",severity="contraindication",
   when={"all":[c("egfr","<",30)]},avoid=["METFORMIN"]),
 dict(id="R-OBESITY",title="Obesity / weight goal",rec="9 text; 9.19",severity="preferred",
   when={"all":[c("diabetes_type","==","type2"),c("obesity","==")]},
   recommend=["Semaglutide or tirzepatide (highest weight loss)","Then dulaglutide/liraglutide","SGLT2I modest loss"],avoid=["Insulin/sulfonylurea/TZD unless needed (weight gain)"],instructions=["INS-WEIGHT-GOAL","INS-MUSCLE-PRESERVE"]),
 dict(id="R-MASLD",title="MASLD/MASH",rec="9.12/9.13a/9.13b",severity="preferred",
   when={"all":[c("diabetes_type","==","type2"),{"any":[c("masld","=="),c("mash_or_high_fibrosis_risk","==")]}]},
   recommend=["GLP1RA (semaglutide approved for MASH with moderate-advanced fibrosis)","TIRZEPATIDE","Pioglitazone (alone or with GLP-1 RA)"],note="Use insulin if decompensated cirrhosis."),
 dict(id="R-CIRRHOSIS",title="Decompensated cirrhosis",rec="Fig 9.4",severity="warning",
   when={"all":[c("decompensated_cirrhosis","==")]},recommend=["Insulin"]),
 dict(id="R-COMBO-INITIAL",title="Initial combination therapy",rec="9.6",severity="info",
   when={"all":[c("diabetes_type","==","type2"),c("a1c","above_goal_by",1.5)]},
   recommend=["Dual combination or more potent agent (GLP-1 RA/tirzepatide, insulin)"],note="A1C >=1.5% above individualized goal."),
 dict(id="R-INSULIN-START",title="Severe hyperglycemia / catabolic",rec="9.20",severity="warning",
   when={"all":[c("diabetes_type","==","type2"),{"any":[c("a1c",">",10),c("random_glucose",">=",300),c("symptomatic_hyperglycemia","=="),c("catabolic_features","==")]}]},
   recommend=["Consider basal insulin (+/- prandial); add GLP-1 RA/tirzepatide; simplify later as glucotoxicity resolves"],note="Evaluate for T1D if possible.",instructions=["INS-INSULIN-START","INS-HYPO-RECOGNITION","INS-GLUCAGON"]),
 dict(id="R-GLP1-BEFORE-INSULIN",title="Prefer GLP-1 RA before insulin if no severe hyperglycemia",rec="9.21",severity="info",
   when={"all":[c("diabetes_type","==","type2"),c("on_insulin","==",False),c("on_glp1ra","==",False),c("on_dual_gip_glp1","==",False),c("a1c","<=",10)]},
   recommend=["GLP1RA or TIRZEPATIDE before starting insulin"]),
 dict(id="R-INSULIN-GLP1",title="Insulin: combine with GLP-1 RA",rec="9.22",severity="preferred",
   when={"all":[c("on_insulin","=="),c("on_glp1ra","==",False),c("on_dual_gip_glp1","==",False),c("diabetes_type","==","type2")]},
   recommend=["Add GLP1RA/TIRZEPATIDE (fixed-ratio products available)"],note="Reassess insulin dose on GLP-1 RA start/escalation."),
 dict(id="R-INSULIN-KEEP-AGENTS",title="Starting insulin: continue other agents",rec="9.23/9 text",severity="info",
   when={"all":[c("on_insulin","==")]},flags=["Continue metformin, SGLT2i, GLP-1 RA; reduce/stop sulfonylurea, meglitinide, DPP-4i."]),
 dict(id="R-GLUCAGON",title="Glucagon for insulin users",rec="9.28",severity="preferred",
   when={"any":[c("on_insulin","=="),c("hypoglycemia_risk_high","==")]},recommend=["Prescribe glucagon (no-reconstitution product preferred); train family/caregivers"],instructions=["INS-GLUCAGON","INS-HYPO-RECOGNITION"]),
 dict(id="R-CGM",title="CGM",rec="9.25",severity="preferred",
   when={"any":[c("on_insulin","=="),c("on_sulfonylurea","=="),c("on_meglitinide","==")]},recommend=["Offer CGM; consider AID system if on insulin (9.27)"]),
 dict(id="R-DPP4-GLP1",title="DPP-4i + GLP-1 RA",rec="9.18",severity="contraindication",
   when={"all":[c("on_dpp4i","=="),{"any":[c("on_glp1ra","=="),c("on_dual_gip_glp1","==")]}]},avoid=["Concurrent DPP4I with GLP1RA/TIRZEPATIDE"],flags=["Stop DPP-4 inhibitor: no added benefit."]),
 dict(id="R-SU-HYPO",title="Reassess hypoglycemia-prone drugs",rec="9.17",severity="warning",
   when={"all":[{"any":[c("on_sulfonylurea","=="),c("on_meglitinide","==")]},{"any":[c("on_glp1ra","=="),c("on_dual_gip_glp1","=="),c("on_sglt2i","=="),c("on_insulin","==")]}]},
   flags=["When adding a new agent, reassess need/dose of sulfonylurea/meglitinide/insulin to avoid hypoglycemia."]),
 dict(id="R-PANCREATITIS",title="History of pancreatitis",rec="9 (pancreatic diabetes)",severity="contraindication",
   when={"all":[c("pancreatitis_history","==")]},avoid=["GLP1RA","TIRZEPATIDE","DPP4I"],recommend=["Early insulin"]),
 dict(id="R-GASTROPARESIS",title="Gastroparesis",rec="Table 9.2",severity="contraindication",
   when={"all":[c("gastroparesis","==")]},avoid=["GLP1RA","TIRZEPATIDE"]),
 dict(id="R-GALLBLADDER",title="Gallbladder disease",rec="Table 9.2",severity="warning",
   when={"all":[c("gallbladder_disease","==")]},flags=["Avoid GLP-1 RA in at-risk individuals; evaluate if cholelithiasis/cholecystitis suspected."]),
 dict(id="R-RETINOPATHY",title="GLP-1 RA and retinopathy",rec="Table 9.2",severity="warning",
   when={"all":[c("retinopathy_high_risk","=="),{"any":[c("on_glp1ra","=="),c("on_dual_gip_glp1","==")]}]},flags=["Close eye monitoring; monitor for NAION."],instructions=["INS-EYE-EXAM"]),
 dict(id="R-DKA-SGLT",title="DKA risk with SGLT2i",rec="9.39; Section 9 SGLT text",severity="contraindication",
   when={"any":[c("diabetes_type","==","type1"),c("dka_history","=="),c("insulin_deficient","==")]},avoid=["SGLT2I / sotagliflozin"],note="Contraindicated/not approved in T1D; do not use after DKA."),
 dict(id="R-SGLT-KETO",title="SGLT2i + ketogenic/very-low-carb diet, fasting, or heavy alcohol",rec="5.26/9.39",severity="warning",
   when={"all":[c("on_sglt2i","=="),{"any":[c("very_low_carb_or_keto_diet","=="),c("heavy_alcohol_use","=="),c("fasting_planned","==")]}]},
   flags=["Avoid ketogenic/very-low-carb eating and excess alcohol; ensure hydration; provide ketone testing; do not start SGLT2i close to fasting days."],instructions=["INS-SGLT2I-KETONE","INS-SGLT2I-SICK-DAY"]),
 dict(id="R-SGLT-SURGERY",title="SGLT2i before surgery",rec="Table 9.2",severity="warning",
   when={"all":[c("on_sglt2i","=="),c("surgery_planned","==")]},flags=["Stop SGLT2i 3-4 days before scheduled surgery."]),
 dict(id="R-GLP1-SURGERY",title="GLP-1 RA before anesthesia",rec="Table 9.2",severity="warning",
   when={"all":[{"any":[c("on_glp1ra","=="),c("on_dual_gip_glp1","==")]},c("surgery_planned","==")]},flags=["Give peri-procedural guidance on holding (aspiration risk)."]),
 dict(id="R-TZD-HF",title="Pioglitazone in HF",rec="Table 9.2",severity="contraindication",
   when={"all":[c("heart_failure","=="),c("on_pioglitazone","==")]},avoid=["Pioglitazone"],flags=["Pioglitazone increases HF risk: do not use."]),
 dict(id="R-TZD-BLADDER",title="Pioglitazone and bladder cancer/fractures",rec="Table 9.2",severity="warning",
   when={"any":[c("bladder_cancer_active_or_prior","=="),c("fracture_risk","==")]},flags=["Avoid pioglitazone in active bladder cancer; caution prior history; fracture risk."]),
 dict(id="R-INHALED-LUNG",title="Inhaled insulin and lung disease",rec="Section 9 text",severity="contraindication",
   when={"any":[c("chronic_lung_disease","=="),c("smoker_current_or_recent","==")]},avoid=["Inhaled insulin"],flags=["Spirometry (FEV1) needed before/after starting inhaled insulin."]),
 dict(id="R-COST",title="Cost barrier",rec="9.29/9.30",severity="info",
   when={"all":[c("cost_barrier","==")]},recommend=["Metformin","Sulfonylurea (glimepiride/glipizide; avoid glyburide in CKD)","Pioglitazone","Human insulin (regular/NPH/70-30)"],note="Weigh hypoglycemia, weight gain, CV/kidney risk of cheaper drugs."),
 dict(id="R-COMPOUNDED",title="Shortage / compounded incretins",rec="9.31a-c",severity="warning",
   when={"all":[c("diabetes_type","!=","none")]},flags=["Do not prescribe/accept compounded semaglutide/tirzepatide; switch to approved alternative in shortage and reassess later."],instructions=["INS-NO-COMPOUNDED"],always=True),
 dict(id="R-CONTRACEPTION-TIRZ",title="Tirzepatide and oral contraceptives",rec="9.32a",severity="warning",
   when={"all":[c("on_dual_gip_glp1","=="),c("on_oral_contraceptive","==")]},flags=["Use second contraceptive method until maintenance dose reached and used >=4 weeks (and after dose escalations)."],instructions=["INS-CONTRACEPTION"]),
 dict(id="R-CHILDBEARING",title="Childbearing potential counseling",rec="9.32a/b",severity="info",
   when={"all":[c("sex_childbearing_potential","=="),{"any":[c("planning_pregnancy","=="),c("pregnant","==")]}]},flags=["Review all drugs for pregnancy safety; preconception planning several months ahead; use pregnancy-approved therapy (see Section 15)."],instructions=["INS-CONTRACEPTION"]),
 dict(id="R-ICI",title="Immune checkpoint inhibitor hyperglycemia",rec="9.33",severity="warning",
   when={"all":[c("on_immune_checkpoint_inhibitor","=="),c("random_glucose",">",250)]},recommend=["Assess for immediate insulin (consider basal insulin if glucose >250 mg/dL); do not stop ICI"],flags=["DKA risk; usually lifelong insulin"]),
 dict(id="R-PI3K",title="PI3K-alpha inhibitor hyperglycemia",rec="9.35a/9.35b/3.8",severity="info",
   when={"all":[c("on_pi3k_inhibitor","==")]},recommend=["Metformin first-line (consider prophylactic start 1 week before)","Pioglitazone or SGLT2i (monitor ketoacidosis) next"],avoid=["Insulin/sulfonylurea except last resort","GLP-1 RA"]),
 dict(id="R-MTOR",title="mTOR inhibitor hyperglycemia",rec="9.34",severity="info",
   when={"all":[c("on_mtor_inhibitor","==")]},recommend=["Metformin first-line","Pioglitazone second-line","Insulin if refractory/severe"]),
 dict(id="R-STEROID",title="Glucocorticoid hyperglycemia",rec="9.36/3.9",severity="info",
   when={"all":[c("on_glucocorticoid_high_dose","==")]},recommend=["Insulin most used (match timing; NPH morning for AM prednisone); sulfonylurea/meglitinide alternatives","Metformin prophylaxis in high-risk (Sec 3)"],flags=["Monitor afternoon/evening glucose, not only fasting; adjust as steroid tapers."],instructions=["INS-STEROID-GLUCOSE"]),
 dict(id="R-TRANSPLANT",title="Transplant recipient",rec="9.37-9.38c",severity="info",
   when={"all":[c("transplant_recipient","==")]},recommend=["Early postoperative: insulin; mild: DPP-4i","Long term: GLP-1 RA, SGLT2i (UTI risk), metformin (eGFR >=45 to start; stop <30)"]),
 dict(id="R-SGA",title="Second-generation antipsychotics",rec="5.53",severity="info",
   when={"all":[c("on_antipsychotic_sga","==")]},flags=["Monitor weight, glucose, lipids every 12-16 weeks."]),
 dict(id="R-B12",title="Metformin B12 monitoring",rec="3.10",severity="info",
   when={"any":[c("metformin_years",">",4),c("anemia_or_neuropathy","==")]},flags=["Check vitamin B12 (annually if >4 years metformin or at risk)."],instructions=["INS-B12"]),
 dict(id="R-PRED-MET",title="Prediabetes: metformin consideration",rec="3.7/3.16",severity="info",
   when={"all":[c("diabetes_type","==","prediabetes"),{"any":[c("age","between",[25,59]),c("bmi",">=",35),c("fasting_glucose",">=",110),c("a1c",">=",6.0),c("history_gdm","==")]}]},
   recommend=["Lifestyle (DPP: 5-7% weight loss, 150 min/week) first-line","Consider metformin; consider GLP-1/tirzepatide for obesity"],instructions=["INS-DPP","INS-ACTIVITY-150","INS-PLATE-METHOD"]),
 dict(id="R-PRED-FOLLOWUP",title="Prediabetes monitoring",rec="3.1",severity="info",
   when={"all":[c("diabetes_type","==","prediabetes")]},flags=["Test for progression at least annually; address CV risk factors; do not stop statins."]),
 dict(id="R-STATIN",title="Statin and diabetes risk",rec="3.12",severity="info",
   when={"all":[c("on_statin","=="),{"any":[c("diabetes_type","==","prediabetes")]}]},flags=["Monitor glucose regularly; statin should NOT be stopped for this reason."]),
 dict(id="R-STROKE-PIO",title="Prior stroke with insulin resistance",rec="3.13",severity="info",
   when={"all":[c("prior_stroke_insulin_resistant","==")]},recommend=["Consider pioglitazone"],flags=["Weigh weight gain, edema, fractures."]),
 dict(id="R-PRE-T1D",title="Presymptomatic T1D",rec="3.2/3.17",severity="info",
   when={"all":[c("diabetes_type","==","presymptomatic_t1d")]},flags=["A1C ~6-monthly and OGTT annually; discuss teplizumab for stage 2 T1D age >=8 years."]),
 dict(id="R-T1D-INSULIN",title="Type 1 diabetes plan",rec="9.1-9.3",severity="preferred",
   when={"all":[c("diabetes_type","==","type1")]},recommend=["Basal-bolus analog insulin or pump/AID","CGM","Glucagon","Carb counting + correction education"],avoid=["SGLT2 inhibitors"],instructions=["INS-INSULIN-TECHNIQUE","INS-GLUCAGON","INS-HYPO-RECOGNITION","INS-SICK-DAY-T1D"]),
 dict(id="R-FASTING",title="Religious fasting planned",rec="5.32/5.33",severity="warning",
   when={"all":[c("fasting_planned","==")]},flags=["Perform IDF-DAR risk score well in advance; adjust therapy (see fasting_adjustments); fasting-focused education."],instructions=["INS-FASTING"]),
 dict(id="R-ALCOHOL",title="Alcohol with insulin/secretagogue",rec="5.18/5.19",severity="info",
   when={"all":[c("alcohol_use","=="),{"any":[c("on_insulin","=="),c("on_sulfonylurea","=="),c("on_meglitinide","==")]}]},instructions=["INS-ALCOHOL"]),
 dict(id="R-TOBACCO",title="Tobacco/vaping",rec="5.40",severity="info",
   when={"any":[c("tobacco_or_vaping","=="),c("smoker_current_or_recent","==")]},recommend=["Counseling + pharmacotherapy (varenicline most effective in diabetes data)"],instructions=["INS-TOBACCO"]),
 dict(id="R-CANNABIS",title="Cannabis in T1D/DKA-prone",rec="5.41",severity="warning",
   when={"all":[c("cannabis_use","=="),{"any":[c("diabetes_type","==","type1"),c("insulin_deficient","=="),c("dka_history","==")]}]},instructions=["INS-CANNABIS"]),
 dict(id="R-DISORDERED-EATING",title="Disordered eating",rec="5.50/5.51",severity="warning",
   when={"all":[c("disordered_eating","==")]},flags=["Refer to behavioral health; avoid rigid carb counting/intensive weight monitoring; check for insulin omission or dose reduction to control weight; review drugs affecting hunger."]),
 dict(id="R-VLC-RISK",title="Very-low-carbohydrate diet cautions",rec="Section 5 text",severity="warning",
   when={"all":[c("very_low_carb_or_keto_diet","=="),{"any":[c("on_insulin","=="),c("on_sulfonylurea","=="),c("egfr","<",60),c("pregnant","==")]}]},flags=["Medical oversight; adjust insulin/secretagogue to prevent hypoglycemia; not recommended in pregnancy, children, kidney disease, disordered eating."]),
 dict(id="R-FOOD-INSECURITY",title="Food insecurity",rec="Section 5 text",severity="info",
   when={"all":[c("food_insecurity","==")]},flags=["Avoid hypoglycemia-prone drugs where food access unreliable; refer to food resources."]),
 dict(id="R-DSMES",title="DSMES/MNT referral",rec="5.1/5.2/5.10",severity="info",when={"all":[c("diabetes_type","!=","none")]},always=True,instructions=["INS-DSMES","INS-MNT"]),
 dict(id="R-SLEEP",title="Sleep",rec="5.56/5.57",severity="info",when={"any":[c("sleep_problem","=="),c("shift_work","==")]},instructions=["INS-SLEEP"]),
 dict(id="R-SEDENTARY",title="Sedentary",rec="5.34",severity="info",when={"all":[c("sedentary","==")]},instructions=["INS-ACTIVITY-150","INS-BREAK-SITTING"]),
]

# ---------------- PATIENT-FACING INSTRUCTION TEMPLATES ----------------
INSTR = [
 ("INS-METFORMIN","Medication","METFORMIN","Take metformin with meals. Mild stomach upset or loose stools are common at first and usually settle; your dose is increased slowly to help. Tell your doctor if you have vomiting, severe diarrhea, dehydration or kidney problems."),
 ("INS-B12","Monitoring","METFORMIN","Long-term metformin can lower vitamin B12. Get your B12 level checked regularly; report numbness, tingling or unusual tiredness."),
 ("INS-SGLT2I","Medication","SGLT2I","Drink enough water. Keep the genital area clean and dry. Report burning urine, fever, genital pain/swelling, or pain, redness or swelling around the genitals or back passage immediately."),
 ("INS-SGLT2I-SICK-DAY","Sick day","SGLT2I","If you are vomiting, not eating or drinking, have severe illness, or are fasting for a long period, stop this tablet and contact your doctor. Stop it 3-4 days before planned surgery."),
 ("INS-SGLT2I-KETONE","Safety","SGLT2I","Avoid very low-carbohydrate or ketogenic diets and heavy alcohol. Seek urgent care for nausea, vomiting, abdominal pain, fast breathing or unusual tiredness even if your sugar is not very high; check blood ketones if you have a meter."),
 ("INS-GLP1","Medication","GLP1RA","Eat smaller meals and stop when you feel full; avoid very fatty or spicy food. Nausea usually improves over time. Seek care for severe or persistent abdominal pain (with or without vomiting) or yellowing of skin/eyes. Tell your doctor before any surgery or procedure needing sedation."),
 ("INS-GLP1-TITRATION","Medication","GLP1RA","Your dose will be increased in steps; do not skip steps or increase on your own. Do not buy compounded or unregulated injectable versions."),
 ("INS-TIRZ","Medication","TIRZEPATIDE","Same weekly day each week. If you take birth-control pills, use an additional non-oral method for 4 weeks after starting and after each dose increase."),
 ("INS-DPP4I","Medication","DPP4I","Report severe, persistent abdominal pain, severe joint pain, or blisters on the skin and stop the medicine until reviewed."),
 ("INS-TZD","Medication","TZD","Report weight gain, swollen ankles or breathlessness immediately. Tell your doctor about bone fractures or blood in urine."),
 ("INS-SU","Medication","SU","Never skip meals while taking this medicine. Carry fast-acting sugar. Learn the signs of low sugar (shaking, sweating, hunger, confusion)."),
 ("INS-INSULIN-START","Medication","INSULIN_HUMAN|INSULIN_ANALOG","Inject into fat under the skin (abdomen, thigh, buttock, upper arm), rotate sites each time and avoid lumpy areas. Check glucose as advised and do not change your dose on your own unless taught how."),
 ("INS-INSULIN-TECHNIQUE","Medication","INSULIN_ANALOG","Use short (4 mm) pen needles; new needle each time; rotate sites; avoid injecting into lumps. Match mealtime insulin to carbohydrate as taught, with correction doses when high."),
 ("INS-HYPO-RECOGNITION","Safety","INSULIN_HUMAN|INSULIN_ANALOG|SU","Low sugar (below 70 mg/dL): shaking, sweating, hunger, palpitations, confusion. Take 15 g fast-acting carbohydrate, recheck in 15 minutes and repeat if needed, then eat. Tell your doctor about every low."),
 ("INS-GLUCAGON","Safety","INSULIN_HUMAN|INSULIN_ANALOG","Keep glucagon (ready-to-use form if possible) at hand. Family and close contacts must know where it is and how to use it for a severe low (unable to swallow or unconscious); call emergency services."),
 ("INS-SICK-DAY-T1D","Sick day","INSULIN_ANALOG","Never stop basal insulin when ill. Check glucose (and ketones) more often, drink fluids, and call your team if ketones are present, you vomit, or sugars stay high."),
 ("INS-NO-COMPOUNDED","Safety","GLP1RA|TIRZEPATIDE","Use only approved, pharmacy-dispensed products. Avoid compounded or online unregulated versions."),
 ("INS-CONTRACEPTION","Safety","TIRZEPATIDE|GLP1RA","Some diabetes medicines are unsafe in pregnancy or affect birth-control absorption. Use reliable contraception and talk to your doctor months before planning pregnancy."),
 ("INS-KIDNEY-MONITOR","Monitoring","SGLT2I|GLP1RA|METFORMIN","Kidney function and urine albumin will be checked regularly; avoid unprescribed painkillers (NSAIDs) and stay hydrated."),
 ("INS-EYE-EXAM","Monitoring","GLP1RA|TIRZEPATIDE","Have a dilated eye examination at diagnosis and then every 1-2 years (every year if retinopathy is present); go sooner for any sudden vision change."),
 ("INS-CV-RISK","Medication","GLP1RA|SGLT2I","This medicine protects heart and kidneys as well as lowering sugar. Keep taking it even when sugars are normal."),
 ("INS-WEIGHT-GOAL","Lifestyle","","Aim for at least 5-7% weight loss (more gives more benefit) through reduced-calorie, nutritious eating and regular activity."),
 ("INS-MUSCLE-PRESERVE","Lifestyle","","While losing weight include muscle-strengthening exercise 2-3 days a week and adequate protein to keep muscle."),
 ("INS-PLATE-METHOD","Nutrition","","Plate method: half non-starchy vegetables, one quarter lean or plant protein, one quarter high-fibre carbohydrate (whole grain/legumes)."),
 ("INS-EAT-PATTERN","Nutrition","","Eat vegetables, whole fruit, legumes, whole grains, nuts and seeds; use unsaturated oils; limit red/processed meat, sweets, refined grains, packaged and ultra-processed foods. A Mediterranean-style pattern is a good choice."),
 ("INS-WATER","Nutrition","","Drink water instead of sweetened drinks and juices; unsweetened or no-calorie drinks are acceptable."),
 ("INS-SALT","Nutrition","","Keep sodium below 2,300 mg/day (about 5 g salt): limit processed foods, do not add extra salt."),
 ("INS-FIBER","Nutrition","","Choose high-fibre carbohydrates (at least 14 g fibre per 1,000 kcal)."),
 ("INS-SUPPLEMENTS","Nutrition","","Vitamin, mineral and herbal supplements (cinnamon, chromium, aloe) do not improve sugar control; tell your doctor what you take. Do not take beta-carotene supplements."),
 ("INS-ALCOHOL","Safety","","If you drink: no more than 1 drink/day (women) or 2 (men), never on an empty stomach. Alcohol can cause delayed low sugar, so check glucose before bed and the next morning."),
 ("INS-ACTIVITY-150","Lifestyle","","At least 150 minutes/week of moderate to vigorous activity (e.g., brisk walking) spread over 3 or more days, with no more than 2 days in a row without activity."),
 ("INS-RESISTANCE","Lifestyle","","Do resistance exercise 2-3 days a week on non-consecutive days; older adults add balance and flexibility work."),
 ("INS-BREAK-SITTING","Lifestyle","","Break up long sitting at least every 30 minutes with a short walk or light activity."),
 ("INS-EXERCISE-HYPO","Safety","INSULIN_HUMAN|INSULIN_ANALOG|SU","Check glucose before and after exercise; low sugar can occur during and hours after. Carry fast-acting carbohydrate; take extra carbohydrate if glucose is below 90 mg/dL before exercising as advised."),
 ("INS-TOBACCO","Lifestyle","","Stopping tobacco and vaping lowers your risk of heart, kidney and eye disease. Ask for counseling and medicines to help you quit; weight gain after quitting is usually small and does not cancel the benefit."),
 ("INS-CANNABIS","Safety","","Avoid recreational cannabis: it can cause vomiting and ketoacidosis in type 1 diabetes."),
 ("INS-SLEEP","Lifestyle","","Aim for about 7 hours of regular sleep; keep fixed bed and wake times, a dark quiet room, no screens before bed, limit evening caffeine and avoid alcohol before sleep. Tell your doctor if you snore loudly or stop breathing at night."),
 ("INS-DPP","Lifestyle","","Join a structured diabetes prevention programme (in-person or certified digital) for coaching on weight loss and activity."),
 ("INS-DSMES","Education","","Attend diabetes self-management education and support at diagnosis, yearly, when targets are not met, and after major life or health changes."),
 ("INS-MNT","Education","","See a registered dietitian for an individualized meal plan."),
 ("INS-STEROID-GLUCOSE","Monitoring","","While on steroid tablets/injections check glucose also in the afternoon and evening, not only fasting; doses may need to change as the steroid is reduced."),
 ("INS-FASTING","Safety","","Before religious fasting, review your treatment plan and risk with your doctor. Check glucose more often (especially the last hours of fasting); break the fast if glucose is below 70 mg/dL or above 300 mg/dL or you feel unwell; drink plenty of fluids and avoid sugary, very fatty meals when breaking the fast."),
 ("INS-FOLLOWUP","Monitoring","","Medication plan will be reviewed every 3-6 months; do not delay review if targets are not met."),
 ("INS-COST","Access","","If cost is a problem, tell your doctor or pharmacist: lower-cost effective options exist. Do not stop medicines without advice."),
]

# ---------------- MONITORING ----------------
MONITOR = [
 ("Medication/insulin plan review","every 3-6 months","9.4/9.14"),
 ("A1C / CGM metrics","at each review; reassess when above goal","9"),
 ("Prediabetes progression test","at least annually","3.1"),
 ("Presymptomatic T1D","A1C ~6-monthly; OGTT annually","3.2"),
 ("eGFR and albuminuria","at least annually and with kidney-affecting drugs","9 CKD"),
 ("Vitamin B12 on metformin","periodic; annually if >4 years or risk (anemia, neuropathy, vegan, GI surgery, PPI)","3.10"),
 ("Retinal exam on GLP-1 RA in high-risk","monitor closely incl. NAION","Table 9.2"),
 ("Spirometry with inhaled insulin","before and after starting","9"),
 ("Weight, glucose, lipids on SGA antipsychotics","every 12-16 weeks","5.53"),
 ("Psychosocial screen (distress, anxiety, depression)","at least annually and with change","5.43-5.48"),
 ("Disordered-eating screen","validated tool (DEPS-R, mSCOFF, QEWP-5, Binge Eating Scale, Night Eating Questionnaire)","5.50"),
 ("Cognitive capacity","throughout life; formal test if changes","5.54"),
 ("Sleep screen","routine","5.56"),
 ("Food insecurity (Hunger Vital Sign)","routine, any team member","Section 5"),
 ("Tobacco/vaping","every visit","5.40"),
 ("Injection sites for lipohypertrophy","each visit with insulin","9"),
 ("Glucose 3 h after high-fat/protein meals","as needed for pump/insulin adjustment","Section 5"),
 ("Overbasalization check","each visit on insulin","9.26"),
]

REFERRALS = [
 ("DSMES","at diagnosis, annually/when goals unmet, with complications, transitions of care","5.2"),
 ("Registered dietitian MNT","at diagnosis and as needed; esp. HTN, dyslipidemia, HF, CKD, GI disease, pregnancy, obesity","5.10"),
 ("Behavioral health","positive screen (depression, distress, anxiety, fear of hypoglycemia, suicidality, cognition); disordered eating; intentional insulin/drug omission for weight; suspected SMI; low engagement; before/after metabolic surgery","Table 5.5"),
 ("Sleep specialist","significant sleep difficulty or suspected OSA","5.56"),
 ("Ophthalmologist","proliferative/severe NPDR before vigorous exercise","Section 5"),
 ("Cardiac evaluation","autonomic neuropathy before more intense activity","Section 5"),
 ("Diabetes prevention program","high-risk adults with prediabetes and overweight/obesity","3.3/3.5"),
 ("Endocrine/transplant team","post-transplant diabetes","9.37"),
 ("Pregnancy/preconception clinic","childbearing potential planning pregnancy","9.32b"),
]

FASTING_ITEMS = [
 ("Pregnancy with diabetes","yes",6.5),
 ("Diabetes type","T1D or LADA",1),("Diabetes type","T2D/other",0),
 ("Duration","> 20 y",1),("Duration","10-20 y",0.5),("Duration","< 10 y",0),
 ("Treatment","multiple daily premixed insulin",2),("Treatment","once-daily premixed insulin",1.5),("Treatment","open-loop pump",1.5),("Treatment","AID system",1),
 ("Treatment","standard basal (NPH, detemir, glargine 100)",1),("Treatment","ultra-long basal (glargine 300, degludec)",0.75),("Treatment","short-acting insulin",0.75),
 ("Treatment","glibenclamide or glipizide",0.75),("Treatment","gliclazide/glimepiride/repaglinide",0.5),("Treatment",">=2 non-insulin non-SU drugs",0.25),("Treatment","nutrition only or monotherapy",0),
 ("Hypoglycemia","impaired awareness",6.5),("Hypoglycemia","severe in last 4 weeks",5),("Hypoglycemia","more than once daily",4),("Hypoglycemia","6-7 episodes/week",3),("Hypoglycemia","3-5/week",2),("Hypoglycemia","1-2/week",1),("Hypoglycemia","<1/week",0.5),("Hypoglycemia","none in 4 weeks",0),
 ("A1C","> 9%",1),("A1C","7.5-9%",0.5),("A1C","< 7.5%",0),
 ("Glucose monitoring","not done",2),("Glucose monitoring","suboptimal",1),("Glucose monitoring","as indicated",0),("Glucose monitoring","any CGM",-0.5),
 ("Hyperglycemic emergency","DKA/HHS in last month",3.5),("Hyperglycemic emergency","2-3 months",2),("Hyperglycemic emergency","4-6 months",1),("Hyperglycemic emergency","none in 6 months",0),
 ("Macrovascular disease","unstable",6.5),("Macrovascular disease","stable",2),("Macrovascular disease","none",0),
 ("Nephropathy","eGFR <30",6.5),("Nephropathy","eGFR 30-45",4),("Nephropathy","eGFR 45-60",2),("Nephropathy","eGFR >60",0),
 ("Neuropathy/foot/retinopathy","3 complications",3),("Neuropathy/foot/retinopathy","2",2),("Neuropathy/foot/retinopathy","1",1),("Neuropathy/foot/retinopathy","0",0),
 ("Cognition/frailty/age","impaired cognition",6.5),("Cognition/frailty/age","advanced frailty",6.5),("Cognition/frailty/age","mild-moderate frailty",4),("Cognition/frailty/age","age >70 with no home support",1),("Cognition/frailty/age","normal",0),
 ("Physical labor","high",4),("Physical labor","moderate",2),("Physical labor","low",0),
 ("Fasting-focused education","yes",0),("Fasting-focused education","no",1),
 ("Fasting hours",">=16 h",1),("Fasting hours","<16 h",0),
]
FASTING_BANDS = [("low (0-3.0)","fasting probably safe"),("moderate (3.5-6.0)","safety uncertain"),("high (>6.0)","fasting probably unsafe")]

FASTING_ADJ = [
 ("metformin, SGLT2i, DPP-4i, GLP-1 RA, acarbose, pioglitazone","low","once daily: main meal; twice daily: split between two meals; weekly: no change","no change"),
 ("glimepiride, gliclazide","low to moderate","once daily: main meal; twice daily: split between two meals","reduce dose if glucose within goal and no hypo/hyperglycemia at baseline"),
 ("glyburide","moderate to high","at main meal","replace with newer sulfonylurea or reduce dose 50%"),
 ("basal insulin","moderate to high","glargine 300/degludec: no timing change; others: at breaking-fast meal","choose lower-hypoglycemia basal; reduce 25-35% if not well managed"),
 ("prandial insulin","high","at mealtime","reduce dose for meal followed by fasting by 35-50%; other meals match carbohydrate"),
 ("mixed/co-formulated insulin","high","once daily: main meal; twice daily: split between two meals","reduce dose for meal followed by fasting by 35-50%; other meals no change"),
]

import sys; sys.path.insert(0,HERE)
import extend_data as X
META["sources"] += X.SOURCES
RECS += X.RECS; FIELDS += X.FIELDS; CLASSES += X.CLASSES; DRUGS += X.DRUGS
RULES += X.RULES; INSTR += X.INSTR; MONITOR += X.MONITOR; REFERRALS += X.REFERRALS
# ---------------- BUILD JSON ----------------
db = {
 "meta": META,
 "patient_fields": [dict(field=a,type=b,notes=c_) for a,b,c_ in FIELDS],
 "recommendations": [dict(id=a,section=b,grade=g,topic=t,summary=s) for a,b,g,t,s in RECS],
 "drug_classes": CLASSES,
 "drugs": [dict(class_id=a,generic=b,strength=c_,max_daily_dose=d,awp_monthly_usd=e,nadac_monthly_usd=f) for a,b,c_,d,e,f in DRUGS],
 "insulin_cost_per_1000_units": [dict(product=a,awp_usd=b,nadac_usd=c_) for a,b,c_ in INSULIN_COST],
 "insulin_dosing": [dict(topic=a,guidance=b,source=c_) for a,b,c_ in INSULIN_RULES],
 "rules": RULES,
 "instructions": [dict(id=a,category=b,class_ids=[x for x in cl.split("|") if x],text=t) for a,b,cl,t in INSTR],
 "monitoring": [dict(item=a,frequency=b,source=c_) for a,b,c_ in MONITOR],
 "referrals": [dict(service=a,triggers=b,source=c_) for a,b,c_ in REFERRALS],
 "fasting_risk_items": [dict(domain=a,level=b,score=c_) for a,b,c_ in FASTING_ITEMS],
 "fasting_risk_bands": [dict(band=a,meaning=b) for a,b in FASTING_BANDS],
 "fasting_adjustments": [dict(drugs=a,hypo_risk=b,timing=c_,dose=d) for a,b,c_,d in FASTING_ADJ],
 "reference_tables": X.REF,
}
with open(f"{OUT}/ada2026_prescription_kb.json","w") as f:
    json.dump(db,f,indent=1,ensure_ascii=False)

# ---------------- BUILD SQLITE ----------------
p=f"{OUT}/ada2026_prescription_kb.sqlite"
if os.path.exists(p): os.remove(p)
cx=sqlite3.connect(p); cu=cx.cursor()
cu.executescript("""
CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE patient_fields(field TEXT PRIMARY KEY, type TEXT, notes TEXT);
CREATE TABLE recommendations(id TEXT PRIMARY KEY, section TEXT, grade TEXT, topic TEXT, summary TEXT);
CREATE TABLE drug_classes(id TEXT PRIMARY KEY, name TEXT, route TEXT, glucose_efficacy TEXT, hypoglycemia_risk TEXT, weight TEXT, mace TEXT, hf TEXT, ckd_progression TEXT, mash TEXT, renal_json TEXT, adverse_json TEXT, monitoring_json TEXT, notes TEXT);
CREATE TABLE drugs(id INTEGER PRIMARY KEY AUTOINCREMENT, class_id TEXT REFERENCES drug_classes(id), generic TEXT, strength TEXT, max_daily_dose TEXT, awp_monthly_usd REAL, nadac_monthly_usd REAL);
CREATE TABLE insulin_cost(product TEXT, awp_usd REAL, nadac_usd REAL);
CREATE TABLE insulin_dosing(topic TEXT, guidance TEXT, source TEXT);
CREATE TABLE rules(id TEXT PRIMARY KEY, title TEXT, rec_ref TEXT, severity TEXT, always_fire INTEGER, when_json TEXT, recommend_json TEXT, avoid_json TEXT, flags_json TEXT, note TEXT, instruction_ids_json TEXT);
CREATE TABLE instructions(id TEXT PRIMARY KEY, category TEXT, text TEXT);
CREATE TABLE instruction_class(instruction_id TEXT REFERENCES instructions(id), class_id TEXT REFERENCES drug_classes(id));
CREATE TABLE monitoring(item TEXT, frequency TEXT, source TEXT);
CREATE TABLE referrals(service TEXT, triggers TEXT, source TEXT);
CREATE TABLE fasting_risk_items(domain TEXT, level TEXT, score REAL);
CREATE TABLE fasting_risk_bands(band TEXT, meaning TEXT);
CREATE TABLE fasting_adjustments(drugs TEXT, hypo_risk TEXT, timing TEXT, dose TEXT);
CREATE TABLE reference_tables(name TEXT, row_json TEXT);
""")
for k,v in META.items(): cu.execute("INSERT INTO meta VALUES(?,?)",(k,json.dumps(v)))
cu.executemany("INSERT INTO patient_fields VALUES(?,?,?)",FIELDS)
cu.executemany("INSERT INTO recommendations VALUES(?,?,?,?,?)",RECS)
for k in CLASSES:
    cu.execute("INSERT INTO drug_classes VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(k["id"],k["name"],k["route"],k["glucose_efficacy"],k["hypoglycemia_risk"],k["weight"],k["mace"],k["hf"],k["ckd_progression"],k["mash"],json.dumps(k["renal"]),json.dumps(k["adverse"]),json.dumps(k["monitoring"]),k["notes"]))
cu.executemany("INSERT INTO drugs(class_id,generic,strength,max_daily_dose,awp_monthly_usd,nadac_monthly_usd) VALUES(?,?,?,?,?,?)",DRUGS)
cu.executemany("INSERT INTO insulin_cost VALUES(?,?,?)",INSULIN_COST)
cu.executemany("INSERT INTO insulin_dosing VALUES(?,?,?)",INSULIN_RULES)
for r in RULES:
    cu.execute("INSERT INTO rules VALUES(?,?,?,?,?,?,?,?,?,?,?)",(r["id"],r["title"],r["rec"],r["severity"],1 if r.get("always") else 0,json.dumps(r["when"]),json.dumps(r.get("recommend",[])),json.dumps(r.get("avoid",[])),json.dumps(r.get("flags",[])),r.get("note",""),json.dumps(r.get("instructions",[]))))
for a,b,cl,t in INSTR:
    cu.execute("INSERT INTO instructions VALUES(?,?,?)",(a,b,t))
    for x in cl.split("|"):
        if x: cu.execute("INSERT INTO instruction_class VALUES(?,?)",(a,x))
cu.executemany("INSERT INTO monitoring VALUES(?,?,?)",MONITOR)
cu.executemany("INSERT INTO referrals VALUES(?,?,?)",REFERRALS)
cu.executemany("INSERT INTO fasting_risk_items VALUES(?,?,?)",FASTING_ITEMS)
cu.executemany("INSERT INTO fasting_risk_bands VALUES(?,?)",FASTING_BANDS)
cu.executemany("INSERT INTO fasting_adjustments VALUES(?,?,?,?)",FASTING_ADJ)
for n,v in X.REF.items():
    for row in (v if isinstance(v,list) else [v]):
        cu.execute("INSERT INTO reference_tables VALUES(?,?)",(n,json.dumps(row)))
cx.commit()
print({t:cu.execute(f"select count(*) from {t}").fetchone()[0] for t in ["recommendations","drug_classes","drugs","rules","instructions","monitoring","patient_fields"]})
cx.close()
