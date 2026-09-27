# F06: "The website is down" — one wrong digit in a DNS A record

| Field | Value |
|---|---|
| Layer | L7 — name resolution |
| Injected on | SRV-CORE, Services → DNS, A record for `www.example.com` |
| Date | 2026-09-27 |
| Detected by | T12 (staff reach the internet by name) and T15 (guests reach it by name) |

## 1. Symptom

**Reported:** "The website is down for everyone."

Every VLAN was affected at once, which usually suggests something central — the router, NAT or the internet
link. All three turned out to be healthy.

## 2. Commands run

### 2.1 `ping 198.51.100.10` on PC-S1 (the web server, by address)

```text
Pinging 198.51.100.10 with 32 bytes of data:

Reply from 198.51.100.10: bytes=32 time<1ms TTL=126
Reply from 198.51.100.10: bytes=32 time=147ms TTL=126
Reply from 198.51.100.10: bytes=32 time<1ms TTL=126
Reply from 198.51.100.10: bytes=32 time<1ms TTL=126

Packets: Sent = 4, Received = 4, Lost = 0 (0% loss)
```

*What it told me:* routing, NAT and the server are all fine. Whatever is broken sits above layer 3.

### 2.2 `ping www.example.com` on PC-S1 (the same server, by name)

```text
Pinging 198.51.100.100 with 32 bytes of data:

Request timed out.
Request timed out.
Request timed out.
Request timed out.

Packets: Sent = 4, Received = 0, Lost = 4 (100% loss)
```

*What it told me:* the fault in one line. Ping printed the address it was about to use — **198.51.100.100** —
and that is not the web server's address. The name resolved to the wrong host, so the packets went to an
address where nothing exists. Reading the first line of ping output, not just the result, is what made this
a thirty-second diagnosis.

### 2.3 `nslookup www.example.com` on PC-S1

```text
Server:  [192.168.10.130]
Address: 192.168.10.130

Non-authoritative answer:
Name:    www.example.com
Address: 198.51.100.100
```

*What it told me:* the answer comes from our own DNS server, so this is not an upstream or caching problem —
our record itself is wrong. `docs/ip-plan.md` lists `www.example.com → 198.51.100.10`, which makes the `.100`
answer a clear deviation from the documented design.

### 2.4 Web browser on PC-S1

```text
http://www.example.com  →  Request Timeout
```

*What it told me:* consistent with the ping. The browser is simply the user-visible version of the same fault.

## 3. Root cause

The A record for `www.example.com` on SRV-CORE pointed at `198.51.100.100` instead of `198.51.100.10` — one
extra digit. Clients resolved the name successfully and then sent traffic to a host that does not exist, so
every attempt timed out while the network underneath worked perfectly.

## 4. Fix

SRV-CORE → Services → DNS → select the `www.example.com` record → Address `198.51.100.10` → **Save**.

## 5. Verification

- `nslookup www.example.com` from PC-S1 returns `198.51.100.10`.
- `http://www.example.com` loads the WEB-EXT page again.
- T12 and T15 pass (staff and guests both reach the site by name).
- Regression smoke set (T01–T04, T08, T12, T15, T16): pass.

## 6. Prevention / lesson

**Test by IP and by name; the difference tells you the layer.** A reachable address with an unreachable name
can only be a resolution problem, and that single contrast skips the entire routing and NAT investigation
that "the internet is down" would normally trigger.

Controls:
- DNS records are documented in `docs/ip-plan.md`, so any answer can be compared against the design instead
  of being taken on trust.
- The test matrix deliberately separates T11 (reach the server by IP) from T12 (reach it by name) so that a
  broken record shows up as one failing test rather than a vague "internet down".
- Records are short and easy to mistype; a second pair of eyes on a DNS change costs less than an outage that
  looks like a routing failure.
