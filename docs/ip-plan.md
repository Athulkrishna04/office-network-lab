# IP & VLAN plan (source of truth)

If a device config and this file disagree, **this file wins**: fix the device, or change this file on purpose and commit that change. Validate with `python tools/ipplan.py`.

## Address block

One private block, `192.168.10.0/24`, split into four equal `/26` subnets: mask `255.255.255.192`, wildcard `0.0.0.63`, 62 usable hosts each.

| VLAN | Name | Subnet | Gateway (R1) | Usable | Broadcast | DHCP range (50) | Reserved for statics |
|---|---|---|---|---|---|---|---|
| 10 | SALES | 192.168.10.0/26 | 192.168.10.1 | .1–.62 | .63 | .11–.60 | .2–.10 (printers), .61–.62 |
| 20 | HR | 192.168.10.64/26 | 192.168.10.65 | .65–.126 | .127 | .75–.124 | .66–.74, .125–.126 |
| 30 | IT | 192.168.10.128/26 | 192.168.10.129 | .129–.190 | .191 | .140–.189 | .130–.139, .190 |
| 40 | GUEST | 192.168.10.192/26 | 192.168.10.193 | .193–.254 | .255 | .200–.249 | .194–.199, .250–.254 |

Enhancement VLANs (E1): **998 PARKING** (unused ports, shut down) and **999 NATIVE** (trunk native VLAN, no hosts, no IP).

## Static assignments

| Address | Device / interface | Notes |
|---|---|---|
| 192.168.10.1 | R1 G0/0.10 | Sales gateway, helper → .130 |
| 192.168.10.65 | R1 G0/0.20 | HR gateway, helper → .130 |
| 192.168.10.129 | R1 G0/0.30 | IT gateway, no helper (server is local) |
| 192.168.10.130 | SRV-CORE | DHCP, DNS, HTTP (intranet) |
| 192.168.10.131 | SW1 VLAN 30 SVI | management |
| 192.168.10.132 | SW2 VLAN 30 SVI | management |
| 192.168.10.193 | R1 G0/0.40 | Guest gateway, helper → .130, GUEST-IN inbound |
| 203.0.113.1 /30 | ISP G0/0 | RFC 5737 documentation range |
| 203.0.113.2 /30 | R1 G0/1 | `ip nat outside`, PAT address |
| 198.51.100.1 /24 | ISP G0/1 | "internet" gateway |
| 198.51.100.10 /24 | WEB-EXT | `www.example.com` |

## Port map (same port blocks on both switches)

| Ports | VLAN | Port security |
|---|---|---|
| Fa0/1–6 | 10 SALES | max 1, sticky, shutdown |
| Fa0/7–12 | 20 HR | max 1, sticky, shutdown |
| Fa0/13–18 | 30 IT | max 1, sticky, shutdown |
| Fa0/19–20 | 40 GUEST (AP uplinks) | max 10, restrict, no sticky |
| Fa0/21–24 | unused (VLAN 1 in MVP → 998 PARKING + shutdown in E1) | n/a |
| Gi0/1–2 | trunks, allowed 10,20,30,40 | n/a |

| Switch | Port | Connected device |
|---|---|---|
| SW1 | Gi0/1 | R1 G0/0 (trunk) |
| SW1 | Gi0/2 | SW2 Gi0/1 (trunk) |
| SW1 | Fa0/1 | PC-S1 |
| SW1 | Fa0/7 | PC-H1 |
| SW1 | Fa0/13 | SRV-CORE |
| SW1 | Fa0/14 | PC-IT1 |
| SW2 | Gi0/1 | SW1 Gi0/2 (trunk) |
| SW2 | Fa0/1 | PC-S2 |
| SW2 | Fa0/7 | PC-H2 |
| SW2 | Fa0/13 | PC-IT2 |
| SW2 | Fa0/19 | AP-GUEST (SSID OFFICE-GUEST) → LAPTOP-G1, PHONE-G1 |

## DNS records (SRV-CORE)

| Name | Type | Address |
|---|---|---|
| intranet.office.test | A | 192.168.10.130 |
| www.example.com | A | 198.51.100.10 |

The `.test` and `example.com` names are reserved for testing and documentation (RFC 2606), so lab names can't clash with real ones.

## Capacity

Each /26 has 62 usable addresses: 50 DHCP leases plus reserved statics. **Growth trigger:** when any department passes about 45 active hosts, redesign with VLSM (for example, Sales moves to a /25 from a new block). Log that in `design-decisions.md`.

## Naming conventions

- Devices: `ROLE-DEPTn`, for example `PC-S1`, `PC-H2`, `SRV-CORE`, `AP-GUEST`.
- Interface descriptions: `TRUNK to <peer> <port>`, `<DEPT> access`, `WAN to ISP G0/0`.
- Files: `F0N-<slug>` for faults, `Tnn-<what>.png` for test evidence.
