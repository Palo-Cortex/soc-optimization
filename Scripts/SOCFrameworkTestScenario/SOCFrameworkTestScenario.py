import demistomock as demisto  # noqa: F401
from CommonServerPython import *  # noqa: F401
import json
import random
import traceback


# ----------------------------------------
# ARTIFACT HELPERS
# ----------------------------------------

def rand_ip():
    return ".".join(str(random.randint(1, 254)) for _ in range(4))

def rand_sha256():
    return "".join(random.choice("abcdef0123456789") for _ in range(64))

def add(artifacts, bucket, value, source):
    if bucket not in artifacts:
        return
    lst = artifacts[bucket]
    for entry in lst:
        if entry.get("value") == value:
            return
    lst.append({"value": value, "source": source})


# ----------------------------------------
# CANONICAL NORMALIZED STRUCTURE
# ----------------------------------------

CANONICAL_BUCKETS = [
    "Attack_Pattern",
    "MITRE_Tactic",
    "MITRE_Technique",
    "Domain",
    "IP",
    "URL",
    "Email_Sender",
    "Email_Recipient",
    "Email_Subject",
    "Email_DisplayName",
    "Email_ReplyTo",
    "Email_MessageID",
    "File_Path",
    "File_Name",
    "File_Hash_SHA256"
]

def empty_artifacts():
    return {b: [] for b in CANONICAL_BUCKETS}


# ----------------------------------------
# LOAD PRODUCT CATEGORY MAP
# ----------------------------------------

def load_product_meta(dataset):
    try:
        raw = demisto.executeCommand("getList", {"listName": "SOC_ProductCategoryMap"})
        raw = raw[0].get("Contents")
        data = json.loads(raw)
        return data.get(dataset, {})
    except Exception:
        return {}


# ----------------------------------------
# MAIN SCENARIO LOGIC
# ----------------------------------------

def scenario_phishing(artifacts):
    sender = "attacker@example.com"
    recipient = "victim@example.com"
    msgid = "MSG-" + rand_sha256()[0:12]

    add(artifacts, "Email_Sender", sender, "scenario")
    add(artifacts, "Email_Recipient", recipient, "scenario")
    add(artifacts, "Email_Subject", "Important: Action Required", "scenario")
    add(artifacts, "Email_DisplayName", "HR Department", "scenario")
    add(artifacts, "Email_ReplyTo", sender, "scenario")
    add(artifacts, "Email_MessageID", msgid, "scenario")

    domain = "malicious.biz"
    url = f"https://{domain}/login"

    add(artifacts, "Domain", domain, "scenario")
    add(artifacts, "URL", url, "scenario")
    add(artifacts, "IP", rand_ip(), "scenario")

    add(artifacts, "MITRE_Tactic", "Initial Access", "scenario")
    add(artifacts, "MITRE_Technique", "T1566.002", "scenario")


def scenario_malware(artifacts):
    file_name = "malware.exe"
    file_path = f"/tmp/{file_name}"

    add(artifacts, "File_Name", file_name, "scenario")
    add(artifacts, "File_Path", file_path, "scenario")
    add(artifacts, "File_Hash_SHA256", rand_sha256(), "scenario")

    add(artifacts, "Domain", "attacker.net", "scenario")
    add(artifacts, "IP", rand_ip(), "scenario")

    add(artifacts, "MITRE_Tactic", "Execution", "scenario")
    add(artifacts, "MITRE_Technique", "T1059.003", "scenario")


def scenario_identity(artifacts):
    add(artifacts, "Domain", "corp.auth", "scenario")
    add(artifacts, "URL", "https://login.corp.auth", "scenario")

    add(artifacts, "MITRE_Tactic", "Credential Access", "scenario")
    add(artifacts, "MITRE_Technique", "T1003", "scenario")


def scenario_endpoint(artifacts):
    add(artifacts, "Domain", "endpoint.internal", "scenario")
    add(artifacts, "File_Name", "agent.exe", "scenario")
    add(artifacts, "File_Path", "/var/tmp/agent.exe", "scenario")
    add(artifacts, "File_Hash_SHA256", rand_sha256(), "scenario")

    add(artifacts, "MITRE_Tactic", "Execution", "scenario")
    add(artifacts, "MITRE_Technique", "T1059", "scenario")


def scenario_cloud(artifacts):
    add(artifacts, "Domain", "cloud.example", "scenario")
    add(artifacts, "IP", rand_ip(), "scenario")

    add(artifacts, "MITRE_Tactic", "Discovery", "scenario")
    add(artifacts, "MITRE_Technique", "T1057", "scenario")


SCENARIOS = {
    "phishing": scenario_phishing,
    "malware": scenario_malware,
    "identity": scenario_identity,
    "endpoint": scenario_endpoint,
    "cloud": scenario_cloud
}


# ----------------------------------------
# MAIN EXECUTION
# ----------------------------------------

def main():
    try:
        args = demisto.args()

        scenario = args.get("scenario", "phishing").lower()
        dataset = args.get("dataset", "ds_test_dataset")
        shadow = args.get("shadowmode", "false").lower() == "true"

        if scenario not in SCENARIOS:
            return demisto.results(f"Unknown scenario '{scenario}'")

        artifacts = empty_artifacts()
        SCENARIOS[scenario](artifacts)

        # Product category resolution
        meta = load_product_meta(dataset)
        product = {
            "key": dataset,
            "category": meta.get("category", "Unknown"),
            "type": meta.get("type", "Unknown"),
            "confidence": meta.get("confidence", "low")
        }

        soc = {
            "Artifacts": artifacts,
            "Product": product,
            "shadow_mode": shadow
        }

        demisto.setContext("SOCFramework", soc)

        demisto.results({
            "Type": 1,
            "ContentsFormat": "json",
            "Contents": soc
        })

    except Exception as e:
        demisto.results(f"Error in TestScenario:\n{e}\n{traceback.format_exc()}")


if __name__ in ("__main__", "__builtin__", "builtins"):
    main()

