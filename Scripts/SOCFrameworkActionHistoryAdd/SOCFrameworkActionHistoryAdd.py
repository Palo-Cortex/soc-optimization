import demistomock as demisto  # noqa: F401
from CommonServerPython import *  # noqa: F401
from datetime import datetime

def main():
    args = demisto.args()

    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "product_category": args.get("product_category",""),
        "brand_source": args.get("brand_source",""),
        "action": args.get("action",""),
        "command_executed": args.get("command",""),
        "output": args.get("output",{})
    }

    existing = demisto.get(demisto.context(), "SOCFramework.ActionHistory")
    if not isinstance(existing, list):
        existing = []

    demisto.setContext("SOCFramework.ActionHistory", existing + [entry])

    demisto.results({"success": True, "entry_added": entry})


if __name__ in ("__main__", "__builtin__", "builtins"):
    main()
