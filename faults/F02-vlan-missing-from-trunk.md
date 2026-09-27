# F02: HR works on one switch and not the other after a VLAN was pruned from the trunk

| Field | Value |
|---|---|
| Layer | L2 — trunk allowed VLAN list |
| Injected on | SW1, GigabitEthernet0/2 (the trunk to SW2) |
| Date | 2026-09-27 |
| Detected by | T02 (HR hosts lease from the HR pool) and T05 (trunks match on both ends) |

## 1. Symptom

**Reported:** "HR upstairs can't get on the network. HR downstairs is fine."

**What works**
- PC-H1 (HR, on SW1) keeps its lease: `192.168.10.76`, gateway `192.168.10.65`
- Sales and IT hosts on SW2 are unaffected

**What doesn't**
- PC-H2 (HR, on SW2) cannot lease an address

```text
C:\>ipconfig /release
   IP Address......................: 0.0.0.0
   ...
C:\>ipconfig /renew
DHCP request failed.
```

**Scope:** VLAN 20 only, and only on SW2. Same VLAN, different switch, different result.
That combination rules out the router and the DHCP server — both are shared by PC-H1, which is fine — and
points straight at what sits between the two switches.

## 2. Hypotheses

1. PC-H2's access port left VLAN 20 — *rejected*: `show vlan brief` on SW2 still lists Fa0/7 under VLAN 20.
2. The DHCP pool is exhausted — *rejected*: PC-H1 holds a lease from the same pool and other VLANs lease fine.
3. VLAN 20 isn't crossing the SW1–SW2 trunk. **Kept.**

## 3. Commands run

### 3.1 `ipconfig` on PC-H1 (same VLAN, other switch)

```text
   IPv4 Address....................: 192.168.10.76
   Subnet Mask.....................: 255.255.255.192
   Default Gateway.................: 192.168.10.65
```

*What it told me:* VLAN 20's gateway, pool and relay all work. Only the SW2 side of HR is broken, so the
fault lives on the path between the switches.

### 3.2 `show interfaces trunk` on SW2 (the switch that reported the problem)

```text
Port        Mode         Encapsulation  Status        Native vlan
Gig0/1      on           802.1q         trunking      1

Port        Vlans allowed on trunk
Gig0/1      10,20,30,40
```

*What it told me:* **nothing is wrong here.** From SW2's point of view the trunk carries VLAN 20 exactly as
designed. This is the dead end that matters: if I had stopped at the switch that reported the fault, I would
have concluded the network was fine.

### 3.3 `show interfaces trunk` on SW1 (the other end of the same cable)

```text
Port        Vlans allowed on trunk
Gig0/1      10,20,30,40
Gig0/2      10,30,40

Port        Vlans allowed and active in management domain
Gig0/1      10,20,30,40
Gig0/2      10,30,40
```

*What it told me:* Gi0/2 — the link to SW2 — allows **10,30,40**. VLAN 20 is missing, while Gi0/1 (to the
router) still has it. HR frames from SW2 are dropped as soon as they arrive at SW1.

## 4. Root cause

VLAN 20 had been pruned from SW1's Gi0/2 allowed list. A trunk's allowed list is configured per interface and
per end, so SW2 happily tagged and sent HR traffic, and SW1 discarded it on arrival. HR hosts on SW1 were
unaffected because their frames never cross that trunk, and the other VLANs still crossed it normally.

## 5. Fix

```text
SW1# configure terminal
SW1(config)# interface GigabitEthernet0/2
SW1(config-if)#  switchport trunk allowed vlan add 20
SW1(config-if)# end
```

`add` matters. Typing `switchport trunk allowed vlan 20` would have **replaced** the whole list with just
VLAN 20 and taken down Sales, IT and Guest across the link — a much bigger outage than the one being fixed.

## 6. Verification

```text
C:\>ipconfig /renew
   IP Address......................: 192.168.10.85
   Subnet Mask.....................: 255.255.255.192
   Default Gateway.................: 192.168.10.65
   DNS Server......................: 192.168.10.130
```

- T02 passes again: PC-H2 leases from the HR pool with the correct gateway.
- T05 passes: both ends of the trunk allow 10,20,30,40.
- Regression smoke set (T01–T04, T08, T12, T15, T16): pass.

## 7. Prevention / lesson

**Check both ends of a trunk.** A trunk has two independent allowed lists, and the healthy end looks perfect,
so a one-sided check finds nothing. Test T05 compares both ends for this reason.

Two supporting controls: always edit an allowed list with `add` or `remove` rather than retyping it, and treat
"one VLAN broken on one switch only" as a trunk problem until proven otherwise — the scope names the suspect
before any command is typed.
