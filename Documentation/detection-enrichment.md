🔎 Detection & Analysis Enrichment Matrix
| **Alert Category**                          | **Entities to Enrich**    | **Enrichment Actions**                                                                                                      |
| ------------------------------------------- | ------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| **Vulnerability**                           | Host, IP, User            | Endpoint vulnerability scan info; asset context (CVE mapping, patch level); user assignment/owner                           |
| **Risk**                                    | User, Host, IP            | User risk score (AD/Okta/Azure AD); endpoint posture; IP threat intel                                                       |
| **Lateral Movement**                        | Host, User, Process       | Host session enumeration; logon history; process execution chain; user logon correlation                                    |
| **Discovery**                               | Host, IP, Process         | Endpoint inventory; network scan patterns; process command-line context                                                     |
| **Defense Evasion**                         | Process, File, Host       | Process reputation & prevalence; file obfuscation checks; endpoint tamper-protection logs                                   |
| **Exfiltration**                            | User, Host, IP, Domain    | User data transfer history; endpoint DLP; network flow analysis; domain WHOIS/Intel                                         |
| **Command and Control**                     | IP, Domain, Host, Process | IP/domain reputation; beaconing pattern analysis; host connection logs; process that initiated connections                  |
| **Malware**                                 | File, Process, Host, User | File hash reputation; sandbox detonation (WildFire/VT); process prevalence; host isolation candidate; user execution source |
| **Antivirus**                               | File, Host, Process       | AV signature match enrichment; hash check; host scan results                                                                |
| **Wildfire Analysis**                       | File, Process             | Detonation results; prevalence checks; file relationships                                                                   |
| **Persistence**                             | Process, File, Host       | Autorun entries; scheduled tasks; registry keys (Windows); startup items                                                    |
| **Credential Access**                       | User, Process, File       | User AD/Okta enrichment; credential dump process detection; file dump artifacts                                             |
| **Initial Access**                          | User, IP, Domain, Host    | User identity enrichment; IP/domain intel; endpoint ingress event details                                                   |
| **Execution**                               | Process, File, Host       | Process chain analysis; file hash reputation; host process ancestry                                                         |
| **Collection**                              | File, Process, User       | File copy/move analysis; suspicious process chain; user activity around collection                                          |
| **Privilege Escalation**                    | User, Process, Host       | User group membership; process privilege level; host privilege escalation events                                            |
| **Impact**                                  | Host, User, Process, File | Host availability; ransomware file changes; user service impact; destructive process details                                |
| **Tampering**                               | Host, Process             | Endpoint security controls tampered; suspicious process modifications                                                       |
| **Reconnaissance**                          | IP, Domain, User          | External IP scanning; domain WHOIS/DNS intel; user reconnaissance commands                                                  |
| **Dropper**                                 | File, Process, Host       | File drop analysis; process tree; hash reputation                                                                           |
| **File Privileges Escalation**              | File, Process, User       | File ACL/permission analysis; process file modification; user privilege context                                             |
| **File Type Obfuscation**                   | File, Process             | File extension mismatch; entropy/packing detection; hash reputation                                                         |
| **Infiltration**                            | IP, Domain, Host          | IP/domain intel; inbound network session analysis; host IDS/IPS logs                                                        |
| **URL Filtering (private-ip-addresses)**    | URL, Domain, IP           | URL reputation; domain WHOIS; private IP resolution                                                                         |
| **Spyware Detected (Anti-Spyware Profile)** | File, Process, Domain, IP | File hash enrichment; process prevalence; domain/IP reputation                                                              |
| **Scan Detected (Zone Protection)**         | IP, Host                  | IP reputation; host scan detection logs; zone protection context                                                            |
