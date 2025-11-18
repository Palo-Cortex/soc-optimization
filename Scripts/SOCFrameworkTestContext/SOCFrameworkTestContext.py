import demistomock as demisto  # noqa: F401
from CommonServerPython import *  # noqa: F401
#!/usr/bin/env python3

import json
import random
import traceback


# ----------------------------------------------------------------------
# FINAL CANONICAL ARTIFACT SCHEMA (must match normalizer exactly)
# ----------------------------------------------------------------------

CANONICAL_BUCKETS = [
    "Attack_Pattern",
    "MITRE_Tactic",
    "MITRE_Technique",
    "Domain",
    "IP",
    "Email_Subject",
    "Email_DisplayName",
    "URL",
    "Email_Recipient",
    "Email_Sender",
    "Email_ReplyTo",
    "Tactic",
    "File_Path",
    "File_Name",
    "File_Hash_SHA256",
    "File_Hash_SHA1",
    "File_Hash_MD5",
]

def new_artifact_struct():
    return {bucket: [] for bucket in CANONICAL_BUCKETS}


# ----------------------------------------------------------------------
# THEMES
# ----------------------------------------------------------------------

THEMES = {
    "marvel": [
        "TonyStark", "LokiLaufeyson", "PeterParker",
        "WandaMaximoff", "StarkIndustries", "Wakanda"
    ],
    "starwars": [
        "LukeSkywalker", "LeiaOrgana", "HanSolo",
        "DarthVader", "Tatooine", "Coruscant"
    ],
    "lotr": [
        "FrodoBaggins", "Gandalf", "Aragorn",
        "Legolas", "Rivendell", "Mordor"
    ],
}

ALL_THEME_VALUES = sum(THEMES.values(), [])


# ----------------------------------------------------------------------
# PRODUCT CATEGORY MAP
# ----------------------------------------------------------------------

def load_product_category_map():
    try:
        resp = demisto.executeCommand("getList", {"listName": "SOC_ProductCategoryMap"})
        raw = resp[0].get("Contents")
        return json.loads(raw) if raw else {}
    except Exception:
        return {}

SOC_PRODUCT_CATEGORY_MAP = load_product_category_map()


# ----------------------------------------------------------------------
# HELPERS
# ----------------------------------------------------------------------

def rand_ip():
    return ".".join(str(random.randint(1, 254)) for _ in range(4))

def rand_sha256():
    return "".join(random.choice("abcdef0123456789") for _ in range(64))

def rand_sha1():
    return "".join(random.choice("abcdef0123456789") for _ in range(40))

def rand_md5():
    return "".join(random.choice("abcdef0123456789") for _ in range(32))

def val(options):
    return random.choice(options)


def add_artifact(artifacts, bucket, value, source):
    """
    Basic add (TestContext does not implement issue precedence).
    Normalizer will handle merge precedence when consuming this.
    """
    if bucket not in artifacts:
        return
    exists = any(e["value"] == value for e in artifacts[bucket])
    if not exists:
        artifacts[bucket].append({
            "value": value,
            "source": source
        })


# ----------------------------------------------------------------------
# SCENARIO ENRICHMENT (maps into canonical buckets only)
# ----------------------------------------------------------------------

def apply_scenario(scenario, artifacts, theme_values):

    s = scenario.lower()

    # -------------------------
    # PHISHING
    # -------------------------
    if s == "phishing":
        sender    = val(theme_values) + "@example.com"
        recipient = val(theme_values) + "@example.com"

        add_artifact(artifacts, "Email_Sender", sender, "scenario.phishing")
        add_artifact(artifacts, "Email_Recipient", recipient, "scenario.phishing")
        add_artifact(artifacts, "Email_Subject", "Please Review Immediately", "scenario.phishing")
        add_artifact(artifacts, "Email_DisplayName", val(theme_values), "scenario.phishing")
        add_artifact(artifacts, "Email_ReplyTo", sender, "scenario.phishing")

        domain = val(theme_values).lower() + ".com"
        url = f"https://{domain}/verify"

        add_artifact(artifacts, "Domain", domain, "scenario.phishing")
        add_artifact(artifacts, "URL", url, "scenario.phishing")
        add_artifact(artifacts, "IP", rand_ip(), "scenario.phishing")

        add_artifact(artifacts, "MITRE_Tactic", "Initial Access", "scenario.phishing")
        add_artifact(artifacts, "MITRE_Technique", "T1566.002", "scenario.phishing")


    # -------------------------
    # MALWARE
    # -------------------------
    elif s == "malware":

        add_artifact(artifacts, "Attack_Pattern", "Execution", "scenario.malware")
        add_artifact(artifacts, "MITRE_Tactic", "Execution", "scenario.malware")
        add_artifact(artifacts, "MITRE_Technique", "T1059.003", "scenario.malware")

        # File artifacts
        file_name = val(theme_values).lower() + ".exe"
        file_path = f"/tmp/{file_name}"

        add_artifact(artifacts, "File_Name", file_name, "scenario.malware")
        add_artifact(artifacts, "File_Path", file_path, "scenario.malware")
        add_artifact(artifacts, "File_Hash_SHA256", rand_sha256(), "scenario.malware")

        add_artifact(artifacts, "IP", rand_ip(), "scenario.malware")
        add_artifact(artifacts, "Domain", val(theme_values).lower() + ".net", "scenario.malware")


    # -------------------------
    # IDENTITY
    # -------------------------
    elif s == "identity":
        domain = val(theme_values).lower() + ".auth"

        add_artifact(artifacts, "Domain", domain, "scenario.identity")
        add_artifact(artifacts, "URL", f"https://login.{domain}", "scenario.identity")

        add_artifact(artifacts, "MITRE_Tactic", "Credential Access", "scenario.identity")
        add_artifact(artifacts, "MITRE_Technique", "T1003", "scenario.identity")


    # -------------------------
    # ENDPOINT
    # -------------------------
    elif s == "endpoint":
        add_artifact(artifacts, "Attack_Pattern", "Execution", "scenario.endpoint")
        add_artifact(artifacts, "MITRE_Tactic", "Execution", "scenario.endpoint")
        add_artifact(artifacts, "MITRE_Technique", "T1059", "scenario.endpoint")

        file_name = val(theme_values).lower() + ".exe"
        file_path = f"/var/tmp/{file_name}"

        add_artifact(artifacts, "File_Name", file_name, "scenario.endpoint")
        add_artifact(artifacts, "File_Path", file_path, "scenario.endpoint")
        add_artifact(artifacts, "File_Hash_MD5", rand_md5(), "scenario.endpoint")

        add_artifact(artifacts, "Domain", val(theme_values).lower() + ".internal", "scenario.endpoint")


    # -------------------------
    # CLOUD
    # -------------------------
    elif s == "cloud":
        domain = val(theme_values).lower() + ".cloud"

        add_artifact(artifacts, "Domain", domain, "scenario.cloud")
        add_artifact(artifacts, "IP", rand_ip(), "scenario.cloud")

        add_artifact(artifacts, "MITRE_Tactic", "Discovery", "scenario.cloud")
        add_artifact(artifacts, "MITRE_Technique", "T1057", "scenario.cloud")


