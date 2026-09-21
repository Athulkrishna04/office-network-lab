# Fault catalog

Six faults that climb the stack from L2 to L7. Each one is **injected into its own copy** of `office-baseline-v1.0.pkt`, never into the baseline itself.

This file is the **design** of each fault: how to inject it, how to trigger it and how to restore it, plus the diagnostic path you'd *expect*. The write-ups (`F0N-*.md`, from `TEMPLATE.md`) record what you **actually observed**, with real output.

| # | Layer | Fault | Injected on | Caught by | Write-up |
|---|---|---|---|---|---|
| F1 | L2 access | Wrong VLAN on a port | SW2 Fa0/19 | T04, T17 | `F01-wrong-vlan-ap-port.md` |
| F2 | L2 trunk | VLAN missing from trunk | SW1 Gi0/2 | T02, T05 | `F02-vlan-missing-from-trunk.md` |
| F3 | L3 boundary | No DHCP relay | R1 G0/0.10 | T01 | `F03-no-dhcp-relay.md` |
| F4 | L3 host | Wrong default gateway | SRV-CORE HR pool | T02, T12 | `F04-wrong-default-gateway.md` |
| F5 | L4 policy | ACL blocks too much | R1 GUEST-IN | T15 | `F05-acl-blocks-too-much.md` |
| F6 | L7 | Bad DNS record | SRV-CORE DNS | T12, T15 | `F06-bad-dns-record.md` |

After every fix, run the **regression smoke set**: T01–T04 · T08 · T12 · T15 · T16.

---

## F1: Wrong VLAN on a port (L2 access)

| | |
|---|---|
| **Inject** | SW2: `configure terminal` → `interface FastEthernet0/19` → `switchport access vlan 30` → `end` |
| **Trigger** | LAPTOP-G1: `ipconfig /release`, then `ipconfig /renew` |
| **Restore** | SW2: `interface FastEthernet0/19` → `switchport access vlan 40`, then the clients renew |

- **Expected symptom:** nothing looks down. The guest laptop gets a **192.168.10.140–.189** (IT) address with gateway .129, and the *staff-only* intranet page loads on a guest device. It's a silent security failure, found by T04 and T17.
- **Commands that separate it from other faults:**
  - LAPTOP-G1 `ipconfig /all`: the address is in the IT subnet.
  - SW2 `show vlan brief`: Fa0/19 is listed under VLAN 30 IT.
  - SW2 `show interfaces fa0/19 switchport`: *Access Mode VLAN: 30 (IT)*.
  - SW2 `show mac address-table interface fa0/19`: the wireless clients' MACs appear in VLAN 30.
  - R1 `show access-lists GUEST-IN`: the counters stop climbing, because guest traffic now enters on G0/0.30, which has no ACL.
- **Root cause:** the AP uplink is in VLAN 30, so guests are bridged into the IT subnet, where GUEST-IN doesn't apply.
- **Prevention:** `ip-plan.md` is the port map of record; audit `show vlan brief` against it; every port has a description. Enhancement: 802.1X with dynamic VLAN assignment.

## F2: VLAN missing from the trunk (L2 trunk)

| | |
|---|---|
| **Inject** | SW1: `interface GigabitEthernet0/2` → `switchport trunk allowed vlan remove 20` |
| **Trigger** | PC-H2: `ipconfig /renew` |
| **Restore** | SW1: `interface GigabitEthernet0/2` → `switchport trunk allowed vlan add 20` |

- **Expected symptom:** PC-H2 (HR on SW2) gets **169.254.x.x** (APIPA), while PC-H1 (HR on SW1) is fine and the other VLANs on SW2 are fine. The scope is *one VLAN on one switch*, which points at the path between the two switches.
- **Commands that separate it from other faults:**
  - PC-H2 `ipconfig /all`: APIPA.
  - Give PC-H2 a temporary static 192.168.10.120/26 with gw .65 and `ping 192.168.10.65`: it **fails**, so the L2 path is broken, not just DHCP. Set it back to DHCP afterwards.
  - SW2 `show vlan brief`: Fa0/7 is in VLAN 20, so the access side is fine.
  - SW2 `show interfaces trunk`: Gi0/1 allows 10,20,30,40, so it *looks fine from this end*.
  - SW1 `show interfaces trunk`: Gi0/2 allows **10,30,40**. There it is.
- **Root cause:** VLAN 20 is pruned from SW1 Gi0/2's allowed list, so HR frames from SW2 are dropped at SW1.
- **Prevention:** only ever use `add` or `remove`, never a retyped list. Check `show interfaces trunk` on **both** ends, which is what T05 does.

## F3: No DHCP relay (L3 boundary)

