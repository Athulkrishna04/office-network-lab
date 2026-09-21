# Servers & endpoints (GUI settings)

Packet Tracer configures these devices through the GUI, not the CLI. In P5, screenshot each finished page into `screenshots/` as evidence.

## SRV-CORE (Server-PT): SW1 Fa0/13, VLAN 30

**Desktop → IP Configuration → Static**

| Field | Value |
|---|---|
| IPv4 address | 192.168.10.130 |
| Subnet mask | 255.255.255.192 |
| Default gateway | 192.168.10.129 |
| DNS server | 192.168.10.130 |

**Services → DHCP → Service: On**

The default `serverPool` **can't be deleted**, so edit it into the IT pool first and click **Save**. Then fill in each of the other pools and click **Add**.

| Pool name | Default gateway | DNS server | Start IP | Subnet mask | Max users | Hands out |
|---|---|---|---|---|---|---|
| serverPool (IT) | 192.168.10.129 | 192.168.10.130 | 192.168.10.140 | 255.255.255.192 | 50 | .140–.189 |
| SALES | 192.168.10.1 | 192.168.10.130 | 192.168.10.11 | 255.255.255.192 | 50 | .11–.60 |
| HR | 192.168.10.65 | 192.168.10.130 | 192.168.10.75 | 255.255.255.192 | 50 | .75–.124 |
| GUEST | 192.168.10.193 | 192.168.10.130 | 192.168.10.200 | 255.255.255.192 | 50 | .200–.249 |

How the server picks a pool: a relayed request carries the relay's address (`giaddr`, the subinterface IP such as 192.168.10.65), and the server uses the pool whose subnet contains it. IT clients aren't relayed, so they get `serverPool`, which matches the server's own subnet.

**Services → DNS → DNS Service: On** (it's **off** by default)

| Name | Type | Address |
|---|---|---|
| intranet.office.test | A Record | 192.168.10.130 |
| www.example.com | A Record | 198.51.100.10 |

**Services → HTTP**: keep it On and edit `index.html`:

```html
<h1>Office intranet</h1>
<p>Staff only. If a guest device can read this page, guest isolation is broken.</p>
```

(That sentence makes tests T17 and fault F1 easy to see in a screenshot.)

Optional hygiene: turn off services you don't use (FTP, EMAIL).

## WEB-EXT (Server-PT): ISP G0/1

| Field | Value |
|---|---|
| IPv4 address | 198.51.100.10 |
| Subnet mask | 255.255.255.0 |
| Default gateway | 198.51.100.1 |
| DHCP / DNS services | Off |

**Services → HTTP → index.html**

```html
<h1>www.example.com</h1>
<p>You reached the internet through R1's PAT.</p>
```

## AP-GUEST (AccessPoint-PT): Port 0 → SW2 Fa0/19

**Config → Port 1**

| Field | Value |
|---|---|
| SSID | OFFICE-GUEST |
| Authentication | WPA2-PSK |
| PSK pass phrase | `GuestLab2026` (lab-only placeholder) |
| Encryption | AES |

## Wireless clients

**LAPTOP-G1 (Laptop-PT)**
1. *Physical* tab: power off → drag out **PT-LAPTOP-NM-1CFE** → drag in **WPC300N** → power on.
2. *Config → Wireless0*: SSID `OFFICE-GUEST`, WPA2-PSK, same pass phrase.
3. *Desktop → IP Configuration*: **DHCP**. You should get an address in .200–.249 with gateway .193.

**PHONE-G1 (SMARTPHONE-PT)**: *Config → Wireless0* with the same SSID and pass phrase, IP configuration **DHCP**.

## Wired PCs (all DHCP)

| Device | Switch / port | VLAN | Expected lease |
|---|---|---|---|
| PC-S1 | SW1 Fa0/1 | 10 | .11–.60, gw .1 |
| PC-H1 | SW1 Fa0/7 | 20 | .75–.124, gw .65 |
| PC-IT1 | SW1 Fa0/14 | 30 | .140–.189, gw .129 |
| PC-S2 | SW2 Fa0/1 | 10 | .11–.60, gw .1 |
| PC-H2 | SW2 Fa0/7 | 20 | .75–.124, gw .65 |
| PC-IT2 | SW2 Fa0/13 | 30 | .140–.189, gw .129 |
| ROGUE (Laptop-PT) | *not cabled*; used only for T20 | n/a | n/a |

If a PC shows *DHCP request failed* right after the build, press **Fast Forward Time**, then click Static → DHCP again (or run `ipconfig /renew`).
