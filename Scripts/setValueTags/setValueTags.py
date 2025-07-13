import demistomock as demisto  # noqa: F401
from CommonServerPython import *  # noqa: F401
import json
import sys

# Inputs
action = demisto.args().get("action", "add").lower()
entry_type = demisto.args().get("type", "playbook").lower()  # "playbook" or "task"
tag = demisto.args().get("tag", "").strip()
time = demisto.args().get("time", "").strip()
category = demisto.args().get("category", "").strip()
taskname = demisto.args().get("playbook_name", "").strip()
product = demisto.args().get("product", "").strip()
vendor = demisto.args().get("vendor", "").strip()
playbookid = demisto.args().get("playbookid", "").strip()
scriptid = demisto.args().get("scriptid", "").strip()

table_name = "value_tags"
changed = 0

# --- Global validation ---
if action not in ["add", "update", "delete"]:
    return_error(f"Invalid action: {action}. Use 'add', 'update', or 'delete'.")
if not tag:
    return_error(f"{action.capitalize()} action requires a non-empty tag.")

# --- ADD: Required field validation with value checks ---
if action == "add":
    if entry_type == "task":
        if not all([tag, time, category, scriptid]):
            return_error("Task add failed. Required fields must have values: tag, time, category, scriptid.")
    elif entry_type == "playbook":
        if not time:
            return_error("Playbook add failed. Missing required field: time.")
        if not playbookid and not taskname:
            return_error("Playbook add failed. Provide either playbookid or playbook_name.")
    else:
        return_error(f"Invalid type: {entry_type}. Use 'playbook' or 'task'.")

# --- Lookup playbookid if needed ---
if action == "add" and entry_type == "playbook" and not playbookid:
    search_body = {"query": taskname}
    search_result = demisto.executeCommand("core-api-post", {
        "uri": "/xsoar/public/v1/playbook/search",
        "body": json.dumps(search_body)
    })

    if isError(search_result):
        return_error(f"Playbook lookup failed: {get_error(search_result)}")

    try:
        contents = search_result[0].get("Contents", {})
        if isinstance(contents, str):
            contents = json.loads(contents)
        result_data = contents.get("response", {})
        playbooks = result_data.get("playbooks", [])
    except Exception as e:
        return_error(f"Error parsing playbook search results: {str(e)}")

    if not playbooks:
        return_error(f"No playbook found with name: {taskname}")

    playbookid = playbooks[0]["id"]

# --- Build row_data ---
row_data = {"tag": tag}

if action == "add":
    row_data["time"] = time
    if product:
        row_data["product"] = product
    if vendor:
        row_data["vendor"] = vendor
    if taskname:
        row_data["taskname"] = taskname

    if entry_type == "playbook":
        row_data["playbookid"] = playbookid
        row_data["category"] = "use_case"
    elif entry_type == "task":
        row_data["scriptid"] = scriptid
        row_data["category"] = category

elif action == "update":
    if time:
        row_data["time"] = time
    if category:
        row_data["category"] = category
    if playbookid:
        row_data["playbookid"] = playbookid
    if scriptid:
        row_data["scriptid"] = scriptid
    if taskname:
        row_data["taskname"] = taskname
    if product:
        row_data["product"] = product
    if vendor:
        row_data["vendor"] = vendor

# --- Perform Action ---
if action in ["add", "update"]:
    if len(row_data) > 1:
        body = {
            "request": {
                "dataset_name": table_name,
                "key_fields": ["tag"],
                "data": [row_data]
            }
        }
        demisto.executeCommand("core-api-post", {
            "uri": "/public_api/v1/xql/lookups/add_data",
            "body": json.dumps(body)
        })
        changed = 1

elif action == "delete":
    delete_body = {
        "request": {
            "dataset_name": table_name,
            "filters": [{"tag": tag}]
        }
    }
    demisto.executeCommand("core-api-post", {
        "uri": "/public_api/v1/xql/lookups/remove_data",
        "body": json.dumps(delete_body)
    })
    changed = 1

# --- Final response ---
if changed:
    return_results(f"{action.capitalize()}d {tag} in the '{table_name}' lookup table.")
else:
    return_results(f"No changes made for tag '{tag}'.")
