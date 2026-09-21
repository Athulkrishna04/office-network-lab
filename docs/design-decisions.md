# Design decisions

One entry per choice, in the form **context → decision → consequence**. Add an entry whenever an enhancement changes the design.

### D1: Router-on-a-stick, not an L3 switch
- **Context:** four VLANs, light traffic, a CCNA-level lab.
- **Decision:** R1 routes between VLANs with 802.1Q subinterfaces on G0/0.
- **Consequence:** simple and easy to inspect (`show ip interface brief`). All inter-VLAN traffic crosses one link twice, which is fine at this size. E5 migrates to an L3 switch and compares the two.

### D2: Central server in the IT VLAN, relays everywhere else
- **Context:** the four /26s use up the whole /24, so there's no spare subnet for a server VLAN.
- **Decision:** SRV-CORE (192.168.10.130) lives in VLAN 30. G0/0.10, .20 and .40 relay DHCP with `ip helper-address`, and .30 doesn't need to.
- **Consequence:** IT keeps working if relay breaks, which makes an asymmetric symptom useful for diagnosis (F3). Guests must be explicitly allowed DHCP and DNS through their ACL.

### D3: Two access switches joined by a trunk
- **Decision:** SW1 (with the router uplink) and SW2 (downstream), with the same port blocks on each.
- **Consequence:** trunk faults affect only one switch's hosts (F2). Hosts in every VLAN exist on both switches, so a fault's scope points to where it is.

### D4: Named extended ACL `GUEST-IN`, inbound on G0/0.40
- **Decision:** filter guest traffic as it enters the router (an extended ACL as close to the source as possible). Permit DHCP and DNS first, deny the three internal /26s, then permit everything else.
- **Consequence:** internal → guest pings fail too, because the replies are dropped (T22, intended). An ACL with no final permit blocks everything, which is what F5 injects.

### D5: PAT on the WAN interface; the ISP has no route back
- **Decision:** `ip nat inside source list 1 interface G0/1 overload`.
- **Consequence:** one public address serves every VLAN. The missing ISP route proves the translation is necessary (T14).

### D6: VTP transparent
- **Decision:** VLANs are configured on each switch by hand.
- **Consequence:** no accidental VLAN deletion through VTP revision numbers, at the cost of creating VLANs twice (trivial with two switches).

### D7: Explicit trunk allowed lists
- **Decision:** `switchport trunk allowed vlan 10,20,30,40`.
- **Consequence:** only intended VLANs cross the trunks. Edits must use `add` and `remove`, never a retyped list (F2's prevention).

### D8: Two port-security profiles
- **Decision:** wired ports use max 1 + sticky + shutdown. AP uplinks use max 10 + restrict, with no sticky.
- **Consequence:** a swapped-in device err-disables a desk port (T20), while guest Wi-Fi isn't killed by its second client.

### D9: Static default route, no dynamic routing in v1
- **Decision:** `ip route 0.0.0.0 0.0.0.0 203.0.113.1`.
- **Consequence:** a single router has no routing peers, so a routing protocol would add nothing. OSPF arrives in E5.

### D10: Documentation-reserved addresses and names
- **Decision:** 203.0.113.0/30 and 198.51.100.0/24 (RFC 5737); `.test` and `example.com` (RFC 2606).
- **Consequence:** the lab can never collide with real networks or domains, and reviewers see the convention was followed on purpose.
