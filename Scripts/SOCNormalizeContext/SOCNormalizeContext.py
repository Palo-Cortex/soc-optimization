import demistomock as demisto  # noqa: F401
from CommonServerPython import *  # noqa: F401
# SOC_NormalizeContext_v9
# Cortex XSIAM / XSOAR Automation (Python 3)
#
# Outputs (EntryContext + Set):
#   Normalized, NormalizedEntity, AlertCategories, ActiveProducts
#
# Normalization includes:
# - domain: issue.domain / domain / issuedomain / userdomain / accountdomain / xdmsourcehostfqdn
# - user: supports arrays (issue.username: ["u1","u2"]), xdmsourceuserusername: []
# - ip(s): issue.hostip[], xdmsource.ipv4addresses[], xdmsourcehostipv4addresses[] (+ common src/dst fallbacks)
# - url(s): issue.url (scalar/array/mixed); canonicalized + deduped
# - email: message id + sender/recipient/subject (if present)
# - process/processes: from initiator*/process* fields and XDM arrays:
#       xdmsourceprocessexecutablepath, xdmsourceprocessexecutablesha256,
#       xdmsourceprocesscommandline, xdmsourceprocessexecutablesigner,
#       xdmsourceprocessexecutablesignaturestatus, xdmsourceprocessname,
#       xdmsourceprocesscausalityid
#
# Canonicalization priority for process canonical_id: sha256 > sha1 > md5 > path > filename

import re
import json
from urllib.parse import urlsplit, urlunsplit, quote, unquote

def ci_dict(d):
    return {str(k).lower(): v for k, v in (d or {}).items()} if isinstance(d, dict) else {}

def ensure_list(x):
    if x is None:
        return []
    if isinstance(x, list):
        return x
    if isinstance(x, tuple) or isinstance(x, set):
        return list(x)
    # strings: split on commas/semicolons if present
    if isinstance(x, str) and (',' in x or ';' in x):
        parts = re.split(r'[;,]\s*', x)
        return [p for p in parts if p]
    return [x]

def first_nonempty(*vals):
    for v in vals:
        if isinstance(v, str) and v.strip():
            return v.strip()
        if isinstance(v, (int, float)) and v is not None:
            return v
        if v not in (None, "", [], {}):
            return v
    return None

def pick_ip_candidates(*vals):
    ips = []
    for v in vals:
        for item in ensure_list(v):
            if isinstance(item, str) and re.match(r'^\d{1,3}(\.\d{1,3}){3}$', item.strip()):
                ips.append(item.strip())
    # dedupe, preserve order
    seen = set()
    out = []
    for ip in ips:
        if ip not in seen:
            seen.add(ip)
            out.append(ip)
    return out

def _norm_path(p: str) -> str:
    if not p: return None
    s = str(p).strip().strip('"').strip("'")
    # naive env expansion (do not hit OS)
    for a, b in [('%SystemRoot%', 'C:\\Windows'), ('%WINDIR%', 'C:\\Windows'),
                 ('$HOME', '/home'), ('%HOMEPATH%', 'C:\\Users\\') ]:
        s = s.replace(a, b)
    return s

def _basename(p: str) -> str:
    if not p: return None
    return p.replace('\\','/').rstrip('/').split('/')[-1]

def canon_proc_id(hashes, path, filename):
    if hashes.get('sha256'): return f"sha256:{str(hashes['sha256']).lower()}"
    if hashes.get('sha1'):   return f"sha1:{str(hashes['sha1']).lower()}"
    if hashes.get('md5'):    return f"md5:{str(hashes['md5']).lower()}"
    if path:                 return f"path:{path.lower()}"
    if filename:             return f"file:{filename.lower()}"
    return "unknown:process"

def prune_empty(d):
    if not isinstance(d, dict):
        return d
    return {k: v for k, v in d.items() if v not in (None, "", [], {})}

def canon_tactic(s):
    if s is None: return None
    k = str(s).strip()
    if not k: return None
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

def collect_alert_categories(incident_ci):
    fields = [
        'mitre_tactic','mitre_tactics','mitretactic','mitretactics',
        'mitre_attack_tactic','mitre_attack_tactics','mitreattacktactic','mitreattacktactics',
        'mitreattck_tactic','mitreattck_tactics','mitreattcktactic','mitreattcktactics',
        'alertcategory','alert_category','category','categoryname','alertcategoryname',
        'tactic','tactics'
    ]
    vals = []
    for f in fields:
        v = incident_ci.get(f)
        if v is not None:
            vals.extend(ensure_list(v))
    # also check labels
    labels = incident_ci.get('labels') or incident_ci.get('label') or []
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

