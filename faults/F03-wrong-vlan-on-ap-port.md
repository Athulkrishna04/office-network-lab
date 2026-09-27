# F03: Guest Wi-Fi landed in the IT VLAN and walked past the guest ACL

| Field | Value |
|---|---|
| Layer | L2 — access port VLAN assignment |
| Injected on | SW2, FastEthernet0/19 (the AP-GUEST uplink) |
| Date | 2026-09-27 |
| Detected by | T04 (guest leases from the GUEST pool) and T17 (guests cannot load the intranet) |

## 1. Symptom

**Nothing looked broken.** No user would have reported this — guest Wi-Fi still worked, the internet still
worked, and no link went down. It was caught by the routine isolation test.

**What was wrong**
- A guest laptop associated to `OFFICE-GUEST` and leased an **IT** address:

```text
C:\>ipconfig /release
   IP Address......................: 0.0.0.0
   ...
C:\>ipconfig /renew
   IP Address......................: 192.168.10.142
   Subnet Mask.....................: 255.255.255.192
   Default Gateway.................: 192.168.10.129
   DNS Server......................: 192.168.10.130
```

- From that laptop, the staff-only intranet loaded:

```text
http://intranet.office.test  →  "Office intranet — Staff only. If a guest device can read this page,
                                 guest isolation is broken."
```

**Scope:** every wireless guest, and only the security boundary. Connectivity was perfect; the *policy* was gone.

## 2. Hypotheses

1. The guest ACL was removed or emptied — *checked below, rejected*: GUEST-IN is intact and still applied.
2. The DHCP server is handing guests the wrong pool — *rejected*: a pool is chosen by the subnet the request
   arrives from, and `.142` with gateway `.129` is a correct **IT** lease, so the request genuinely arrived
   from the IT subnet.
3. The guest traffic is entering the network in the wrong VLAN. **Kept.**

Key reasoning: the address wasn't malformed, it was *correct for the wrong VLAN*. That means the fault is
upstream of DHCP — in where the access point's traffic is placed.

## 3. Commands run

### 3.1 `show access-lists GUEST-IN` on R1

```text
Extended IP access list GUEST-IN
    permit udp any any eq bootps (5 match(es))
    permit udp 192.168.10.192 0.0.0.63 host 192.168.10.130 eq domain
    deny ip 192.168.10.192 0.0.0.63 192.168.10.0 0.0.0.63
    deny ip 192.168.10.192 0.0.0.63 192.168.10.64 0.0.0.63
    deny ip 192.168.10.192 0.0.0.63 192.168.10.128 0.0.0.63
    permit ip 192.168.10.192 0.0.0.63 any
```

*What it told me:* the ACL is complete and still in place, but its deny counters are not moving. The ACL
matches on source `192.168.10.192/26`, and the guest now has a `192.168.10.128/26` address, so **no guest
traffic matches the policy any more**. The rule didn't fail — the traffic stopped being subject to it.

### 3.2 `show interfaces fa0/19 switchport` on SW2

```text
Name: Fa0/19
Switchport: Enabled
Administrative Mode: static access
Operational Mode: static access
Administrative Trunking Encapsulation: dot1q
Operational Trunking Encapsulation: native
Negotiation of Trunking: Off
Access Mode VLAN: 30 (IT)
```

*What it told me:* **Access Mode VLAN: 30 (IT)** on the access point's uplink. Every wireless client is being
bridged into the IT VLAN, so guest traffic reaches R1 on G0/0.30 — an interface with no ACL — instead of
G0/0.40, where GUEST-IN lives.

## 4. Root cause

The access point's switch port was moved from VLAN 40 to VLAN 30. Guest devices were therefore placed inside
the IT subnet, where they leased IT addresses and reached the router on an unfiltered subinterface. The guest
ACL was never touched and never failed: the traffic simply stopped arriving where the ACL was applied.

## 5. Fix

```text
SW2# configure terminal
SW2(config)# interface FastEthernet0/19
SW2(config-if)#  switchport access vlan 40
SW2(config-if)# end
```

## 6. Verification

```text
C:\>ipconfig /renew
   IP Address......................: 192.168.10.201
   Subnet Mask.....................: 255.255.255.192
   Default Gateway.................: 192.168.10.193
   DNS Server......................: 192.168.10.130
```

- T04 passes: the guest leases from the GUEST pool with gateway `.193`.
- T17 passes: `http://intranet.office.test` no longer loads from the guest laptop.
- Regression smoke set (T01–T04, T08, T12, T15, T16): pass.

## 7. Prevention / lesson

**A VLAN assignment is a security control, not just a connectivity setting.** This fault broke nothing and
alarmed nobody; a monitoring system watching for outages would never have seen it. What caught it was a test
that asserts something must *fail* — T17.

Controls worth having: keep the port map in `docs/ip-plan.md` as the source of truth and audit
`show vlan brief` against it; keep a description on every port so an unexpected VLAN stands out; and run the
negative isolation tests on a schedule, not only after changes. At a larger scale, 802.1X with dynamic VLAN
assignment would remove the reliance on a manually configured port.
