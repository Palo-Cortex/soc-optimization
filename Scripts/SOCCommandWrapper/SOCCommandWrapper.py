import demistomock as demisto  # noqa: F401
from CommonServerPython import *  # noqa: F401
def main():
    args = demisto.args()

    command = args.get("command")
    arg_names = args.get("args_map", [])
    artifacts = args.get("artifacts", {})

    resolved = demisto.get(demisto.context(), "SOCFramework.ResolvedArtifacts") or {}

    exec_args = {}

    for arg in arg_names:
        value = None

        # Direct match
        if arg in resolved:
            value = resolved[arg]
        else:
            # match based on last token (“guid”, “endpoint_id”, etc.)
            for k, v in resolved.items():
                if arg in k or arg in str(v):
                    value = v
                    break

        if not value:
            return demisto.results({
                "success": False,
                "error": f"Missing argument: {arg}"
            })

        exec_args[arg] = value

    try:
        result = demisto.executeCommand(command, exec_args)
    except Exception as e:
        return demisto.results({"success": False, "error": str(e)})

    demisto.setContext("SOCFramework.ActionOutput", result)

    demisto.results({
        "success": True,
        "command_executed": command,
        "args_used": exec_args,
        "raw_result": result
    })


if __name__ in ("__builtin__", "builtins", "__main__"):
    main()
