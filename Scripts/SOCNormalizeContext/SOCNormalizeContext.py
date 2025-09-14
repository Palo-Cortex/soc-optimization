demisto.debug('pack name = SOC Framework, pack version = 2.0.0')

# SOC_NormalizeContext_v11 (Readable + PID normalization)
# Cortex XSIAM / XSOAR Automation (Python 3)
#
# Outputs (Context + Set):
#   Normalized, NormalizedEntity, AlertCategories, ActiveProducts
#
# Normalizes: domain, user(s), ip(s), url(s), email, process(es), pid/ppid
# Notes:
# - Primary entity precedence: email > url > user > process > host > ip > cloud
# - Process canonical_id priority: sha256 > sha1 > md5 > path > filename
# - Email primary uses "recipients" (plural) to match downstream playbooks
# - Marks known-good system binary cmd.exe in System32 as system_binary=true
# - Adds Normalized.pids / Normalized.ppids and backfills process.runtime.{pid,ppid}

import re
from urllib.parse import urlsplit, urlunsplit, quote, unquote

# ---------------------------
# Small, safe utility helpers
# ---------------------------

def ci_dict(d):
    """Lower-case keys of a dict (safe for None)."""
    if not isinstance(d, dict):
        return {}
    return {str(k).lower(): v for k, v in d.items()}

def ensure_list(x):
    """Return x as a list, splitting strings on ',' or ';' when appropriate."""
    if x is None:
        return []
    if isinstance(x, list):
        return x
    if isinstance(x, (tuple, set)):
        return list(x)
    if isinstance(x, str) and (',' in x or ';' in x):
        parts = re.split(r'[;,]\s*', x)
        return [p for p in parts if p]
    return [x]

def first_nonempty(*vals):
    """First value that is not empty string/None/[]/{}."""
    for v in vals:
        if isinstance(v, str) and v.strip():
            return v.strip()
        if v not in (None, "", [], {}):
            return v
    return None

def prune_empty(d):
    """Remove keys with empty values; keep non-dict values untouched."""
    if not isinstance(d, dict):
        return d
    return {k: v for k, v in d.items() if v not in (None, "", [], {})}

# ---------------------------
# Field collectors
# ---------------------------

def gather_domain(ci):
    return first_nonempty(
        ci.get('issue.domain'),
        ci.get('issuedomain'),
        ci.get('domain'),
        ci.get('userdomain'),
        ci.get('accountdomain'),
        first_nonempty(*ensure_list(ci.get('xdmsourcehostfqdn')))
    )

def gather_usernames(ci):
    """Return (primary_user, all_usernames)."""
    keys = [
        'issue.username','username','user','actorusername','userid','user_id',
        'sourceuser','accountname','xdmsourceuserusername'
    ]
    seen, names = set(), []
    for k in keys:
        for v in ensure_list(ci.get(k)):
            s = str(v).strip()
            if s and s not in seen:
                seen.add(s); names.append(s)
    return (names[0] if names else None), names

def pick_ip_candidates(*vals):
    """Collect IPv4 candidates and dedupe (order-preserving)."""
    ips, seen, out = [], set(), []
    for v in vals:
        for item in ensure_list(v):
            s = str(item).strip()
            if re.fullmatch(r'\d{1,3}(\.\d{1,3}){3}', s):
                ips.append(s)
    for ip in ips:
        if ip not in seen:
            seen.add(ip); out.append(ip)
    return out

def gather_ips(ci):
    ips = pick_ip_candidates(
        ci.get('issue.hostip'),
        ci.get('xdmsource.ipv4addresses'),
        ci.get('xdmsourcehostipv4addresses'),
        ci.get('src'), ci.get('srcip'), ci.get('sourceip'),
        ci.get('dst'), ci.get('dstip'), ci.get('destinationip'),
        ci.get('ip')
    )
    return (ips[0] if ips else None), ips

# ---------------------------
# PID / PPID normalization
# ---------------------------

def _to_pid_str(v):
    """Return a PID/PPID as a clean string (digits only if numeric)."""
    if v is None:
        return None
    s = str(v).strip()
    return s if s else None

def _collect_ids(ci, *keys):
    """Collect values from multiple keys (each may be scalar/list), dedupe, keep order."""
    seen, out = set(), []
    for k in keys:
        for v in ensure_list(ci.get(k)):
            s = _to_pid_str(v)
            if s and s not in seen:
                seen.add(s); out.append(s)
    return out

