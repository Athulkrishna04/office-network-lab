# Verification matrix

Baseline: `packet-tracer/office-baseline-v1.0.pkt` · Packet Tracer 9.0.1 · tested 25–26 Sep 2026.

**22 of 22 tests pass, including 5 negative tests** (marked ✗ expected) that pass only when the traffic is blocked.

**Checkpoints:** M1 = T01–T03, T05–T10, T21 · M2 = T04, T11–T20, T22
**Regression smoke set** (re-run after every fix or change): T01–T04 · T08 · T12 · T15 · T16

| ID | Req | From | Action / command | Expected | Result | Observed |
|---|---|---|---|---|---|---|
| T01 | FR-04 | PC-S1, PC-S2 | `ipconfig /all` | .11–.60 /26, gw .1, DNS .130 | PASS | PC-S1 192.168.10.11, PC-S2 .12, mask 255.255.255.192, gw .1, DNS .130 |
| T02 | FR-04 | PC-H1, PC-H2 | `ipconfig /all` | .75–.124 /26, gw .65, DNS .130 | PASS | PC-H1 .75, PC-H2 .76, gw .65 — leases relayed across R1 |
| T03 | FR-04 | PC-IT1, PC-IT2 | `ipconfig /all` | .140–.189 /26, gw .129, DNS .130 | PASS | PC-IT1 .140, PC-IT2 .141, gw .129 |
| T04 | FR-04, FR-08 | LAPTOP-G1, PHONE-G1 | associate to OFFICE-GUEST (WPA2-PSK/AES), `ipconfig` | .200–.249 /26, gw .193 | PASS | Laptop .202, phone .201, gw .193, DNS .130 |
| T05 | FR-03 | SW1, SW2 | `show interfaces trunk` (both ends) | trunking; allowed 10,20,30,40 | PASS | SW1 Gi0/1 + Gi0/2, SW2 Gi0/1 — allowed and active 10,20,30,40 on both ends |
| T06 | FR-01 | SW1, SW2 | `show vlan brief` | ports match the port map | PASS | 10 on Fa0/1–6, 20 on Fa0/7–12, 30 on Fa0/13–18, 40 on Fa0/19–20 (both switches) |
| T07 | FR-03 | R1 | `show ip interface brief` | subinterfaces + WAN up/up | PASS | G0/0, .10 (.1), .20 (.65), .30 (.129), .40 (.193), G0/1 (203.0.113.2) all up/up |
| T08 | FR-03 | PC-S1 | ping PC-H2 192.168.10.76 | success | PASS | 4/4 replies, TTL 127 — inter-VLAN **and** across both switches |
| T09 | FR-03 | PC-S1 | ping SRV-CORE 192.168.10.130 | success | PASS | 4/4 replies, TTL 127 |
| T10 | FR-05 | PC-S1 | `nslookup intranet.office.test` | 192.168.10.130 | PASS | Server 192.168.10.130, answer 192.168.10.130 |
| T11 | FR-06 | PC-S1 | `ping 198.51.100.10` | success | PASS | 4/4 replies, TTL 126 |
| T12 | FR-05, FR-06 | PC-S1 | browser `http://www.example.com` | WEB-EXT page loads | PASS | Page rendered ("You reached the internet through R1's PAT") |
| T13 | FR-06 | R1 | `show ip nat translations` | inside local → 203.0.113.2 | PASS | icmp 192.168.10.11 → 203.0.113.2, tcp 192.168.10.202:1025 → 203.0.113.2:1025 |
| T14 | FR-06 | ISP | `show ip route` | no route to 192.168.10.0/24 | PASS | Only 198.51.100.0/24 and 203.0.113.0/30 connected; gateway of last resort not set |
| T15 | FR-07 | LAPTOP-G1 | browser `http://www.example.com` | loads | PASS | Page loads with GUEST-IN applied — guests keep the internet |
| T16 | FR-07 | LAPTOP-G1 | ping PC-S1 192.168.10.11 | ✗ expected: blocked | PASS | "Reply from 192.168.10.193: Destination host unreachable" — dropped by the ACL at its own gateway |
| T17 | FR-07 | LAPTOP-G1 | browser `http://intranet.office.test` | ✗ expected: resolves, doesn't load | PASS | Loaded **before** the ACL; "Request Timeout" after |
| T18 | FR-07 | LAPTOP-G1 | ping 192.168.10.1 | ✗ expected: blocked | PASS | "Reply from 192.168.10.193: Destination host unreachable" |
| T19 | FR-07 | R1 | `show access-lists GUEST-IN` | deny counters increase | PASS | deny → IT subnet 42 matches; DNS permit 3; internet permit 8 |
| T20 | FR-09 | SW1 + ROGUE | Rogue laptop on Fa0/1, generate traffic; `show port-security interface Fa0/1` | port err-disabled, violation 1 | PASS | `%PM-4-ERR_DISABLE: psecure-violation ... Fa0/1`; Port Status Secure-shutdown, Violation Count 1, caused by 0001.9644.5103. Recovered with `shutdown` / `no shutdown` |
| T21 | FR-10 | PC-IT1 | ping 192.168.10.131, .132 | success | PASS | 3/4 replies to each (first packet lost to ARP) |
| T22 | FR-07 | PC-S1 | ping LAPTOP-G1 192.168.10.202 | ✗ expected: blocked | PASS | Request timed out — the guest's reply is dropped inbound by GUEST-IN (documented design behaviour, see design-decisions D4) |

## Port security state at baseline

`show port-security address`:

| Switch | Port | VLAN | Type |
|---|---|---|---|
| SW1 | Fa0/1, Fa0/7, Fa0/13, Fa0/14 | 10, 20, 30, 30 | SecureSticky (1 each) |
| SW2 | Fa0/1, Fa0/7, Fa0/13 | 10, 20, 30 | SecureSticky (1 each) |
| SW2 | Fa0/19 (AP uplink) | 40 | DynamicConfigured — max 10, violation restrict |

## Notes

- The first ping to a new destination often shows one "Request timed out" while ARP resolves. That is not a failure; the remaining replies are what count.
- Negative tests (T16–T18, T22) are the guest-isolation proof. If any of them ever starts succeeding, treat it as a P1 fault.
