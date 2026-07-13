import os, json, datetime
from validate_triage import run_hl7_validator, triage_outcome
from ai_investigator import investigate_ambiguity

def execute_full_pipeline(name, path):
    ts = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    tx_id = f"tx_demo_{int(datetime.datetime.utcnow().timestamp())}"
    with open(path, 'r') as f: raw_fix = json.load(f)
    prof = raw_fix.get("meta", {}).get("profile", ["Unknown/PAS"])[0].split("/")[-1]
    
    out_file = f"bin/outcome_{name}.json"
    run_hl7_validator(path, out_file)
    route, issues = triage_outcome(out_file)
    
    ui_state = {"badgeColor": "green", "badgeLabel": "Passed Validation", "summaryStatus": "APPROVED", "narrativeText": "Clean pass."}
    det = {"engine": "HL7 validator_cli.jar", "isValidStructure": True, "totalErrors": 0, "totalWarnings": 0, "rawHL7Issues": []}
    heur = {"engine": "PAS Coprocessor LLM (GPT-4o)", "executionTriggered": False, "confidenceScore": 1.0, "clinicalJustification": "N/A", "crosswalk": None}

    if route == "ROUTE_REJECT":
        ui_state.update({"badgeColor": "red", "badgeLabel": "Hard Error Detected", "summaryStatus": "REJECTED", "narrativeText": "Critical structural violation."})
        det.update({"isValidStructure": False, "totalErrors": len(issues), "rawHL7Issues": [{"severity": "error", "location": "Claim.prescription.period", "message": i} for i in issues]})
    elif route == "ROUTE_AI_INVESTIGATION":
        ui_state.update({"badgeColor": "orange", "badgeLabel": "AI Investigation Active", "summaryStatus": "RESOLVED_COMPLIANT", "narrativeText": "AI crosswalk applied."})
        det.update({"totalWarnings": len(issues), "rawHL7Issues": [{"severity": "warning", "location": "Claim.supportingInfo[0].code", "message": i} for i in issues]})
        ai_res = investigate_ambiguity(issues, raw_fix)
        heur.update({"executionTriggered": True, "confidenceScore": ai_res.get("confidence_score"), "clinicalJustification": ai_res.get("clinical_justification"), "crosswalk": ai_res.get("crosswalk_mapping")})
        ui_state.update({"narrativeText": ai_res.get("clinical_justification")})

    final = {"transactionId": tx_id, "timestamp": ts, "fixtureId": name, "profileTarget": prof, "uiState": ui_state, "deterministicAnalysis": det, "heuristicAnalysis": heur}
    with open(f"ui_data/{name}_dashboard.json", 'w') as out: json.dump(final, out, indent=2)

if __name__ == "__main__":
    for k, v in {"Fixture_A_Safe_Case": "fixtures/fixture_a.json", "Fixture_B_Breaking_Case": "fixtures/fixture_b.json", "Fixture_C_Uncertain_Case": "fixtures/fixture_c.json"}.items():
        if os.path.exists(v): execute_full_pipeline(k, v)
