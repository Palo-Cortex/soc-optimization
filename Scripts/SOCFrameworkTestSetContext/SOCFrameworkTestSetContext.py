import demistomock as demisto  # noqa: F401
from CommonServerPython import *  # noqa: F401
def main():
    args = demisto.args()
    key = args.get("key")
    value = args.get("value")

    if not key:
        return demisto.results("Missing key parameter.")

    demisto.setContext(key, value)
    demisto.results({"success": True, "key": key, "value": value})


if __name__ in ("__builtin__", "builtins", "__main__"):
    main()
