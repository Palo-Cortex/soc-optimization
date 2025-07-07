from datetime import datetime
import json

def validate_playbook_exists(playbook_name):
    query_body = {"query": playbook_name}

    res = demisto.executeCommand("core-api-post", {
        "uri": "/xsoar/public/v1/playbook/search",
        "body": json.dumps(query_body)
    })

    if isError(res):
        print(f"❌ Error calling core-api-post for '{playbook_name}': {get_error(res)}")
        return False

    try:
        contents = res[0].get("Contents", {})
        if isinstance(contents, str):
            contents = json.loads(contents)

        result_data = contents.get("response", {})
    except Exception as e:
        print(f"❌ Unexpected response format for '{playbook_name}': {str(e)}")
        return False

    if len(result_data.get('playbooks', [])) < 1:
        return False
    else:
        print(result_data['playbooks'][0]['name'])
        return True

def main():
    try:
        ep_name = demisto.args().get("entry_point_name")
        playbook_name = demisto.args().get("playbook_name", "")
        action = demisto.args().get("action")
        list_name = "PlaybookDeploymentMatrix"

        if not action:
            return_error("Missing required argument: 'action'")

        res = demisto.executeCommand("getList", {"listName": list_name})
        if isError(res[0]):
            return_error(f"Failed to retrieve list: {res[0]['Contents']}")

        raw_data = res[0]["Contents"]
        data = json.loads(raw_data) if isinstance(raw_data, str) else raw_data

        if action == "list":
            result_lines = [
                f"- **{ep.get('name')}**: {'✅ Enabled' if ep.get('enabled', True) else '🚫 Disabled'} | 🟢 Prod: {ep.get('prod', '')} | 🧪 Green: {ep.get('green', '')}"
                for ep in data
            ]
            return_results("\n".join(result_lines))
            return

        if action == "create":
            if not ep_name:
                return_error("Missing required argument: 'entry_point_name' for create action")
            if any(item.get("name") == ep_name for item in data):
                return_error(f"Entry Point '{ep_name}' already exists.")
            new_entry = {
                "name": ep_name,
                "enabled": False,
                "deployment": "prod",
                "prod": "",
                "green": ""
            }
            data.append(new_entry)
            demisto.executeCommand("setList", {
                "listName": list_name,
                "listData": json.dumps(data)
            })
            return_results(f"🆕 Created new Entry Point: **{ep_name}** (disabled by default)")
            return

        if action == "delete":
            if not ep_name:
                return_error("Missing required argument: 'entry_point_name' for delete action")
            data = [item for item in data if item.get("name") != ep_name]
            demisto.executeCommand("setList", {
                "listName": list_name,
                "listData": json.dumps(data)
            })
            return_results(f"🗑️ Deleted Entry Point: **{ep_name}**")
            return

        if not ep_name:
            return_error("Missing required argument: 'entry_point_name'")

        entry = next((item for item in data if item.get("name") == ep_name), None)
        if not entry:
            return_error(f"No entry found for Entry Point: {ep_name}")

        if action not in ("enable", "disable", "show") and not entry.get("enabled", True):
            return_error(f"⚠️ Entry Point '{ep_name}' is currently disabled.")

        if action == "show":
            deployed_prod = entry.get("prod", "")
            staged_green = entry.get("green", "")
            enabled_status = "✅ Enabled" if entry.get("enabled", True) else "🛑 Disabled"
            result = (
                f"📌 **Playbook Status for {ep_name}**\n"
                f"• {enabled_status}\n"
                f"• 🟢 Prod: **{deployed_prod}**\n"
                f"• 🧪 Green: **{staged_green}**"
            )
            return_results(result)
            return

        elif action == "enable":
            entry["enabled"] = True
            message = f"✅ Entry Point '{ep_name}' has been **enabled**."

        elif action == "disable":
            entry["enabled"] = False
            message = f"🛑 Entry Point '{ep_name}' has been **disabled**."

        elif action == "stage":
            if not playbook_name:
                return_error("Missing 'playbook_name' for stage action.")
            if not validate_playbook_exists(playbook_name):
                return_error(f"⚠️ Playbook '{playbook_name}' does not exist")
            entry["green"] = playbook_name
            message = f"🧪 Staged new green playbook for {ep_name}: **{playbook_name}**"

        elif action == "deploy":
            green_candidate = entry.get("green")
            if not green_candidate:
                return_error(f"No green candidate is currently staged for {ep_name}.")
            if not validate_playbook_exists(green_candidate):
                return_error(f"The staged green playbook '{green_candidate}' does not exist or is inaccessible.")
            old_prod = entry.get("prod")
            entry["backup"] = {
                "playbook": old_prod,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            entry["prod"] = green_candidate
            entry["green"] = old_prod
            entry["deployment"] = "prod"
            message = (
                f"✅ Deployed green → prod for {ep_name}.\n"
                f"Promoted: **{green_candidate}**\n"
                f"Demoted: **{old_prod}**\n"
                f"📦 Backup saved with timestamp: {entry['backup']['timestamp']}"
            )

        elif action == "rollback":
            old_green = entry.get("green")
            old_prod = entry.get("prod")
            if not old_green or not old_prod:
                return_error(f"Cannot rollback — missing green or prod value for {ep_name}.")
            entry["backup"] = {
                "playbook": old_prod,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            entry["prod"] = old_green
            entry["green"] = old_prod
            entry["deployment"] = "prod"
            message = (
                f"↩️ Rolled back playbooks for {ep_name}.\n"
                f"Restored: **{old_green}** as prod\n"
                f"Moved: **{old_prod}** back to green\n"
                f"📦 Backup saved with timestamp: {entry['backup']['timestamp']}"
            )

        else:
            return_error("Invalid action. Use 'list', 'create', 'delete', 'show', 'stage', 'deploy', 'rollback', 'enable', or 'disable'.")

        if action in ("stage", "deploy", "rollback", "enable", "disable"):
            demisto.executeCommand("setList", {
                "listName": list_name,
                "listData": json.dumps(data)
            })

        return_results(message)

    except Exception as e:
        return_error(f"Script error: {str(e)}")

main()