def gather_pids(ci):
    """Return (primary_pid, all_pids, primary_ppid, all_ppids)."""
    pid_keys = [
        'issue.initiatorpid', 'initiatorpid', 'issue.pid', 'pid', 'processid',
        'xdmsourceprocessid', 'xdmsource.processid', 'xdmsourcepid', 'process.pid'
    ]
    ppid_keys = [
        'issue.initiatorppid', 'initiatorppid', 'ppid', 'parentprocessid',
        'xdmsourceprocessparentid', 'xdmsource.parentprocessid', 'process.ppid'
    ]
    pids  = _collect_ids(ci, *pid_keys)
    ppids = _collect_ids(ci, *ppid_keys)
    return (pids[0] if pids else None), pids, (ppids[0] if ppids else None), ppids

# ---------------------------
# URL normalization
# ---------------------------

_URL_RE = re.compile(r'(?i)(?P<u>(?:https?://|ftp://|www\.)[^\s<>"\'\]\)]+)')

def _canon_host(netloc):
    """Lowercase host, IDNA if needed, preserve single port if present."""
    if not netloc:
        return netloc
    try:
        host_port = netloc.split('@')[-1]  # strip userinfo if present
        if ':' in host_port and host_port.count(':') == 1:
            host, port = host_port.split(':', 1)
            return f"{host.encode('idna').decode('ascii').lower()}:{port}"
        return host_port.encode('idna').decode('ascii').lower()
    except Exception:
        return netloc.lower()

def _normalize_url_once(s):
    if not s:
        return None
    s = str(s).strip().strip('<>').strip('\'"')
    if s.lower().startswith('www.'):
        s = 'http://' + s
    m = _URL_RE.search(s)
    if m:
        s = m.group('u')
    try:
        scheme, netloc, path, query, fragment = urlsplit(s)
        scheme = (scheme or 'http').lower()
        netloc = _canon_host(netloc)
        # drop default ports
        if scheme == 'http' and netloc.endswith(':80'):
            netloc = netloc[:-3]
        if scheme == 'https' and netloc.endswith(':443'):
            netloc = netloc[:-4]
        # path normalize: decode, collapse //, re-encode; always keep a leading '/'
        path = path or '/'
        path = re.sub(r'/+', '/', unquote(path))
        path = quote(path, safe='/-._~')
        return urlunsplit((scheme, netloc, path, query, ''))
    except Exception:
        return s.strip()

def gather_urls(ci):
    raw = []
    for key in ['issue.url', 'url', 'issue.urls', 'urls']:
        raw.extend(ensure_list(ci.get(key)))
    for key in ['description', 'details', 'emailsubject', 'issue.emailsubject']:
        for s in ensure_list(ci.get(key)):
            if isinstance(s, str):
                raw.extend(m.group('u') for m in _URL_RE.finditer(s))
    seen, out = set(), []
    for item in raw:
        n = _normalize_url_once(item)
        if n and n not in seen:
            seen.add(n); out.append(n)
    return (out[0] if out else None), out

# ---------------------------
# Process building
# ---------------------------

def _norm_path(p):
    if not p:
        return None
    s = str(p).strip().strip('"').strip("'")
    # naive env expansion (do not query OS)
    for a, b in [('%SystemRoot%', 'C:\\Windows'),
                 ('%WINDIR%', 'C:\\Windows'),
                 ('$HOME', '/home'),
                 ('%HOMEPATH%', 'C:\\Users\\')]:
        s = s.replace(a, b)
    return s

def _basename(p):
    if not p:
        return None
    return p.replace('\\', '/').rstrip('/').split('/')[-1]

def _first_str_or_none(v):
    """Take first element if list/tuple, str() everything else safely."""
    if isinstance(v, (list, tuple, set)):
        v = next(iter(v), None)
    return (str(v) if v is not None else None)

def canon_proc_id(hashes, path, filename):
    """Stable canonical_id with list-safe hash handling."""
    h256 = _first_str_or_none(hashes.get('sha256'))
    h1   = _first_str_or_none(hashes.get('sha1'))
    hmd5 = _first_str_or_none(hashes.get('md5'))
    if h256: return f"sha256:{h256.lower()}"
    if h1:   return f"sha1:{h1.lower()}"
    if hmd5: return f"md5:{hmd5.lower()}"
    if path: return f"path:{str(path).lower()}"
    if filename: return f"file:{str(filename).lower()}"
    return "unknown:process"

