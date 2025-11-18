import demistomock as demisto  # noqa: F401
from CommonServerPython import *  # noqa: F401
#!/usr/bin/env python3

import json
import traceback

# ============================================================================
#  CANONICAL ARTIFACT BUCKET SCHEMA  (must match TestContext)
# ============================================================================
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
    """Create empty canonical artifact buckets."""
    return {bucket: [] for bucket in CANONICAL_BUCKETS}


# ============================================================================
#  HELPERS
# ============================================================================

def normalize_list(value):
    """Return a list of clean strings from any type."""
    if value is None:
        return []

    if isinstance(value, list):
        vals = []
        for v in value:
            if isinstance(v, (str, int, float)):
                vals.append(str(v))
        return vals

    if isinstance(value, (str, int, float)):
        return [str(value)]

    # Try JSON loading
    try:
        loaded = json.loads(value)
        if isinstance(loaded, list):
            return [str(x) for x in loaded]
        return [str(loaded)]
    except Exception:
        return []


# ============================================================================
#  SIMPLE MERGE LOGIC
#  - if value exists, keep it
#  - if value not present, add it
#  - we DO NOT override sources anymore
# ============================================================================
def add_to_bucket(struct, bucket, value, source):
    """Merge: if value not present, add; if present, do nothing."""
    if bucket not in struct:
        return

    for entry in struct[bucket]:
        if entry["value"] == value:
            # Already there, keep existing source
            return

    struct[bucket].append({
        "value": value,
        "source": source
    })


# ============================================================================
# FIELD → BUCKET MAPPING (used for Issue & generic key extraction)
# ============================================================================
def map_field_to_bucket(field_key, values):
    k = field_key.lower()

    # IP
    if k in ("ip", "ips", "sourceip", "srcip", "dstip", "remoteip"):
        return "IP", values

    # Domain
    if k in ("domain", "alert_domain"):
        return "Domain", values

    # URL
    if "url" in k or "externallink" in k:
        return "URL", values

    # Email
    if k in ("emailsender", "emailfrom"):
        return "Email_Sender", values
    if k in ("emailrecipient", "emailto"):
        return "Email_Recipient", values
    if k in ("emailsubject", "subject"):
        return "Email_Subject", values
    if k in ("emailreplyto", "replyto"):
        return "Email_ReplyTo", values
    if k in ("emaildisplayname", "senderdisplayname"):
        return "Email_DisplayName", values

    # MITRE
    if k in ("mitretechniqueid", "mitretechniquename"):
        return "MITRE_Technique", values
    if k in ("mitretacticid", "mitretacticname"):
        return "MITRE_Tactic", values

    # Generic tactic field
    if k in ("tactic", "tactics"):
        return "Tactic", values

    # Attack pattern
    if k == "attack_pattern":
        return "Attack_Pattern", values

    # File path
    if k in ("filepath", "file_path"):
        return "File_Path", values

    # File name
    if k in ("filename", "file_name"):
        return "File_Name", values

    # Hashes (if they exist as standalone fields)
    if k == "sha256":
        return "File_Hash_SHA256", values
    if k == "sha1":
        return "File_Hash_SHA1", values
    if k == "md5":
        return "File_Hash_MD5", values

    return None, None


# ============================================================================
#  HASH INFERENCE FOR ExtractedIndicators["File"]
# ============================================================================
def infer_hash_bucket(file_value):
    """Infer hash bucket by length."""
    length = len(file_value)
    if length == 64:
        return "File_Hash_SHA256"
    if length == 40:
        return "File_Hash_SHA1"
    if length == 32:
        return "File_Hash_MD5"
    return "File_Name"


# ============================================================================
#  ExtractedIndicators parser (MATCHES YOUR REAL STRUCTURE)
# ============================================================================
def parse_extracted_indicators(raw_list, out_struct):
    """
    Your ExtractedIndicators is a list of DICT PACKS:
     [
       {
         "Attack_Pattern": [...],
         "Domain": [...],
         "File": [...],
         "IP": [...],
         "Tactic": [...],
         "URL": [...]
       },
       ...
     ]
    """
    if not isinstance(raw_list, list):
        return

    for pack in raw_list:
        if not isinstance(pack, dict):
            continue

        for key, raw_vals in pack.items():
            vals = normalize_list(raw_vals)
            if not vals:
                continue

            bucket = None

            # Direct bucket name match:
            if key in CANONICAL_BUCKETS:
                bucket = key

            # Handle File specially
            elif key.lower() == "file":
                for fv in vals:
                    b = infer_hash_bucket(fv)
                    add_to_bucket(out_struct, b, fv, "ExtractedIndicators.File")
                continue

            # Map via field mapping
            else:
                bucket, mapped_vals = map_field_to_bucket(key, vals)
                if bucket:
                    for v in mapped_vals:
                        add_to_bucket(out_struct, bucket, v, f"ExtractedIndicators.{key}")
                continue

            # If we got a direct canonical bucket
            if bucket:
                for v in vals:
                    add_to_bucket(out_struct, bucket, v, f"ExtractedIndicators.{key}")


