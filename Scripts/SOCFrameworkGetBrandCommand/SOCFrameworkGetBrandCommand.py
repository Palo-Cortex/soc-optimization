import demistomock as demisto  # noqa: F401
from CommonServerPython import *  # noqa: F401
import json

def main():
    args = demisto.args()
    brand = args.get("brand_source")
    action = args.get("action")

    # Load list from XSIAM
    res = demisto.executeCommand("getList", {"listName": "SOC_VendorCapabilities"})
    if not res or "Contents" not in res[0]:
        return demisto.results("List 'SOC_VendorCapabilities' not found or empty.")

    try:
        vcaps = json.loads(res[0]["Contents"]).get("VendorCapabilities", {})
    except Exception as e:
        return demisto.results(f"Invalid JSON in SOC_VendorCapabilities list: {e}")

    brand_entry = vcaps.get(brand)
    if not brand_entry:
        return demisto.results({"success": False, "error": f"Brand '{brand}' not found."})

    action_entry = brand_entry.get(action)
    if not action_entry:
        return demisto.results({
            "success": False,
            "error": f"Brand '{brand}' does not support action '{action}'."
        })

    demisto.setContext("SOCFramework.BrandCommand", action_entry)

    demisto.results({
        "success": True,
        "command": action_entry.get("command"),
        "args": action_entry.get("args")
    })


if __name__ in ("__builtin__", "builtins", "__main__"):
    main()