| | |
|---|---|
| **Inject** | R1: `interface GigabitEthernet0/0.10` → `no ip helper-address 192.168.10.130` |
| **Trigger** | PC-S1 and PC-S2: `ipconfig /renew` |
| **Restore** | R1: `interface GigabitEthernet0/0.10` → `ip helper-address 192.168.10.130` |

- **Expected symptom:** every Sales host on **both** switches gets APIPA, while HR, IT and Guest are fine. The scope is one VLAN everywhere, which points at something VLAN-10-specific on the router or server.
- **Commands that separate it from other faults:**
  - Give PC-S1 a temporary static 192.168.10.20/26 with gw .1 and `ping 192.168.10.1`: it **succeeds**, so L2 and the subinterface are fine and the problem is DHCP-specific.
  - R1 `show ip interface g0/0.10`: *Helper address is not set*. Compare it with `show ip interface g0/0.20`, which shows 192.168.10.130. (Or read both subinterfaces in `show running-config`.)
  - Simulation mode, filtered to DHCP: the DISCOVER reaches R1 and goes no further.
- **Root cause:** DHCP DISCOVER is a broadcast and routers don't forward broadcasts. Without a helper, nothing relays it to SRV-CORE in VLAN 30.
- **Prevention:** a template for each VLAN's subinterface; T01–T04 cover every VLAN after any router change.

## F4: Wrong default gateway (L3 host config)

| | |
|---|---|
| **Inject** | SRV-CORE → Services → DHCP → select the **HR** pool → Default Gateway `192.168.10.1` → **Save** |
| **Trigger** | PC-H1 and PC-H2: `ipconfig /renew` |
| **Restore** | HR pool → Default Gateway `192.168.10.65` → Save, then renew |

- **Expected symptom:** HR PCs get normal-looking addresses (.75+) and can ping each other, but can't reach the server, other VLANs, names or the internet.
- **Commands that separate it from other faults:**
  - PC-H1 `ipconfig /all`: *Default Gateway 192.168.10.1*, which isn't inside 192.168.10.64/26.
  - `ping 192.168.10.65`: **succeeds**, so the real gateway is alive and R1 is fine.
  - `tracert 192.168.10.130`: dies at hop 1.
  - SRV-CORE DHCP page: the HR pool shows gateway .1.
- **Root cause:** a copy-paste error means the HR pool hands out the Sales gateway, so hosts send off-subnet traffic to an address that doesn't exist in their VLAN.
- **Lesson:** a successful lease doesn't prove the options are correct.
- **Prevention:** review pool changes against the DHCP table in `ip-plan.md`.

## F5: ACL blocks too much (L4 policy)

| | |
|---|---|
| **Inject** | R1: `ip access-list extended GUEST-IN` → `no 60` |
| **Trigger** | none (takes effect immediately) |
| **Restore** | R1: `ip access-list extended GUEST-IN` → `60 permit ip 192.168.10.192 0.0.0.63 any` |

- **Expected symptom:** guests join the Wi-Fi, get an address, and names resolve, but no website loads and they **can't even ping their own gateway .193**. Staff are unaffected.
- **Commands that separate it from other faults:**
  - LAPTOP-G1 `ipconfig`: fine.
  - `nslookup www.example.com`: works, because line 20 still permits DNS.
  - `ping 192.168.10.193` and `ping 198.51.100.10`: both fail.
  - R1 `show ip interface g0/0.40`: *Inbound access list is GUEST-IN*.
  - R1 `show access-lists GUEST-IN`: only lines 10–50 remain, and the counters on 10 and 20 are climbing.
  - R1 `show ip nat translations`: nothing from the .200 range.
- **Root cause:** every ACL ends with an implicit `deny ip any any`, and line 60 was the only permit for general traffic.
- **Verify the fix both ways:** T15 must pass **and** T16–T18 must still fail.
- **Prevention:** write the policy before the ACL, and always test what must pass as well as what must fail.

## F6: Bad DNS record (L7)

| | |
|---|---|
| **Inject** | SRV-CORE → Services → DNS → select `www.example.com` → Address `198.51.100.100` → **Save** |
| **Trigger** | none |
| **Restore** | Address `198.51.100.10` → Save |

- **Expected symptom:** "the website is down" in every VLAN, but `ping 198.51.100.10` works.
- **Commands that separate it from other faults:**
  - PC-S1 `ping www.example.com`: *Pinging 198.51.100.100*, then timeouts.
  - `nslookup www.example.com`: Server 192.168.10.130, Address **198.51.100.100**, where `ip-plan.md` says .10.
  - R1 `show ip nat translations`: flows headed to .100.
  - ISP `ping 198.51.100.100`: fails, because no such host exists.
- **Root cause:** a typo in the A record.
- **Prevention:** DNS records are listed in `ip-plan.md`; T11 (by IP) and T12 (by name) together isolate DNS.