def gather_usernames(incident_ci):
    # Arrays and scalars
    candidates = []
    for key in ['issue.username','username','user','actorusername','userid','user_id','sourceuser','accountname','xdmsourceuserusername']:
        v = incident_ci.get(key)
        if v is not None:
            candidates.extend(ensure_list(v))
    # dedupe
    names = []
    seen = set()
    for n in candidates:
        if not n: continue
        s = str(n).strip()
        if not s: continue
        if s not in seen:
            seen.add(s); names.append(s)
    primary = names[0] if names else None
    return primary, names

def gather_domain(incident_ci):
    dom = first_nonempty(
        incident_ci.get('issue.domain'),
        incident_ci.get('issuedomain'),
        incident_ci.get('domain'),
        incident_ci.get('userdomain'),
        incident_ci.get('accountdomain'),
        # xdmsourcehostfqdn may be list or scalar
        first_nonempty(*ensure_list(incident_ci.get('xdmsourcehostfqdn')))
    )
    return dom

def gather_ips(incident_ci):
    ips = pick_ip_candidates(
        incident_ci.get('issue.hostip'),
        incident_ci.get('xdmsource.ipv4addresses'),
        incident_ci.get('xdmsourcehostipv4addresses'),
        incident_ci.get('src'), incident_ci.get('srcip'), incident_ci.get('sourceip'),
        incident_ci.get('dst'), incident_ci.get('dstip'), incident_ci.get('destinationip'),
        incident_ci.get('ip')
    )
    primary = ips[0] if ips else None
    return primary, ips

# -------- URL normalization --------
_URL_RE = re.compile(
    r'(?P<u>(?:https?://|ftp://|www\.)[^\s<>"\'\]\)]+)', re.IGNORECASE
)

def _canon_host(h):
    try:
        # Split host:port, lowercase host, IDNA if needed
        if not h:
            return h
        host_port = h.split('@')[-1]  # drop userinfo if present
        if ':' in host_port and host_port.count(':') == 1:
            host, port = host_port.split(':', 1)
            host = host.encode('idna').decode('ascii').lower()
            return f"{host}:{port}"
        host = host_port.encode('idna').decode('ascii').lower()
        return host
    except Exception:
        return (h or '').lower()

def _normalize_url_once(u: str) -> str:
    if not u:
        return None
    s = u.strip().strip('<>').strip('\'"')
    # If it looks like "www.example.com/..." without scheme, prepend http://
    if s.lower().startswith('www.'):
        s = 'http://' + s
    # Pull first URL if string contains multiple
    m = _URL_RE.search(s)
    if m:
        s = m.group('u')
    try:
        parts = urlsplit(s)
        scheme = (parts.scheme or 'http').lower()
        netloc = _canon_host(parts.netloc)
        # drop default ports
        if (scheme == 'http' and netloc.endswith(':80')):
            netloc = netloc[:-3]
        if (scheme == 'https' and netloc.endswith(':443')):
            netloc = netloc[:-4]
        # normalize path: percent-decode/encode once, collapse // -> /
        raw_path = parts.path or '/'
        unq_path = unquote(raw_path)
        norm_path = re.sub(r'/+', '/', unq_path)
        enc_path = quote(norm_path, safe='/-._~')
        # keep query as-is (avoid reordering), strip fragment
        query = parts.query
        return urlunsplit((scheme, netloc, enc_path, query, ''))
    except Exception:
        # fallback: basic cleanup
        return s.strip()

def gather_urls(incident_ci):
    raw_candidates = []
    # Primary fields (arrays or scalars)
    for key in ['issue.url', 'url', 'issue.urls', 'urls']:
        v = incident_ci.get(key)
        if v is not None:
            raw_candidates.extend(ensure_list(v))
    # Also scan subject/description-ish fields for embedded URLs (best-effort, optional)
    for key in ['description', 'details', 'emailsubject', 'issue.emailsubject']:
        v = incident_ci.get(key)
        for s in ensure_list(v):
            if isinstance(s, str):
                raw_candidates.extend(m.group('u') for m in _URL_RE.finditer(s))

    # Flatten, normalize, dedupe (preserve order)
    seen = set()
    out = []
    for item in raw_candidates:
        if not item:
            continue
        s = str(item)
        n = _normalize_url_once(s)
        if not n:
            continue
        if n not in seen:
            seen.add(n); out.append(n)
    primary = out[0] if out else None
    return primary, out

