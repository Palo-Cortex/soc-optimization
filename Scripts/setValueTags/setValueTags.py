import demistomock as demisto  # noqa: F401
from CommonServerPython import *  # noqa: F401
import json

# Inputs
action = demisto.args().get("action", "add").lower()
entry_type = demisto.args().get("type", "playbook").lower()
tag = demisto.args().get("tag", "").strip()
time = demisto.args().get("time", "").strip()
category = demisto.args().get("category", "").strip()
taskname = demisto.args().get("playbook_name", "").strip()
product = demisto.args().get("product", "").strip()
vendor = demisto.args().get("vendor", "").strip()
playbookid = demisto.args().get("playbookid", "").strip()
scriptid = demisto.args().get("scriptid", "").strip()
output_format = demisto.args().get("output_format", "markdown").strip().lower()

table_name = "value_tags"
changed = 0

# --- Validation for actions ---
if action not in ["add", "update", "delete", "list_by_type", "list_by_tag_or_name", "list_all"]:
    return_error(f"Invalid action: {action}. Use 'add', 'update', 'delete', 'list_by_type', 'list_by_tag_or_name', or 'list_all'.")

if output_format not in ["json", "table", "markdown"]:
    return_error("Invalid output_format. Use 'json', 'table', or 'markdown'.")

# --- ADD Validation ---
if action == "add":
    if not tag:
        return_error("Add action requires a non-empty tag.")
    if entry_type == "task":
        if not all([tag, time, category, scriptid]):
            return_error("Task add failed. Required fields: tag, time, category, scriptid.")
    elif entry_type == "playbook":
        if not time:
            return_error("Playbook add failed. Missing required field: time.")
        if not playbookid and not taskname:
            return_error("Playbook add failed. Provide either playbookid or playbook_name.")
    else:
        return_error("Invalid type. Use 'playbook' or 'task'.")

# --- Playbook Lookup if Needed ---
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

# --- Build Row Data ---
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
    if not tag:
        return_error("Update action requires a tag.")
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

# --- Perform Write Actions ---
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
    if not tag:
        return_error("Delete action requires a tag.")
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

# --- Table Cleanup Helper ---
def clean_rows(rows):
    display_keys = ["Category", "PlaybookID", "Product", "ScriptID", "Tag", "TaskName", "Time", "Vendor"]
    cleaned_rows = []
    for row in rows:
        cleaned_row = {key: str(row.get(key, "") or "") for key in display_keys}
        cleaned_rows.append(cleaned_row)
    return cleaned_rows

# --- Format Output ---
def format_output(rows):
    cleaned = clean_rows(rows)

    if output_format == "json":
        return_results(json.dumps(cleaned, indent=2))

    elif output_format == "table":
        if cleaned:
            markdown = tableToMarkdown("Value Tags Table", cleaned)
            return_results(markdown)
        else:
            return_results("No results found.")

    else:  # markdown
        markdown = tableToMarkdown("Lookup Table Results", cleaned) if cleaned else "No entries found."
        return_results(markdown)

# --- Read Actions ---
if action in ["list_by_type", "list_by_tag_or_name", "list_all"]:
    fetch_body = {"request": {"dataset_name": table_name}}

    if action == "list_by_tag_or_name":
        filters = []
        if tag:
            filters.append({"tag": tag})
        if taskname:
            filters.append({"taskname": taskname})
        if not filters:
            return_error("Must provide 'tag' or 'playbook_name'.")
        fetch_body["request"]["filters"] = filters

    result = demisto.executeCommand("core-api-post", {
        "uri": "/public_api/v1/xql/lookups/get_data",
        "body": json.dumps(fetch_body)
    })

    if isError(result):
        return_error(f"Fetch failed: {get_error(result)}")

    contents = result[0].get("Contents", {})
    if isinstance(contents, str):
        contents = json.loads(contents)

    rows = contents.get("response", {}).get("reply", {}).get("data", [])

    if action == "list_by_type":
        filtered = []
        for r in rows:
            cat = r.get("Category", "").lower()
            if entry_type == "playbook" and cat == "use_case":
                filtered.append(r)
            elif entry_type == "task" and cat != "use_case":
                filtered.append(r)
        format_output(filtered)
    else:
        format_output(rows)

# --- Final Write Response ---
if changed:
    return_results(f"{action.capitalize()}d {tag} in the '{table_name}' lookup table.")
elif action in ["add", "update", "delete"]:
    return_results(f"No changes made for tag '{tag}'.")