def build_process_from_flat(ci):
    hashes = {
        "sha256": first_nonempty(ci.get('initiatorsha256'), ci.get('initiator_sha256'),
                                 ci.get('processsha256'), ci.get('process_sha256'),
                                 ci.get('sha256')),
        "sha1":   first_nonempty(ci.get('initiatorsha1'), ci.get('initiator_sha1'),
                                 ci.get('processsha1'), ci.get('process_sha1'),
                                 ci.get('sha1')),
        "md5":    first_nonempty(ci.get('initiatormd5'), ci.get('initiator_md5'),
                                 ci.get('processmd5'), ci.get('process_md5'),
                                 ci.get('md5')),
    }
    # normalize hash values to first scalar string
    hashes = {k: _first_str_or_none(v) for k, v in hashes.items() if v is not None}

    path = _norm_path(first_nonempty(ci.get('image'), ci.get('imagepath'),
                                     ci.get('executablepath'), ci.get('processpath'),
                                     ci.get('filepath')))
    filename = first_nonempty(ci.get('filename'), _basename(path))
    cmdline  = first_nonempty(ci.get('cmdline'), ci.get('commandline'), ci.get('processcommandline'))
    signer   = first_nonempty(ci.get('signer'), ci.get('signature'), ci.get('signaturestatus'))
    pid      = first_nonempty(ci.get('pid'), ci.get('processid'))
    ppid     = first_nonempty(ci.get('ppid'), ci.get('parentprocessid'))

    entity = {
        "canonical_id": canon_proc_id(hashes, path, filename),
        "hashes": prune_empty({k: (v.lower() if isinstance(v, str) else v) for k, v in hashes.items() if v}),
        "image": prune_empty({"path": path, "filename": filename, "command_line": cmdline, "signer": signer}),
        "runtime": prune_empty({"pid": pid, "ppid": ppid})
    }

    # Hint: mark known-good system binary (helps playbooks avoid quarantining cmd.exe itself)
    if entity["image"].get("path"):
        p = entity["image"]["path"].replace('/', '\\').lower()
        if p.startswith(r'c:\windows\system32') and entity["image"].get("filename", "").lower() == "cmd.exe":
            entity["system_binary"] = True

    return None if entity["canonical_id"] == "unknown:process" else entity

def build_processes_from_xdm(ci):
    keys = {
        "path":       'xdmsourceprocessexecutablepath',
        "sha256":     'xdmsourceprocessexecutablesha256',
        "cmdline":    'xdmsourceprocesscommandline',
        "signer":     'xdmsourceprocessexecutablesigner',
        "signature":  'xdmsourceprocessexecutablesignaturestatus',
        "name":       'xdmsourceprocessname',
        "causality":  'xdmsourceprocesscausalityid',
        "pid":        'xdmsourceprocessid',          # optional
        "ppid":       'xdmsourceprocessparentid'     # optional
    }
    arrays = {k: ensure_list(ci.get(v)) for k, v in keys.items()}
    maxlen = max((len(v) for v in arrays.values()), default=0)

    out = []
    for i in range(maxlen):
        path      = _norm_path(first_nonempty(arrays["path"][i] if i < len(arrays["path"]) else None))
        filename  = first_nonempty(arrays["name"][i] if i < len(arrays["name"]) else None, _basename(path))
        sha256    = _first_str_or_none(arrays["sha256"][i] if i < len(arrays["sha256"]) else None)
        cmdline   = first_nonempty(arrays["cmdline"][i] if i < len(arrays["cmdline"]) else None)
        signer    = first_nonempty(arrays["signer"][i] if i < len(arrays["signer"]) else None)
        signature = first_nonempty(arrays["signature"][i] if i < len(arrays["signature"]) else None)
        causality = first_nonempty(arrays["causality"][i] if i < len(arrays["causality"]) else None)
        pid       = _to_pid_str(arrays["pid"][i]  if i < len(arrays["pid"])  else None)
        ppid      = _to_pid_str(arrays["ppid"][i] if i < len(arrays["ppid"]) else None)

        hashes = prune_empty({"sha256": (sha256.lower() if isinstance(sha256, str) else sha256)})
        entity = prune_empty({
            "canonical_id": canon_proc_id(hashes, path, filename),
            "hashes": hashes,
            "image": prune_empty({
                "path": path, "filename": filename,
                "command_line": cmdline, "signer": signer, "signature": signature
            }),
            "runtime": prune_empty({"pid": pid, "ppid": ppid}),
            "causality_id": causality
        })
        if entity and entity["canonical_id"] != "unknown:process":
            out.append(entity)
    return out

