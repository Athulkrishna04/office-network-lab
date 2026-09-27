# F01: Sales VLAN lost DHCP after the relay was removed

| Field | Value |
|---|---|
| Layer | L3 — router, DHCP relay |
| Injected on | R1, subinterface G0/0.10 (VLAN 10 SALES) |
| Date | 2026-09-27 |
| Detected by | T01 (every VLAN must lease from its own pool) |

## 1. Symptom

**Reported:** "Nobody in Sales can get on the network. HR and IT are fine."

**What works**
- PC-H1 (HR) keeps a valid lease: `192.168.10.76 / 255.255.255.192`, gateway `192.168.10.65`
- IT hosts are unaffected
- The DHCP server itself is clearly alive, because other VLANs are being served

**What doesn't**
- PC-S1 (Sales) cannot lease an address at all

```text
C:\>ipconfig /release
   IP Address......................: 0.0.0.0
   Subnet Mask.....................: 0.0.0.0
   Default Gateway.................: 0.0.0.0
   DNS Server......................: 0.0.0.0

C:\>ipconfig /renew
DHCP request failed.
```

**Scope:** VLAN 10 only, and on **both** switches (PC-S1 on SW1 and PC-S2 on SW2 behave the same).
A fault that follows the VLAN rather than the switch cannot be a cable, an access port or a single trunk —
it has to be something that is configured per VLAN. That points at the router subinterface or the DHCP pool.

## 2. Hypotheses

1. The Sales access ports left VLAN 10 — *rejected*: HR and IT ports are fine on the same switches, and a
   statically addressed Sales host can still reach its gateway.
2. Layer 2 path broken for VLAN 10 — *rejected*: with a manual address, PC-S1 pings `192.168.10.1` successfully,
   so the VLAN, the trunks and the gateway are all healthy.
3. Something VLAN-10-specific in how addresses are handed out — the router's relay, or the Sales pool. **Kept.**

## 3. Commands run

### 3.1 `ipconfig` on PC-H1 (a VLAN that works)

```text
FastEthernet0 Connection:(default port)
   IPv4 Address....................: 192.168.10.76
   Subnet Mask.....................: 255.255.255.192
   Default Gateway.................: 192.168.10.65
```

*What it told me:* the server is handing out leases normally to other VLANs, so the server and its pools
are not dead. The problem is specific to VLAN 10.

### 3.2 `show ip interface g0/0.10` on R1 (the broken VLAN)

```text
GigabitEthernet0/0.10 is up, line protocol is up (connected)
  Internet address is 192.168.10.1/26
  Broadcast address is 255.255.255.255
  Address determined by setup command
  MTU is 1500 bytes
  Helper address is not set
```

*What it told me:* **Helper address is not set.** The interface itself is up with the right address, so
routing for Sales is fine — but nothing is relaying DHCP.

### 3.3 `show ip interface g0/0.20` on R1 (a VLAN that works, for comparison)

```text
GigabitEthernet0/0.20 is up, line protocol is up (connected)
  Internet address is 192.168.10.65/26
  ...
  Helper address is 192.168.10.130
```

*What it told me:* HR's subinterface has the helper that Sales is missing. Comparing a broken thing with a
working thing that is configured the same way is what turned a vague symptom into a one-line difference.

## 4. Root cause

`ip helper-address 192.168.10.130` had been removed from G0/0.10. A DHCP DISCOVER is a broadcast, and routers
do not forward broadcasts, so without the helper the Sales client's request never reaches SRV-CORE in VLAN 30.
HR, Guest and IT were unaffected because HR and Guest still have their helpers and IT sits in the same VLAN as
the server, where no relay is needed at all.

## 5. Fix

```text
R1# configure terminal
R1(config)# interface GigabitEthernet0/0.10
R1(config-subif)#  ip helper-address 192.168.10.130
R1(config-subif)# end
```

## 6. Verification

```text
C:\>ipconfig /renew
   IP Address......................: 192.168.10.11
   Subnet Mask.....................: 255.255.255.192
```

- T01 passes again: PC-S1 leases `192.168.10.11` from the Sales pool.
- Regression smoke set (T01–T04, T08, T12, T15, T16): pass.

## 7. Prevention / lesson

The lesson is the diagnostic one: **scope tells you the layer.** One VLAN failing on every switch can only be
something configured per VLAN, which immediately ruled out cabling, access ports and trunks and took the search
straight to the four router subinterfaces.

As a control, the four subinterfaces should be built from one template and checked together, for example by
reading all four `show ip interface` outputs after any router change, since three of the four need a helper and
only the server's own VLAN does not. Test T01 covers every VLAN for exactly this reason.
