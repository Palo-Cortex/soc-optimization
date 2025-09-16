import demistomock as demisto  # noqa: F401
from CommonServerPython import *  # noqa: F401
def main():
    try:
        trigger_name = demisto.args().get("entrypoint_name")
        list_name = demisto.args().get("list_name", "PlaybookDeploymentMatrix")

        if not trigger_name:
            return_error("Missing 'entrypoint_name' argument")

        # Get list contents
        res = demisto.executeCommand("getList", {"listName": list_name})
        if isError(res[0]):
            return_error(f"Failed to retrieve list: {res[0]['Contents']}")

        json_data = res[0]["Contents"]
        matrix = json.loads(json_data) if isinstance(json_data, str) else json_data

        # Find the entry by name
        match = next((item for item in matrix if item.get("name") == trigger_name and item.get("enabled", True)), None)

        if not match:
            return_error(f"No enabled entry found for trigger: {trigger_name}")

        deployment = match.get("deployment", "prod")
        playbook_name = match.get(deployment)

        if not playbook_name:
            return_error(f"Deployment '{deployment}' not defined for trigger: {trigger_name}")

        return_results({
            "Type": entryTypes["note"],
            "ContentsFormat": formats["json"],
            "Contents": {"playbook_name": playbook_name,"deployment": deployment},
            "EntryContext": {"PlaybookRouting.Playbook.Name": playbook_name,"PlaybookRouting.Playbook.Deployment": deployment}
        })

    except Exception as e:
        return_error(f"Script error: {str(e)}")


main()
