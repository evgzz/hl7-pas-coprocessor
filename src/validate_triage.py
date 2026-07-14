import subprocess
import json
import os

VALIDATOR_JAR = "bin/validator_cli.jar"
IG_PACKAGE = "bin/ig_packages/hl7.fhir.us.davinci-pas#2.0.1.tgz"
FHIR_VERSION = "4.0.1"

# def run_hl7_validator(fixture_path, output_path):
    # cmd = ["java", "-jar", VALIDATOR_JAR, fixture_path, "-version", FHIR_VERSION, "-ig", IG_PACKAGE, "-output", output_path]
def run_hl7_validator(fixture_path, output_path):
    # Re-order the flags so options come first, use -output-json, and place target file at the end
    cmd = [
        "java", "-jar", VALIDATOR_JAR, 
        "-version", FHIR_VERSION, 
        "-ig", IG_PACKAGE, 
        "-output", output_path, 
        fixture_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return output_path
    # subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # return output_path

def triage_outcome(outcome_json_path):
    if not os.path.exists(outcome_json_path):
        return "ROUTE_REJECT", ["Validator failed to produce an outcome block."]
    with open(outcome_json_path, 'r') as f:
        outcome = json.load(f)
    issues = outcome.get("issue", [])
    errors, warnings = [], []
    for issue in issues:
        severity = issue.get("severity")
        diagnostics = issue.get("details", {}).get("text", issue.get("diagnostics", "Unknown"))
        loc = issue.get("expression", ["root"])[0]
        summary = f"[{loc}] {diagnostics}"
        if severity in ["error", "fatal"]:
            errors.append(summary)
        elif severity == "warning":
            warnings.append(summary)
    if errors: return "ROUTE_REJECT", errors
    if warnings: return "ROUTE_AI_INVESTIGATION", warnings
    return "ROUTE_APPROVE", ["Clean pass."]
