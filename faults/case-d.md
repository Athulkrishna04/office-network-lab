# Case D: <one-line title, written after you find it>

| Field | Value |
|---|---|
| Layer | <fill in once you know: L2 access / L2 trunk / L3 / L4 / L7> |
| Challenge file (broken state) | `packet-tracer/faults/case-d.pkt` |
| Date | 2026-09-26 |
| Time to resolve | <start → end> |
| Injected by / how blind | Injected in a scrambled batch of six, diagnosed in a different order |

## 1. Symptom

**Reported:** "Nobody in Sales can get on the network this morning. HR and IT are fine."

**What works**
- PC-H1 (HR): address 192.168.10.75, gateway 192.168.10.65, `ping 192.168.10.1` → 4/4 replies
- PC-IT1 (IT): address 192.168.10.140, gateway 192.168.10.129, `ping 192.168.10.1` → 4/4 replies
- Both HR and IT leased addresses from the correct pools, so the DHCP server itself is answering somebody

**What doesn't**
- PC-S1 (Sales): no IPv4 address after `ipconfig /renew` (DHCP Servers shows 0.0.0.0)
- PC-S1 → `ping 192.168.10.1` (its own gateway): 4/4 request timed out
- PC-S1 → `ping 192.168.10.130` (the DHCP/DNS server): request timed out

**Scope:** VLAN 10 (Sales) only. HR and IT are unaffected, on both switches.
*Still to confirm:* is PC-S2 (Sales on the other switch) also broken? That answer decides whether this is
one VLAN **everywhere** (points at the router or the server) or one VLAN **on one switch** (points at the
link between the switches).

## 2. Hypotheses (most likely first)

1. <hypothesis> — test:
2. <hypothesis> — test:
3. <hypothesis> — test:

*Candidates worth considering, given that only one VLAN is affected and that a host with no address
cannot ping anything by definition:*
- the Sales access ports are no longer in VLAN 10
- VLAN 10 is missing from a trunk
- the Sales gateway on the router is down or misconfigured
- the Sales DHCP pool on the server is wrong or exhausted
- the router is no longer forwarding Sales DHCP requests to the server

Cross out the ones you disprove — the dead ends are part of the story.

## 3. Commands run
*In order, with trimmed **real** output. Include the dead ends.*

### 3.1 `ipconfig /all` on PC-S1

```text
<paste>
```

What it told me:

### 3.2 `<command>` on `<DEVICE>`

```text
<paste>
```

What it told me:

## 4. Root cause

*One sentence, plus why it produces exactly this symptom.*

## 5. Fix

```text
<exact commands>
```

## 6. Verification

- Failing test re-run (T01: PC-S1 and PC-S2 lease 192.168.10.11–.60, gateway .1):
- Regression smoke set (T01–T04, T08, T12, T15, T16): PASS / FAIL
- Evidence: `screenshots/case-d-*.png`

## 7. Prevention / lesson

*One control that would have prevented or caught this sooner.*
