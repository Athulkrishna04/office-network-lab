# F05: Guests kept DHCP and DNS but lost everything else when the ACL's final permit was removed

| Field | Value |
|---|---|
| Layer | L4 — ACL policy |
| Injected on | R1, extended ACL `GUEST-IN` (applied inbound on G0/0.40) |
| Date | 2026-09-27 |
| Detected by | T15 (guests can reach the internet) |

## 1. Symptom

**Reported:** "The guest Wi-Fi says it's connected but nothing loads."

**What works**
- The guest laptop is associated and holds a valid lease:

```text
C:\>ipconfig
Wireless0 Connection:
   IPv4 Address....................: 192.168.10.201
   Subnet Mask.....................: 255.255.255.192
   Default Gateway.................: 192.168.10.193
```

- Name resolution still works:

```text
C:\>nslookup www.example.com
Server:  [192.168.10.130]
Address: 192.168.10.130

Non-authoritative answer:
Name:    www.example.com
Address: 198.51.100.10
```

**What doesn't**
- The guest cannot even reach its own gateway:

```text
C:\>ping 192.168.10.193
Reply from 192.168.10.193: Destination host unreachable.
Reply from 192.168.10.193: Destination host unreachable.
Packets: Sent = 4, Received = 0, Lost = 4 (100% loss)
```

- Web browsing fails: `http://www.example.com` → **Request Timeout**

**Scope:** guests only. Staff VLANs are unaffected.

## 2. Reading the symptom

This combination is diagnostic on its own, before any router command:

- DHCP works → broadcasts and the relay are fine, so this is not a VLAN, trunk or cabling fault.
- DNS works → the guest can reach a host in the **IT** subnet, which is further away than the gateway.
- Ping to the gateway fails with *Destination host unreachable* **from the gateway itself**.

A device that answers DHCP and DNS but refuses ICMP to its own address is not down — it is **filtering**.
And the fact that two specific protocols survive while everything else dies points at an ACL with explicit
permits for those protocols and nothing else.

Note the wording of the failure: `Reply from 192.168.10.193: Destination host unreachable` means the router
answered and refused. A missing route or a dead gateway produces `Request timed out` instead.

## 3. Commands run

### 3.1 `show access-lists GUEST-IN` on R1

```text
Extended IP access list GUEST-IN
    permit udp any any eq bootps (7 match(es))
    permit udp 192.168.10.192 0.0.0.63 host 192.168.10.130 eq domain (2 match(es))
    deny ip 192.168.10.192 0.0.0.63 192.168.10.0 0.0.0.63
    deny ip 192.168.10.192 0.0.0.63 192.168.10.64 0.0.0.63
    deny ip 192.168.10.192 0.0.0.63 192.168.10.128 0.0.0.63
```

*What it told me:* the list ends at the third deny. The design has a sixth line,
`permit ip 192.168.10.192 0.0.0.63 any`, and it is gone. The counters corroborate the symptom exactly:
DHCP and DNS are matching and being permitted, and everything else falls through to the **implicit
`deny ip any any`** that ends every ACL.

That implicit deny is the whole fault. Nothing was added to block the guests — a permit was removed, and the
invisible rule at the bottom did the rest.

## 4. Root cause

The final `permit ip 192.168.10.192 0.0.0.63 any` was removed from `GUEST-IN`. With the explicit permits for
DHCP and DNS still in place, guests could lease addresses and resolve names, but every other packet — including
ICMP to their own gateway and all web traffic — hit the implicit deny at the end of the list.

## 5. Fix

```text
R1# configure terminal
R1(config)# ip access-list extended GUEST-IN
R1(config-ext-nacl)#  permit ip 192.168.10.192 0.0.0.63 any
R1(config-ext-nacl)# end
```

In a named ACL, a new line without a sequence number is appended to the **end** of the list, which is exactly
where this permit belongs: after the three denies, so it cannot override them.

## 6. Verification

A fix to a security control has to be verified in both directions — that what should work does, and that what
should stay blocked still is.

- **Must work:** the guest laptop loads `http://www.example.com` again.
- **Must stay blocked:** `http://intranet.office.test` from the guest laptop → **Request Timeout**, so the
  isolation rules were not weakened while restoring internet access.
- Regression smoke set (T01–T04, T08, T12, T15, T16): pass.

## 7. Prevention / lesson

**Every ACL ends with an invisible `deny ip any any`.** An ACL that looks like it only contains "deny" rules
for a few subnets actually blocks everything else as well, and the failure appears as a connectivity problem
rather than a policy one.

Controls that follow:
- Write the policy in plain words before writing the ACL, ending with what should be allowed after the denies
  (`docs/design-decisions.md`, D4). The final permit is then a stated requirement, not an afterthought.
- Test both halves of the policy, never just one: T15 proves guests keep the internet, while T16–T18 prove
  they stay out of the internal subnets. Checking only that "the block works" would have passed this fault.
- Use `show access-lists` counters as evidence. Lines with climbing counters show what is matching; a line that
  should exist and does not appear at all is far easier to spot in that output than in a config diff.