def dedupe_processes(procs):
    """Prefer richer entries per canonical_id."""
    best = {}
    for p in procs or []:
        key = p.get("canonical_id") or "unknown"
        score = 0
        if p.get("hashes"): score += 3
        if p.get("image", {}).get("path") or p.get("image", {}).get("filename"): score += 2
        if p.get("image", {}).get("command_line"): score += 1
        if p.get("image", {}).get("signer") or p.get("image", {}).get("signature"): score += 1
        if key not in best or score > best[key][0]:
            best[key] = (score, p)
    return [v[1] for v in best.values()]

# ---------------------------
# Categories / Tactics
# ---------------------------

def canon_tactic(s):
    if s is None:
        return None
    k = str(s).strip()
    if not k:
        return None
    M = {
        "initial access": "Initial Access", "execution": "Execution",
        "persistence": "Persistence", "privilege escalation": "Privilege Escalation",
        "defense evasion": "Defense Evasion", "credential access": "Credential Access",
        "discovery": "Discovery", "lateral movement": "Lateral Movement",
        "collection": "Collection", "command and control": "Command and Control",
        "exfiltration": "Exfiltration", "impact": "Impact",
        "reconnaissance": "Reconnaissance", "resource development": "Resource Development",
        "malware": "Malware"
    }
    return M.get(k.lower(), k)

def collect_alert_categories(ci):
    fields = [
        'mitre_tactic','mitre_tactics','mitretactic','mitretactics',
        'mitre_attack_tactic','mitre_attack_tactics','mitreattacktactic','mitreattacktactics',
        'mitreattck_tactic','mitreattck_tactics','mitreattcktactic','mitreattcktactics',
        'alertcategory','alert_category','category','categoryname','alertcategoryname',
        'tactic','tactics'
    ]
    vals = []
    for f in fields:
        v = ci.get(f)
        if v is not None:
            vals.extend(ensure_list(v))
    # labels fallback
    labels = ci.get('labels') or ci.get('label') or []
    if not vals and isinstance(labels, list):
        for it in labels:
            if isinstance(it, dict):
                k = str(it.get('type') or it.get('name') or '').lower()
                if k in fields:
                    vals.append(it.get('value'))
    out, seen = [], set()
    for v in vals:
        c = canon_tactic(v)
        if c and c not in seen:
            seen.add(c); out.append(c)
    return out

# ---------------------------
# Main
# ---------------------------

