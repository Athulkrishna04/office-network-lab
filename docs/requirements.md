# Requirements

> Draft written in phase P1. The client is fictional (a role-played lab brief). Rewrite it in your own voice, and keep the IDs stable, because tests and write-ups refer to them.

## 1. Customer brief

A 60-person office on one floor, with two wiring closets. Staff are in **Sales** (about 30), **HR** (about 8) and **IT** (about 5, plus the server). Visitors need **Wi-Fi with internet only**. The office has one internet connection with a single public address. The office manager wants one place to manage addresses and names, wants guests kept away from staff systems, and doesn't want an unknown laptop plugged into a desk port to just work.

## 2. Stakeholders

| Stakeholder | Interest | Key answer (role-played) |
|---|---|---|
| Office manager (sponsor) | Cost, uptime | "Must fit one /24 and free tools; a short outage is acceptable, but a guest reaching HR files isn't." |
| Sales lead | Internet reliability | "We live in web apps; if the website is down, we're down." |
| HR lead | Confidentiality | "Guests must never reach our systems." |
| IT admin | Manageability | "One DHCP/DNS server, documented addressing, switches reachable from IT." |
| Guests | Simple Wi-Fi | "One password, internet works." |
| Reviewer / hiring manager | Evidence | "Show me it works, show me you can fix it when it doesn't." |

## 3. Functional requirements

| ID | Requirement |
|---|---|
| FR-01 | Four separate broadcast domains: VLAN 10 Sales, 20 HR, 30 IT, 40 Guest. |
| FR-02 | Each VLAN gets a /26 carved from 192.168.10.0/24. |
| FR-03 | Sales, HR and IT hosts can reach each other (inter-VLAN routing). |
| FR-04 | All hosts get addresses from one central DHCP server, including VLANs that aren't local to it. |
| FR-05 | One central DNS server resolves internal (`intranet.office.test`) and external (`www.example.com`) names. |
| FR-06 | All VLANs reach the internet through one public address (PAT). |
| FR-07 | Guests get DHCP, DNS and the internet, but can't reach the Sales, HR or IT subnets. |
| FR-08 | Guest access is over WPA2 Wi-Fi. |
| FR-09 | Every access port limits and remembers the devices allowed on it (port security). |
| FR-10 | Switches can be managed from the IT VLAN. |

## 4. Non-functional requirements

| ID | Requirement |
|---|---|
| NFR-01 | Reproducible: someone else can rebuild or open it from the repo alone. |
| NFR-02 | Free tooling only: Packet Tracer 8.2.x+, Git, draw.io, Python. |
| NFR-03 | Every design choice is written down with its reason (`design-decisions.md`). |
| NFR-04 | Each VLAN supports at least 50 DHCP clients, with room reserved for statics. |
| NFR-05 | No real credentials in the repo. |

## 5. Constraints, assumptions, scope

- **Constraints:** one /24 (192.168.10.0/24); Packet Tracer's IOS feature subset; a single ISP link.
- **Assumptions:** a single site; at most 50 concurrent clients per VLAN; the ISP provides one /30.
- **Out of scope for v1** (see PLAN §9): redundancy, HR-specific ACLs, 802.1X, VPN, QoS, IPv6, real hardware.

## 6. Success criteria

| ID | Criterion |
|---|---|
| SC1 | 100% of FRs have at least one passing test in `tests/verification-matrix.md`. |
| SC2 | Every guest-isolation negative test (T16–T18, T22) fails as designed: zero leaks. |
| SC3 | 6/6 faults injected and resolved; each write-up has a symptom, commands with real output, root cause, fix and verification. |
| SC4 | The regression smoke set passes after every fix. |
| SC5 | A reviewer can open the `.pkt` in the stated PT version and reproduce T01–T22 from the README alone. |
| SC6 | The repo is public with the `.pkt` files, diagram, IP plan and write-ups. |

## 7. Traceability matrix

| Requirement | Implemented in | Proven by |
|---|---|---|
| FR-01 | SW1/SW2 [M1]: VLANs + access ports | T06 |
| FR-02 | `docs/ip-plan.md`, R1 subinterfaces | `tools/ipplan.py`, T01–T04 |
| FR-03 | R1 G0/0.10–.40 (router-on-a-stick), trunks | T05, T07, T08, T09 |
| FR-04 | SRV-CORE pools + `ip helper-address` | T01–T04 |
| FR-05 | SRV-CORE DNS | T10, T12 |
| FR-06 | R1 PAT + default route | T11–T14 |
| FR-07 | R1 GUEST-IN inbound on G0/0.40 | T15–T19, T22 |
| FR-08 | AP-GUEST WPA2-PSK | T04 |
| FR-09 | SW1/SW2 [M2] port security | T20 |
| FR-10 | VLAN 30 SVIs + default gateway | T21 |