# ----------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------

def main():
    try:
        args = demisto.args()

        theme = args.get("theme", "marvel").lower()
        scenario = args.get("scenario", "endpoint")
        theme_values = ALL_THEME_VALUES if theme == "random" else THEMES.get(theme, THEMES["marvel"])

        dataset = args.get("dataset")
        productcategory = args.get("productcategory")
        shadowmode = args.get("shadowmode", "false").lower() == "true"

        # PRODUCT OBJECT
        product = {
            "category": "Endpoint",
            "confidence": "high",
            "key": dataset if dataset else "ds_crowdstrike_falcon_event",
            "type": "EDR"
        }

        if dataset and dataset in SOC_PRODUCT_CATEGORY_MAP:
            meta = SOC_PRODUCT_CATEGORY_MAP[dataset]
            product["category"] = meta["category"]
            product["type"] = meta["type"]
            product["confidence"] = meta["confidence"]

        if productcategory:
            product["category"] = productcategory

        # ARTIFACTS
        artifacts = new_artifact_struct()

        # Light base background noise (consistent with Normalizer merge logic)
        for bucket in CANONICAL_BUCKETS:
            if bucket == "IP":
                add_artifact(artifacts, bucket, rand_ip(), "base")
            elif bucket == "Domain":
                add_artifact(artifacts, bucket, val(theme_values).lower() + ".biz", "base")
            elif bucket == "URL":
                add_artifact(
                    artifacts,
                    bucket,
                    f"https://{val(theme_values).lower()}.biz/{random.randint(100,999)}",
                    "base"
                )
            elif bucket in ("Email_Sender", "Email_Recipient"):
                add_artifact(artifacts, bucket, val(theme_values) + "@example.com", "base")
            elif bucket == "Email_Subject":
                add_artifact(artifacts, bucket, "Test Subject", "base")
            elif bucket == "Email_DisplayName":
                add_artifact(artifacts, bucket, val(theme_values), "base")
            elif bucket == "Email_ReplyTo":
                add_artifact(artifacts, bucket, val(theme_values) + "@example.com", "base")

            # File artifacts (light base)
            elif bucket == "File_Path":
                add_artifact(artifacts, bucket, "/tmp/basefile", "base")
            elif bucket == "File_Name":
                add_artifact(artifacts, bucket, "basefile.exe", "base")
            elif bucket == "File_Hash_SHA256":
                add_artifact(artifacts, bucket, rand_sha256(), "base")
            elif bucket == "File_Hash_SHA1":
                add_artifact(artifacts, bucket, rand_sha1(), "base")
            elif bucket == "File_Hash_MD5":
                add_artifact(artifacts, bucket, rand_md5(), "base")

        # Apply Scenario
        apply_scenario(scenario, artifacts, theme_values)

        # Build SOCFramework object
        socfw = {
            "Artifacts": artifacts,
            "Product": product,
            "shadow_mode": shadowmode
        }

        # Write to context
        demisto.setContext("SOCFramework", socfw)

        # Return HR
        demisto.results({
            "Type": 1,
            "ContentsFormat": "json",
            "Contents": json.dumps(socfw, indent=2)
        })

    except Exception as e:
        demisto.results(f"SOCFramework-TestContext Error: {e}\n{traceback.format_exc()}")


if __name__ in ("__main__", "__builtin__", "builtins"):
    main()