# ============================================================================
#  GENERIC OBJECT PARSER (Issue-like dicts, other dict keys)
# ============================================================================
def extract_from_object(obj, prefix):
    out = new_artifact_struct()

    if isinstance(obj, dict):
        merged = {}
        merged.update(obj)
        cf = obj.get("CustomFields") or obj.get("fields") or {}
        merged.update(cf)

        for key, value in merged.items():
            vals = normalize_list(value)
            if not vals:
                continue

            bucket, mapped_vals = map_field_to_bucket(key, vals)
            if bucket:
                for v in mapped_vals:
                    add_to_bucket(out, bucket, v, f"{prefix}.{key}")

    return out


# ============================================================================
# MERGE TWO ARTIFACT STRUCTS
# ============================================================================
def merge_structs(existing, new_items):
    """Merge new_items INTO existing with add-only semantics."""
    for bucket in CANONICAL_BUCKETS:
        for entry in new_items[bucket]:
            add_to_bucket(existing, bucket, entry["value"], entry["source"])


# ============================================================================
# MAIN
# ============================================================================
def main():
    try:
        args = demisto.args()
        key = args.get("key")
        if not key:
            demisto.results("Error: key=<context key> required.")
            return

        # Don't normalize SOCFramework itself (avoid recursion / corruption)
        if key.lower().startswith("socframework"):
            demisto.results("Refusing to normalize 'SOCFramework' key to avoid recursion.")
            return

        # ----------------------------------------------------------------------
        # LOAD CONTEXT AND EXISTING SOCFRAMEWORK ROOT
        # ----------------------------------------------------------------------
        ctx = demisto.context() or {}

        socfw = ctx.get("SOCFramework")
        if not isinstance(socfw, dict):
            # Initialize SOCFramework root (Option 3, shadow_mode: true)
            socfw = {
                "Artifacts": new_artifact_struct(),
                "Product": {
                    "category": "",
                    "type": "",
                    "confidence": "",
                    "key": ""
                },
                "shadow_mode": True
            }

        artifacts = socfw.get("Artifacts") or new_artifact_struct()

        # ----------------------------------------------------------------------
        # SPECIAL CASE: ISSUE (use demisto.incidents(), not context)
        # ----------------------------------------------------------------------
        if key.lower() == "issue":
            incs = demisto.incidents() or []
            issue_obj = incs[0] if incs else None
            if not issue_obj:
                demisto.results("Issue not found via demisto.incidents().")
                return

            temp = extract_from_object(issue_obj, "issue")
            merge_structs(artifacts, temp)

        else:
            # ------------------------------------------------------------------
            # GET RAW VALUE FOR NON-ISSUE KEY FROM CONTEXT
            # ------------------------------------------------------------------
            raw = ctx.get(key)
            if raw is None:
                demisto.results(f"Key '{key}' not found in context.")
                return

            # ExtractedIndicators
            if key == "ExtractedIndicators":
                temp = new_artifact_struct()
                parse_extracted_indicators(raw, temp)
                merge_structs(artifacts, temp)

            # Dict
            elif isinstance(raw, dict):
                temp = extract_from_object(raw, key)
                merge_structs(artifacts, temp)

            # Scalar / list / other
            else:
                vals = normalize_list(raw)
                temp = new_artifact_struct()
                bucket, mapped_vals = map_field_to_bucket(key, vals)
                if bucket:
                    for v in mapped_vals:
                        add_to_bucket(temp, bucket, v, key)
                merge_structs(artifacts, temp)

        # ----------------------------------------------------------------------
        # WRITE BACK UPDATED STRUCTURE
        # ----------------------------------------------------------------------
        socfw["Artifacts"] = artifacts
        demisto.setContext("SOCFramework", socfw)

        demisto.results(f"SOCFramework.Artifacts updated from key '{key}'.")

    except Exception as e:
        demisto.results(f"Error in SOCFramework-NormalizeKeyToArtifacts: {e}\n{traceback.format_exc()}")


if __name__ in ("__main__", "__builtin__", "builtins"):
    main()
