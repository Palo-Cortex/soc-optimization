import demistomock as demisto  # noqa: F401
from CommonServerPython import *  # noqa: F401
import json

# List of jobs to delete
jobs_to_remove = [
    "Auto Triage",
    "Collect Playbook Metrics"
]

# Manual cleanup instructions
manual_cleanup = """
⚠️ Manual cleanup required:

- Uninstall the following content packs via Marketplace > Installed Packs:
    • POV Content Pack
    • SOC Framework
    • Playbook / Automation Triggers

- Remove the following integration instances via Settings > Integrations:
    • Core REST API - Standard XSIAM API Key Cred (Core REST API)
    • PlaybookMetrics (System XQL HTTP Collector - Community Contribution)
    • Triggers (MITRE Execution, MITRE Initial Access)
"""

def delete_job_by_name(job_name):
    # Search for the job
    res = demisto.executeCommand("core-api-post", {
        "uri": "/xsoar/public/v1/jobs/search",
        "body": json.dumps({
            "query": job_name,
            "page": 0,
            "size": 100
        })
    })

    if not res or not isinstance(res[0].get("Contents"), dict):
        print(f"❌ Could not fetch jobs for: {job_name}")
        return

    jobs = res[0]["Contents"].get("response", {}).get("data", [])

    for job in jobs:
        if job.get("name") == job_name:
            job_id = job.get("id")
            print(f"🗑️ Deleting job: {job_name} ({job_id})")
            delete_res = demisto.executeCommand("core-api-delete", {
                "uri": f"/xsoar/public/v1/jobs/{job_id}"
            })
            print(f"✅ Delete response: {delete_res}")
            return

    print(f"⚠️ Job not found: {job_name}")

# Run the job deletions
for job in jobs_to_remove:
    delete_job_by_name(job)

# Print manual cleanup steps
print(manual_cleanup)

# Final message
return_results("✅ SOC Framework cleanup script executed.")