# -------- Process builders --------
def build_process_from_flat(ci):
    hashes = {
        "sha256": first_nonempty(ci.get('initiatorsha256'), ci.get('initiator_sha256'),
                                 ci.get('processsha256'), ci.get('process_sha256'),
                                 ci.get('sha256')),
        "sha1": first_nonempty(ci.get('initiatorsha1'), ci.get('initiator_sha1'),
                               ci.get('processsha1'), ci.get('process_sha1'),
                               ci.get('sha1')),
        "md5": first_nonempty(ci.get('initiatormd5'), ci.get('initiator_md5'),
                              ci.get('processmd5'), ci.get('process_md5'),
                              ci.get('md5')),
    }
    path = _norm_path(first_nonempty(ci.get('image'), ci.get('imagepath'),
                                     ci.get('executablepath'), ci.get('processpath'),
                                     ci.get('filepath')))
    filename = first_nonempty(ci.get('filename'), _basename(path))
    cmdline  = first_nonempty(ci.get('cmdline'), ci.get('commandline'), ci.get('processcommandline'))
    signer   = first_nonempty(ci.get('signer'), ci.get('signature'), ci.get('signaturestatus'))
    pid      = first_nonempty(ci.get('pid'), ci.get('processid'))

    # Normalize hash values to strings; support list values defensively (take first)
    def _first_str(v):
        vv = ensure_list(v)
        x = vv[0] if vv else None
        return str(x) if x is not None else None
    hashes = {k: _first_str(v) for k, v in hashes.items() if v is not None}

    ppid     = first_nonempty(ci.get('ppid'), ci.get('parentprocessid'))
    entity = {
        "canonical_id": canon_proc_id(hashes, path, filename),
        "hashes": prune_empty({k: (v.lower() if isinstance(v,str) else v) for k,v in hashes.items() if v}),
        "image": prune_empty({"path": path, "filename": filename, "command_line": cmdline, "signer": signer}),
        "runtime": prune_empty({"pid": pid, "ppid": ppid})
    }
    return entity if entity["canonical_id"] != "unknown:process" else None

def build_processes_from_xdm(ci):
    # Collect parallel arrays (some may be length 1)
    keys = {
        "path": 'xdmsourceprocessexecutablepath',
        "sha256": 'xdmsourceprocessexecutablesha256',
        "cmdline": 'xdmsourceprocesscommandline',
        "signer": 'xdmsourceprocessexecutablesigner',
        "signature": 'xdmsourceprocessexecutablesignaturestatus',
        "name": 'xdmsourceprocessname',
        "causality": 'xdmsourceprocesscausalityid'
    }
    arrays = {k: ensure_list(ci.get(v)) for k, v in keys.items()}
    maxlen = max((len(v) for v in arrays.values()), default=0)
    out = []
    for i in range(maxlen):
        path = _norm_path(first_nonempty(arrays["path"][i] if i < len(arrays["path"]) else None))
        filename = first_nonempty(arrays["name"][i] if i < len(arrays["name"]) else None, _basename(path))
        sha256 = first_nonempty(arrays["sha256"][i] if i < len(arrays["sha256"]) else None)
        cmdline = first_nonempty(arrays["cmdline"][i] if i < len(arrays["cmdline"]) else None)
        signer = first_nonempty(arrays["signer"][i] if i < len(arrays["signer"]) else None)
        signature = first_nonempty(arrays["signature"][i] if i < len(arrays["signature"]) else None)
        causality = first_nonempty(arrays["causality"][i] if i < len(arrays["causality"]) else None)
        hashes = prune_empty({"sha256": sha256.lower() if isinstance(sha256,str) else sha256})
        entity = prune_empty({
            "canonical_id": canon_proc_id(hashes, path, filename),
            "hashes": hashes,
            "image": prune_empty({"path": path, "filename": filename, "command_line": cmdline, "signer": signer, "signature": signature}),
            "runtime": {},
            "causality_id": causality
        })
        if entity and entity.get("canonical_id") != "unknown:process":
            out.append(entity)
    return out

def dedupe_processes(procs):
    best = {}
    for p in procs or []:
        key = p.get("canonical_id") or "unknown"
        # score richness
        score = 0
        if p.get("hashes"): score += 3
        if p.get("image", {}).get("path") or p.get("image", {}).get("filename"): score += 2
        if p.get("image", {}).get("command_line"): score += 1
        if p.get("image", {}).get("signer") or p.get("image", {}).get("signature"): score += 1
        if key not in best or score > best[key][0]:
            best[key] = (score, p)
    return [v[1] for v in best.values()]