def main():
    incs = demisto.incidents() or []
    incident = incs[0] if incs else {}

    # Flatten top + CustomFields with case-insensitive keys
    ci = ci_dict(incident)
    ci.update(ci_dict(incident.get('CustomFields') or {}))

    # Domain
    domain = gather_domain(ci)

    # Users
    primary_user, all_usernames = gather_usernames(ci)
    user_email = first_nonempty(ci.get('email'), ci.get('useremail'), ci.get('actoruseremail'))
    user_id    = first_nonempty(ci.get('userid'), ci.get('user_id'), ci.get('oktauserid'), ci.get('aduserid'))

    # IPs
    primary_ip, ips = gather_ips(ci)

    # PIDs
    primary_pid, all_pids, primary_ppid, all_ppids = gather_pids(ci)

    # Host
    host_name = first_nonempty(ci.get('hostname'), ci.get('host'), ci.get('agenthostname'),
                               ci.get('devicehostname'), ci.get('xdrhostname'), ci.get('agentname'),
                               ci.get('xdmsourcehosthostname'))
    host_id   = first_nonempty(ci.get('agentid'), ci.get('deviceid'), ci.get('endpointid'),
                               ci.get('xdrendpointid'), ci.get('xdmsourceagentidentifier'))
    host_fqdn = first_nonempty(ci.get('hostfqdn'), ci.get('hostname_fqdn'), ci.get('fqdn'),
                               first_nonempty(*ensure_list(ci.get('xdmsourcehostfqdn'))))
    host_ip   = primary_ip

    # Email
    email_msg_id    = first_nonempty(ci.get('emailmessageid'), ci.get('messageid'), ci.get('abnormalmessageid'))
    email_senders   = [s for s in ensure_list(ci.get('issue.emailsender'))    if str(s).strip()]
    email_recipients= [s for s in ensure_list(ci.get('issue.emailrecipient')) if str(s).strip()]
    email_subjects  = [s for s in ensure_list(ci.get('issue.emailsubject'))   if str(s).strip()]
    if not email_subjects:
        email_subjects = [s for s in ensure_list(ci.get('emailsubject')) if str(s).strip()]

    # URLs
    primary_url, urls = gather_urls(ci)

    # Cloud
    instance_id = first_nonempty(ci.get('awsinstanceid'), ci.get('instanceid'), ci.get('cloudinstanceid'))

    # Processes (flat + XDM)
    procs = []
    pf = build_process_from_flat(ci)
    if pf: procs.append(pf)
    procs.extend(build_processes_from_xdm(ci))
    procs = dedupe_processes(procs)
    primary_proc = procs[0] if len(procs) == 1 else None

    # If we have a single primary process and it's missing pid/ppid, backfill from gathered IDs
    if primary_proc:
        rt = primary_proc.setdefault("runtime", {})
        if not rt.get("pid") and primary_pid:
            rt["pid"] = primary_pid
        if not rt.get("ppid") and primary_ppid:
            rt["ppid"] = primary_ppid

    # Categories
    cats = collect_alert_categories(ci)

    # Active products (disable via context.DisabledProducts.{endpoint|network|identity|email|cloud}=true)
    ctx = demisto.context() or {}
    disabled = (ctx or {}).get('DisabledProducts') or {}
    products = {"endpoint": True, "network": True, "identity": True, "email": True, "cloud": True}
    for k, v in disabled.items():
        if v: products[k] = False

    # Primary entity selection
    if email_msg_id:
        primary = {
            "type": "email",
            "email_message_id": email_msg_id,
            "sender": email_senders or None,
            "recipients": email_recipients or None,  # plural for downstream playbooks
            "subject": (email_subjects[0] if email_subjects else None),
            "user": primary_user or None,
            "user_email": user_email or None
        }
    elif primary_url:
        primary = {"type": "url", "url": primary_url}
    elif primary_user or user_id or user_email:
        primary = {"type": "user",
                   "user": primary_user or user_email or user_id,
                   "user_id": user_id or None,
                   "user_email": user_email or None}
    elif primary_proc:
        primary = {"type": "process", **primary_proc}
    elif host_name or host_id or host_ip or host_fqdn:
        primary = {"type": "host", "name": host_name or None,
                   "id": host_id or None, "ip": host_ip or None, "fqdn": host_fqdn or None}
    elif primary_ip:
        primary = {"type": "ip", "ip": primary_ip}
    elif instance_id:
        primary = {"type": "cloud", "instance_id": instance_id}
    else:
        primary = {"type": "unknown"}

    Normalized = prune_empty({
        "primary": primary,
        "domain": domain,
        "user": prune_empty({
            "user": primary_user,
            "user_id": user_id,
            "user_email": user_email,
            "all_usernames": all_usernames or None
        }),
        "users": all_usernames or None,
        "host": prune_empty({"name": host_name, "id": host_id, "ip": host_ip, "fqdn": host_fqdn, "pid": primary_pid}),
        "ip": prune_empty({"ip": primary_ip}),
        "ips": ips or None,
        "pids": (all_pids or None),
        "ppids": (all_ppids or None),
        "url": prune_empty({"url": primary_url}),
        "urls": urls or None,
        "email": prune_empty({
            "email_message_id": email_msg_id,
            "sender": email_senders or None,
            "recipients": email_recipients or None,   # plural
            "subject": (email_subjects[0] if email_subjects else None)
        }),
        "cloud": prune_empty({"instance_id": instance_id}),
        "process": primary_proc,
        "processes": procs or None
    })

    # Set keys for compatibility
    demisto.executeCommand('Set', {'key': 'Normalized',       'value': Normalized,                'append': 'false'})
    demisto.executeCommand('Set', {'key': 'NormalizedEntity', 'value': Normalized.get('primary'), 'append': 'false'})
    demisto.executeCommand('Set', {'key': 'AlertCategories',  'value': cats,                      'append': 'false'})
    demisto.executeCommand('Set', {'key': 'ActiveProducts',   'value': products,                  'append': 'false'})

    # Human-readable preview + EntryContext
    human = {
        "Normalized.preview": {
            "primary": Normalized.get('primary'),
            "user": Normalized.get('user'),
            "host": Normalized.get('host'),
            "ip": Normalized.get('ip'),
            "domain": Normalized.get('domain'),
            "url": Normalized.get('url'),
            "process": Normalized.get('process'),
        },
        "AlertCategories": cats,
        "ActiveProducts": products,
        "ContextKeys": ["Normalized","NormalizedEntity","AlertCategories","ActiveProducts"]
    }
    demisto.results({
        "Type": 1,
        "ContentsFormat": "json",
        "Contents": human,
        "HumanReadable": "Normalization complete — keys set in context",
        "EntryContext": {
            "Normalized": Normalized,
            "NormalizedEntity": Normalized.get('primary'),
            "AlertCategories": cats,
            "ActiveProducts": products
        }
    })

# XSOAR/XSIAM entrypoint
if __name__ in ('__builtin__','builtins','__main__'):
    main()

