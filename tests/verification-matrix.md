# Verification matrix

Fill in **Result** (PASS/FAIL) and **Evidence** (a screenshot path, or pasted output in the notes below) during P5. A **negative** test (marked ✗ expected) passes when the traffic is blocked.

**Checkpoints:** M1 = T01–T03, T05–T10, T21 · M2 = T04, T11–T20, T22
**Regression smoke set** (after every fix or change): T01–T04 · T08 · T12 · T15 · T16

| ID | Req | From | Action / command | Expected | Result | Evidence |
|---|---|---|---|---|---|---|
| T01 | FR-04 | PC-S1, PC-S2 | `ipconfig /renew`, `ipconfig /all` | .11–.60 /26, gw .1, DNS .130 | | |
| T02 | FR-04 | PC-H1, PC-H2 | `ipconfig /renew`, `ipconfig /all` | .75–.124 /26, gw .65, DNS .130 | | |
| T03 | FR-04 | PC-IT1, PC-IT2 | `ipconfig /renew`, `ipconfig /all` | .140–.189 /26, gw .129, DNS .130 | | |
| T04 | FR-04, FR-08 | LAPTOP-G1, PHONE-G1 | associate to OFFICE-GUEST (WPA2), `ipconfig /all` | .200–.249 /26, gw .193 | | |
| T05 | FR-03 | SW1, SW2 | `show interfaces trunk` (both ends of each trunk) | SW1 Gi0/1 + Gi0/2, SW2 Gi0/1 trunking; allowed 10,20,30,40 on both sides | | |
| T06 | FR-01 | SW1, SW2 | `show vlan brief` | every used port in its planned VLAN (see ip-plan.md) | | |
| T07 | FR-03 | R1 | `show ip interface brief` | G0/0, G0/0.10/.20/.30/.40 (and G0/1 after M2) up/up | | |
| T08 | FR-03 | PC-S1 | `ping` PC-H2 | success | | |
| T09 | FR-03 | PC-S2, PC-H1 | `ping 192.168.10.130`; `ping` PC-IT2 | success | | |
| T10 | FR-05 | PC-S1, PC-H2 | `nslookup intranet.office.test`; browser `http://intranet.office.test` | 192.168.10.130; intranet page loads | | |
| T11 | FR-06 | PC-H1 | `ping 198.51.100.10` | success | | |
| T12 | FR-05, FR-06 | PC-S1, PC-H2, PC-IT1 | browser `http://www.example.com` | WEB-EXT page loads | | |
| T13 | FR-06 | R1 | `show ip nat translations` | inside local 192.168.10.x ↔ inside global 203.0.113.2 | | |
| T14 | FR-06 | ISP | `show ip route` | no route to 192.168.10.0/24 (NAT is doing the work) | | |
| T15 | FR-07 | LAPTOP-G1 | `nslookup www.example.com`; browser `http://www.example.com` | resolves; page loads | | |
| T16 | FR-07 | LAPTOP-G1 | `ping` PC-S1 | ✗ expected: request timed out | | |
| T17 | FR-07 | LAPTOP-G1 | browser `http://intranet.office.test` | ✗ expected: name resolves, page does **not** load | | |
| T18 | FR-07 | LAPTOP-G1 | `ping 192.168.10.1`, `.65`, `.129` | ✗ expected: all fail | | |
| T19 | FR-07 | R1 | `show access-lists GUEST-IN` before and after T16–T18 | match counters on lines 30–50 increase | | |
| T20 | FR-09 | SW1 + ROGUE | move PC-S1's cable to ROGUE and generate traffic; `show port-security interface fa0/1` | Fa0/1 err-disabled, violation count 1. Recover: reconnect PC-S1, `shutdown` / `no shutdown` | | |
| T21 | FR-10 | PC-IT1 | `ping 192.168.10.131`, `ping 192.168.10.132` | success | | |
| T22 | FR-07 | PC-S1 | `ping` LAPTOP-G1 | ✗ expected: the reply is dropped by GUEST-IN (documented design behavior) | | |

## Notes / pasted output

<!-- Paste real CLI output for key tests here in ```text blocks, labelled with the test ID. -->