def main():
    incs = demisto.incidents() or []
    incident = incs[0] if incs else {}
    # flatten top + CustomFields, case-insensitive keys
    incident_ci = ci_dict(incident)
    incident_ci.update(ci_dict(incident.get('CustomFields') or {}))

    # ---- domain ----
    domain = gather_domain(incident_ci)

    # ---- user ----
    primary_user, all_usernames = gather_usernames(incident_ci)
    user_email = first_nonempty(incident_ci.get('email'), incident_ci.get('useremail'), incident_ci.get('actoruseremail'))
    user_id = first_nonempty(incident_ci.get('userid'), incident_ci.get('user_id'), incident_ci.get('oktauserid'), incident_ci.get('aduserid'))

    # ---- IPs ----
    primary_ip, ips = gather_ips(incident_ci)

    # ---- Host ----
    host_name = first_nonempty(incident_ci.get('hostname'), incident_ci.get('host'), incident_ci.get('agenthostname'),
                               incident_ci.get('devicehostname'), incident_ci.get('xdrhostname'), incident_ci.get('agentname'),
                               incident_ci.get('xdmsourcehosthostname'))
    host_id = first_nonempty(incident_ci.get('agentid'), incident_ci.get('deviceid'), incident_ci.get('endpointid'),
                             incident_ci.get('xdrendpointid'), incident_ci.get('xdmsourceagentidentifier'))
    host_fqdn = first_nonempty(incident_ci.get('hostfqdn'), incident_ci.get('hostname_fqdn'), incident_ci.get('fqdn'),
                               first_nonempty(*ensure_list(incident_ci.get('xdmsourcehostfqdn'))))
    host_ip = primary_ip

    # ---- Email ----
    email_msg_id = first_nonempty(incident_ci.get('emailmessageid'), incident_ci.get('messageid'), incident_ci.get('abnormalmessageid'))
    email_senders = [s for s in ensure_list(incident_ci.get('issue.emailsender')) if str(s).strip()]
    email_recipients = [s for s in ensure_list(incident_ci.get('issue.emailrecipient')) if str(s).strip()]
    email_subjects = [s for s in ensure_list(incident_ci.get('issue.emailsubject')) if str(s).strip()]
    if not email_subjects:
        # fallback to generic fields
        email_subjects = [s for s in ensure_list(incident_ci.get('emailsubject')) if str(s).strip()]

    # ---- URLs ----
    primary_url, urls = gather_urls(incident_ci)

    # ---- Cloud ----
    instance_id = first_nonempty(incident_ci.get('awsinstanceid'), incident_ci.get('instanceid'), incident_ci.get('cloudinstanceid'))

    # ---- Process (flat + XDM arrays) ----
    procs = []
    p_flat = build_process_from_flat(incident_ci)
    if p_flat: procs.append(p_flat)
    procs.extend(build_processes_from_xdm(incident_ci))
    procs = dedupe_processes(procs)
    primary_proc = procs[0] if len(procs) == 1 else None

    # ---- Alert Categories ----
    cats = collect_alert_categories(incident_ci)

    # ---- Active Products (simple, true unless explicitly disabled) ----
    ctx = demisto.context() or {}
    ctx_disabled = (ctx or {}).get('DisabledProducts') or {}
    products = {"endpoint": True, "network": True, "identity": True, "email": True, "cloud": True}
    for k, v in ctx_disabled.items():
        if v: products[k] = False

    # ---- Primary entity selection (email > url > user > process > host > ip > cloud) ----
    if email_msg_id:
        primary = {
            "type": "email",
            "email_message_id": email_msg_id,
            "sender": email_senders or None,
            "recipient": email_recipients or None,
            "subject": (email_subjects[0] if email_subjects else None),
            "user": primary_user or None,
            "user_email": user_email or None
        }
    elif primary_url:
        primary = {"type": "url", "url": primary_url}
    elif primary_user or user_id or user_email:
        primary = {"type": "user", "user": primary_user or user_email or user_id, "user_id": user_id or None, "user_email": user_email or None}
    elif primary_proc:
        primary = {"type": "process", **primary_proc}
    elif host_name or host_id or host_ip or host_fqdn:
        primary = {"type": "host", "name": host_name or None, "id": host_id or None, "ip": host_ip or None, "fqdn": host_fqdn or None}
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
        "host": prune_empty({"name": host_name, "id": host_id, "ip": host_ip, "fqdn": host_fqdn}),
        "ip": prune_empty({"ip": primary_ip}),
        "ips": ips or None,
        "url": prune_empty({"url": primary_url}),
        "urls": urls or None,
        "email": prune_empty({
            "email_message_id": email_msg_id,
            "sender": email_senders or None,
            "recipient": email_recipients or None,
            "subject": (email_subjects[0] if email_subjects else None)
        }),
        "cloud": prune_empty({"instance_id": instance_id}),
        "process": primary_proc,
        "processes": procs or None
    })

    # ---- Write via Set (for compatibility) ----
    demisto.executeCommand('Set', {'key': 'Normalized', 'value': Normalized, 'append': 'false'})
    demisto.executeCommand('Set', {'key': 'NormalizedEntity', 'value': Normalized.get('primary'), 'append': 'false'})
    demisto.executeCommand('Set', {'key': 'AlertCategories', 'value': cats, 'append': 'false'})
    demisto.executeCommand('Set', {'key': 'ActiveProducts', 'value': products, 'append': 'false'})

    # ---- Also return EntryContext ----
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

if __name__ in ('__builtin__','builtins','__main__'):
    main()
