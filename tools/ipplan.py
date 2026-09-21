"""Validate and print the office IP plan: 192.168.10.0/24 split into four /26s.

Usage:
    python tools/ipplan.py              # aligned table + consistency checks
    python tools/ipplan.py --markdown   # table as Markdown (for the README)

Checks that each DHCP range stays inside its subnet, avoids the gateway and the
broadcast address, and doesn't overlap any static address.
"""
import ipaddress
import sys

BLOCK = ipaddress.ip_network("192.168.10.0/24")

# (name, VLAN, first DHCP address, pool size, static addresses in that subnet)
PLAN = [
    ("SALES", 10, "192.168.10.11", 50, []),
    ("HR", 20, "192.168.10.75", 50, []),
    ("IT", 30, "192.168.10.140", 50, ["192.168.10.130", "192.168.10.131", "192.168.10.132"]),
    ("GUEST", 40, "192.168.10.200", 50, []),
]


def problems(net, gateway, first, last, statics):
    found = []
    if first not in net or last not in net or last == net.broadcast_address:
        found.append(f"DHCP range {first}-{last} leaves {net}")
    if first <= gateway <= last:
        found.append(f"gateway {gateway} is inside the DHCP range")
    for ip in statics:
        if ip not in net:
            found.append(f"static {ip} is outside {net}")
        elif first <= ip <= last:
            found.append(f"static {ip} is inside the DHCP range")
    return found


def main():
    subnets = list(BLOCK.subnets(new_prefix=26))
    if len(subnets) != len(PLAN):
        sys.exit(f"{BLOCK} gives {len(subnets)} /26s but the plan has {len(PLAN)} VLANs")

    header = ["VLAN", "Name", "Subnet", "Mask", "Wildcard", "Gateway", "Usable", "Broadcast", "DHCP range"]
    rows, failures = [], []
    for (name, vlan, start, size, statics), net in zip(PLAN, subnets):
        hosts = list(net.hosts())
        gateway = hosts[0]
        first = ipaddress.ip_address(start)
        last = first + (size - 1)
        static_ips = [ipaddress.ip_address(s) for s in statics]
        failures += [f"VLAN {vlan} {name}: {p}" for p in problems(net, gateway, first, last, static_ips)]
        rows.append([
            str(vlan), name, str(net), str(net.netmask), str(net.hostmask), str(gateway),
            f"{hosts[0]}-{hosts[-1]} ({len(hosts)})", str(net.broadcast_address), f"{first}-{last}",
        ])

    if "--markdown" in sys.argv:
        print("| " + " | ".join(header) + " |")
        print("|" + "---|" * len(header))
        for row in rows:
            print("| " + " | ".join(row) + " |")
    else:
        widths = [max(len(cell) for cell in column) for column in zip(header, *rows)]
        for row in [header, *rows]:
            print("  ".join(cell.ljust(width) for cell, width in zip(row, widths)))

    if failures:
        print("\nFAIL:\n  " + "\n  ".join(failures), file=sys.stderr)
        sys.exit(1)
    print(f"\nOK: {BLOCK} -> {len(subnets)} x /26; gateways, DHCP ranges and statics are consistent.",
          file=sys.stderr)


if __name__ == "__main__":
    main()
