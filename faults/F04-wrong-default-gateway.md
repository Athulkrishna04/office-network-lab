# F04: HR's DHCP pool handed out the wrong default gateway

| Field | Value |
|---|---|
| Layer | L3 — DHCP options (host configuration) |
| Injected on | SRV-CORE, Services → DHCP, **HR** pool |
| Date | 2026-09-27 |
| Detected by | T02 (HR leases carry gateway 192.168.10.65) |

## 1. Symptom

This one is quiet: **DHCP succeeds**, and the address looks normal at a glance.

```text
C:\>ipconfig /renew
   IP Address......................: 192.168.10.75
   Subnet Mask.....................: 255.255.255.192
   Default Gateway.................: 192.168.10.1
   DNS Server......................: 192.168.10.130
```

The address and mask are right for HR (`192.168.10.64/26`), but the gateway is **192.168.10.1** — that is
Sales' gateway, and it is not even inside HR's subnet. HR's gateway should be `192.168.10.65`.

**Scope:** every host in VLAN 20, on both switches, from their next lease onwards. Hosts that had not yet
renewed kept working with their old, correct gateway — so the fault would have spread gradually as leases
came up for renewal, which is what makes this class of fault confusing in the field.

## 2. Hypotheses

1. The host was configured by hand — *rejected*: it is a DHCP client, and `ipconfig /all` lists
   `DHCP Servers: 192.168.10.130`, so the wrong value was **handed to it**.
2. The router's HR subinterface changed address — *rejected*: see 3.2, `192.168.10.65` answers pings.
3. The HR pool on the server is handing out the wrong gateway option. **Kept.**

## 3. Commands run

### 3.1 `ipconfig /all` on PC-H1

```text
   IPv4 Address....................: 192.168.10.75
   Subnet Mask.....................: 255.255.255.192
   Default Gateway.................: 192.168.10.1
   DHCP Servers....................: 192.168.10.130
   DNS Servers.....................: 192.168.10.130
```

*What it told me:* the lease itself is fine; one **option** inside it is wrong. A working DHCP exchange does
not mean the options it carries are correct.

### 3.2 `ping 192.168.10.65` from PC-H1 (the gateway HR *should* have)

```text
Reply from 192.168.10.65: bytes=32 time<1ms TTL=255
Reply from 192.168.10.65: bytes=32 time<1ms TTL=255
Packets: Sent = 4, Received = 4, Lost = 0 (0% loss)
```

*What it told me:* the real HR gateway is alive and reachable. The router is not the problem — the host has
simply been pointed somewhere else.

### 3.3 `ping 192.168.10.130` from PC-H1 (off-subnet, through the gateway)

```text
Reply from 192.168.10.130: bytes=32 time<1ms TTL=127
Packets: Sent = 4, Received = 4, Lost = 0 (0% loss)
```

*What it told me:* **it still worked**, which was not what I expected from a host with an unusable gateway.
See "Why there was no outage" below — this is the most interesting part of the case.

### 3.4 SRV-CORE → Services → DHCP → HR pool

```text
Pool Name:        HR
Default Gateway:  192.168.10.1        <-- wrong, should be 192.168.10.65
DNS Server:       192.168.10.130
Start IP Address: 192.168.10.75
Subnet Mask:      255.255.255.192
Maximum Users:    50
```

*What it told me:* the root cause, in one screen. Everything else in the pool is correct, and `.1` is the
value from the Sales pool directly above it — the signature of a copy-paste edit.

## 4. Root cause

The HR pool's Default Gateway option was set to `192.168.10.1` (the Sales gateway) instead of
`192.168.10.65`. Every HR host that renewed after the change was configured to send off-subnet traffic to an
address that does not exist in its own subnet.

## 5. Why there was no outage

`192.168.10.1` is not in HR's `192.168.10.64/26`, so by the textbook HR should have lost everything beyond
its own subnet. It didn't, and the reason is **proxy ARP**, which is enabled by default on the router's
subinterfaces (visible as `Proxy ARP is enabled` in `show ip interface g0/0.20`).

When the host tried to reach an off-subnet address it ARPed for its configured gateway, `192.168.10.1`. That
request reached R1 on G0/0.20. R1 knows how to reach `192.168.10.1` — it owns it on another subinterface —
so it answered the ARP with its **own** MAC address. The host then sent its traffic to R1 and everything
routed normally.

So the misconfiguration was **masked**, and that is the real lesson: the fault was latent, not harmless. It
would have become an outage the moment proxy ARP was disabled (a common hardening step), or if the address
handed out had been one the router could not reach.

*Status of this explanation:* proxy ARP is confirmed enabled on the subinterface, and it accounts for the
observed behaviour. The confirming experiment — hold the wrong gateway, disable proxy ARP on G0/0.20, and
watch off-subnet pings start failing — was attempted but not completed: the host had already renewed with
the corrected gateway, so the test proved nothing either way. Worth repeating properly.

## 6. Fix

SRV-CORE → Services → DHCP → **HR** pool → Default Gateway → `192.168.10.65` → **Save**, then renew the
affected hosts.

```text
C:\>ipconfig /release
C:\>ipconfig /renew
   IP Address......................: 192.168.10.75
   Subnet Mask.....................: 255.255.255.192
   Default Gateway.................: 192.168.10.65
   DNS Server......................: 192.168.10.130
```

## 7. Verification

- T02 passes: HR hosts lease `.75–.124` with gateway `192.168.10.65`.
- Regression smoke set (T01–T04, T08, T12, T15, T16): pass.

## 8. Prevention / lesson

**A successful lease proves nothing about the options inside it.** Test T02 checks the gateway and DNS
values, not just that an address appeared — this fault is exactly why it is written that way.

Two controls follow from this case:
- The DHCP pool table in `docs/ip-plan.md` is the source of truth; pool edits get checked against it, since
  the four pools differ only by a few digits and sit next to each other in one screen.
- A fault that is masked by a default behaviour is still a fault. Anything "working by accident" gets fixed
  and written down, because the accident disappears the day someone hardens the router.
