# Four-VLAN Office Network: Cisco Packet Tracer

> Designed a 4-VLAN office network in Packet Tracer (inter-VLAN routing, DHCP, DNS, NAT, ACLs); injected and resolved 6 faults with documented root cause and fix.

**Status:** baseline v1.0 built and verified; fault write-ups in progress.
**Packet Tracer version:** `9.0.1`. The `.pkt` files need Packet Tracer 9.0 or newer to open.

## What's in it

- **4 VLANs:** Sales 10, HR 20, IT 30 and Guest Wi-Fi 40, each a /26 of `192.168.10.0/24`
- **Inter-VLAN routing:** router-on-a-stick on R1 (802.1Q subinterfaces)
- **Central DHCP + DNS** on one server, with DHCP relayed to the other VLANs by `ip helper-address`
- **NAT (PAT)** to a simulated ISP that has no route back to private space
- **Guest ACL:** DHCP and DNS allowed, Sales/HR/IT denied, internet allowed
- **Port security:** sticky with max 1 on wired ports, max 10 on the AP uplink

## Topology

![Topology](diagrams/topology.png)

Source: [`diagrams/topology.drawio`](diagrams/topology.drawio) (draw.io).

## IP plan

| VLAN | Name | Subnet | Gateway | DHCP range |
|---|---|---|---|---|
| 10 | SALES | 192.168.10.0/26 | .1 | .11–.60 |
| 20 | HR | 192.168.10.64/26 | .65 | .75–.124 |
| 30 | IT | 192.168.10.128/26 | .129 | .140–.189 |
| 40 | GUEST | 192.168.10.192/26 | .193 | .200–.249 |

Full plan: [docs/ip-plan.md](docs/ip-plan.md). Validate it with `python tools/ipplan.py`.

## Verification

**22 of 22 tests pass**, including 5 negative tests where the traffic must be blocked (guest isolation). Full results, with the observed output for each test, are in [tests/verification-matrix.md](tests/verification-matrix.md).

Highlights:
- Every host leases from its own VLAN's pool; HR, Sales and Guest leases are relayed across the router to one central server.
- `show ip nat translations` shows inside addresses translated to the single public address 203.0.113.2, and the ISP has no route back to 192.168.10.0/24.
- Guests reach the internet but not Sales, HR or IT; blocked pings are refused by their own gateway (192.168.10.193), which is the ACL at work.
- A rogue laptop on SW1 Fa0/1 put the port into `err-disable` with a violation count of 1.

## Fault write-ups

| # | Layer | Fault | Write-up |
|---|---|---|---|
| F01 | L3 relay | Sales VLAN lost DHCP when the relay was removed | [F01](faults/F01-no-dhcp-relay.md) |
| F02 | L2 trunk | HR worked on one switch only after a VLAN was pruned from the trunk | [F02](faults/F02-vlan-missing-from-trunk.md) |
| F03 | L2 access | Guest Wi-Fi landed in the IT VLAN and bypassed the guest ACL | [F03](faults/F03-wrong-vlan-on-ap-port.md) |
| F04 | L3 host | HR's DHCP pool handed out the wrong default gateway | [F04](faults/F04-wrong-default-gateway.md) |
| F05 | L4 policy | Removing the ACL's final permit left guests with DHCP and DNS only | [F05](faults/F05-acl-blocks-too-much.md) |
| F06 | L7 | One wrong digit in a DNS A record took "the website" down | [F06](faults/F06-bad-dns-record.md) |

Each fault was injected into a copy of the baseline, diagnosed, fixed and then reverted, with the regression smoke set re-run after every fix. Every write-up carries the symptom, the commands run with their real output (dead ends included), the root cause, the fix, verification and a prevention control. The blank template is [faults/TEMPLATE.md](faults/TEMPLATE.md).

The faults climb the stack on purpose — access port, trunk, DHCP relay, host options, ACL, DNS — so the set shows a method rather than six lucky guesses. Two of them (F03 and F04) break no connectivity at all, which is what makes them worth reading.

## Repository layout

```
docs/          requirements, IP plan, design decisions
configs/       running-configs exported from the devices + server/endpoint GUI settings
tests/         verification matrix T01–T22
faults/        write-up template and the six fault write-ups
packet-tracer/ baseline .pkt + six challenge .pkt files
diagrams/      topology.drawio + topology.png
screenshots/   evidence referenced by tests and write-ups
tools/         ipplan.py
```

## How to open

1. Install Cisco Packet Tracer (the version above or newer) from Cisco Networking Academy.
2. Open `packet-tracer/office-baseline-v1.0.pkt` to see the working network.
3. Read the six write-ups in `faults/` to follow how each fault was found and fixed. Every fault can be reproduced in the baseline with the inject command listed at the top of its write-up.

## What I learned

- **Scope names the layer.** One VLAN down on every switch is a router or server problem; one VLAN down on one switch is a trunk problem; one host down is that host or its port. Deciding scope before typing a command shortened every diagnosis here.
- **Check both ends of a trunk.** In F02 the switch that reported the fault looked perfectly configured; the pruned VLAN was only visible from the other end of the same cable.
- **A working DHCP lease proves nothing about the options inside it** (F04), and a successful name lookup proves nothing about the address it returned (F06).
- **Every ACL ends with an invisible deny** (F05), so removing a permit is enough to cause an outage that looks like a connectivity failure.
- **Some faults break no connectivity at all.** F03 left the guest network fully working while quietly putting guests inside the IT subnet; only a test that asserts something must *fail* caught it.

## Roadmap (after v1.0)

SSH and hardening · DHCP snooping + DAI · NTP/syslog/TFTP backups · EtherChannel · L3 core switch + OSPF · IPv6 dual-stack · rebuild on real IOS (CML/GNS3) with Python checks.
