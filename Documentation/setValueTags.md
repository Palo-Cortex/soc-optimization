# 🏷️ `setValueTags` Script Usage

The `setValueTags` script manages the `value_tags` lookup table in Cortex XSIAM. This table powers dashboards that track how and where automation is delivering value in your SOC.

---

## 📌 Purpose

Use this script to **add**, **update**, or **delete** individual records in the `value_tags` dataset. Each record represents either:

- A **playbook** use case (category: `use_case`)
- A **task** (enrichment, triage, remediation, etc.)

---

## 📋 Parameters

| Parameter     | Required (Playbook) | Required (Task) | Description                              |
|---------------|---------------------|------------------|------------------------------------------|
| `action`      | ✅                  | ✅               | `add`, `update`, or `delete`             |
| `tag`         | ✅                  | ✅               | Name of the use case or task label       |
| `time`        | ✅                  | ✅               | Time value in seconds                    |
| `playbookid`  | ✅                  |                  | ID of the playbook                       |
| `scriptid`    |                     | ✅               | Script or command executed (e.g. `ip=8.8.8.8`) |
| `taskname`    | optional            | optional         | Display name for the task or playbook    |
| `product`     | optional            | optional         | Name of the product used in automation   |
| `vendor`      | optional            | optional         | Vendor associated with the product       |
| `category`    | fixed: `use_case`   | ✅               | Task category (e.g. enrichment, triage)  |

---

## 🧠 Usage Examples

### ➕ Add a Playbook Entry
```bash
!setValueTags action=add tag=Malware_Hunt time=120 playbook_name="Hunting - Malware" product="XDR" vendor="Palo Alto"
```

### ➕ Add a Task Entry
```bash
!setValueTags action=add type=task category=enrichment tag=domain_lookup time=3 scriptid=DomainTools.V2
```

### ✏️ Update a Tag
```bash
!setValueTags action=update tag=Malware_Hunt time=150 vendor="Updated Vendor"
```

### ❌ Delete a Tag
```bash
!setValueTags action=delete tag=Malware_Hunt
```

---

## ⚠️ Error Handling

- `add`: Fails if required fields are missing
- `update`: Only `tag` is required; all other fields are optional
- `delete`: Requires only the `tag`

The script will safely **exit without updating the table** if validation fails.

---

## 📊 How It Powers Dashboards

Dashboards rely on the `value_tags` lookup to:

- Group metrics by use case
- Track time savings across enrichment, triage, remediation
- Show vendor/product utilization
- Compare custom vs. built-in playbook usage

This enables SOC leaders to quantify automation ROI and analyst workload impact.

---

## 📁 File Location

You can find the script in this repository under:

```
scripts/setValueTags.py
```

