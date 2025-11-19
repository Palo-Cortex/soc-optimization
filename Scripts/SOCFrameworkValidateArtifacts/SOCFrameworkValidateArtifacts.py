import demistomock as demisto  # noqa: F401
from CommonServerPython import *  # noqa: F401
import json

def resolve_value(artifact_key, runtime_artifacts, catalog_entry):
    """Try all catalog source paths until one returns a value."""
    for path in catalog_entry.get("sources", []):
        # strip SOCFramework.Artifacts prefix
        key = path.replace("SOCFramework.Artifacts.", "")
        value = demisto.get(runtime_artifacts, key)
        if value:
            return value
    return None

def main():
    args = demisto.args()
    required = args.get("required", [])
    # Normalize required → always a list
    if isinstance(required, str):
        # handles: "email.message_id"
        # handles: "email.message_id, file.sha256"
        required = [r.strip() for r in required.split(",") if r.strip()]

    runtime_artifacts = args.get("artifacts", {})

    # Load SOC_Artifacts list
    raw = demisto.executeCommand("getList", {"listName": "SOC_Artifacts"})
    if not raw or "Contents" not in raw[0]:
        return demisto.results("List 'SOC_Artifacts' not found or empty.")

    try:
        catalog = json.loads(raw[0]["Contents"]).get("Artifacts", {})
    except Exception as e:
        return demisto.results(f"Invalid JSON in SOC_Artifacts list: {e}")

    resolved = {}
    missing = []

    for artifact_key in required:
        cat_entry = catalog.get(artifact_key)
        if not cat_entry:
            missing.append(artifact_key)
            continue

        value = resolve_value(artifact_key, runtime_artifacts, cat_entry)
        if value:
            resolved[artifact_key] = value
        else:
            missing.append(artifact_key)

    demisto.setContext("SOCFramework.ResolvedArtifacts", resolved)

    demisto.results({
        "success": len(missing) == 0,
        "resolved": resolved,
        "missing": missing
    })


if __name__ in ("__builtin__", "builtins", "__main__"):
    main()
