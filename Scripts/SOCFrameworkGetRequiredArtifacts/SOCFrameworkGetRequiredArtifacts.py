import demistomock as demisto  # noqa: F401
from CommonServerPython import *  # noqa: F401
import json

def main():
    args = demisto.args()
    action = args.get("action")

    # Load list content
    res = demisto.executeCommand("getList", {"listName": "SOC_FrameworkActions"})
    if not res or "Contents" not in res[0]:
        return demisto.results("List 'SOC_FrameworkActions' not found or empty.")

    try:
        data = json.loads(res[0]["Contents"])
    except Exception as e:
        return demisto.results(f"Invalid JSON in SOC_FrameworkActions list: {e}")

    actions = data.get("Actions", {})
    required = actions.get(action, {}).get("required_artifacts", [])

    demisto.setContext("SOCFramework.RequiredArtifacts", required)

    demisto.results({"required_artifacts": required})


if __name__ in ("__builtin__", "builtins", "__main__"):
    main()
