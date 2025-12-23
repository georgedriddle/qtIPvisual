"""Generate sample data for qtIPvisual testing"""

import yaml
import random
from ipaddress import IPv4Network

# Sample data pools
locations = [
    "New York",
    "London",
    "Tokyo",
    "Sydney",
    "Paris",
    "Berlin",
    "Toronto",
    "Singapore",
    "Mumbai",
    "São Paulo",
]
departments = [
    "Engineering",
    "Sales",
    "Marketing",
    "HR",
    "Finance",
    "IT",
    "Operations",
    "R&D",
    "Support",
    "Legal",
]
statuses = [
    "Active",
    "Inactive",
    "Testing",
    "Production",
    "Staging",
    "Development",
    "Reserved",
    "Deprecated",
]
owners = [
    "Alice Johnson",
    "Bob Smith",
    "Carol Davis",
    "David Brown",
    "Eve Wilson",
    "Frank Miller",
    "Grace Lee",
    "Henry Wang",
    "Iris Chen",
    "Jack Martinez",
]
descriptions = [
    "Primary network segment",
    "Secondary backup network",
    "Guest network access",
    "Management network",
    "Storage network",
    "VoIP network segment",
    "IoT device network",
    "DMZ network zone",
    "Internal application servers",
    "Database cluster network",
]

# Base networks to subnet from
base_networks = ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]


def generate_random_subnet(base_net_str, min_prefix=16, max_prefix=28):
    """Generate a random subnet from a base network"""
    base_net = IPv4Network(base_net_str)
    prefix_len = random.randint(min_prefix, max_prefix)

    # Generate random subnet within base network
    max_subnets = 2 ** (prefix_len - base_net.prefixlen)
    subnet_num = random.randint(0, max_subnets - 1)

    subnets = list(base_net.subnets(new_prefix=prefix_len))
    if subnet_num < len(subnets):
        return str(subnets[subnet_num])
    return str(subnets[0])


def generate_sample_data(num_records=100):
    """Generate sample data with random fields and networks"""

    # Define fields
    fields = {
        "Name": {
            "controlType": "lineEdit",
            "colorMap": {r"prod": "lightgreen", r"test": "yellow", r"dev": "lightblue"},
            "colorWeight": 5,
            "show": True,
        },
        "Location": {
            "controlType": "lineEdit",
            "colorMap": {
                r"New York|London": "lightcoral",
                r"Tokyo|Singapore": "lightblue",
                r"Paris|Berlin": "lightgreen",
            },
            "colorWeight": 3,
            "show": True,
        },
        "Department": {
            "controlType": "lineEdit",
            "colorMap": {
                r"Engineering|IT": "lightyellow",
                r"Sales|Marketing": "lightpink",
            },
            "colorWeight": 2,
            "show": True,
        },
        "Status": {
            "controlType": "lineEdit",
            "colorMap": {
                r"Active": "lightgreen",
                r"Production": "green",
                r"Testing": "yellow",
                r"Inactive|Deprecated": "lightgray",
            },
            "colorWeight": 10,
            "show": True,
        },
        "Owner": {
            "controlType": "lineEdit",
            "colorMap": {},
            "colorWeight": 1,
            "show": True,
        },
        "Description": {
            "controlType": "lineEdit",
            "colorMap": {r"Management|DMZ": "orange", r"Database|Storage": "lightcyan"},
            "colorWeight": 4,
            "show": False,
        },
        "VLAN": {
            "controlType": "lineEdit",
            "colorMap": {},
            "colorWeight": 1,
            "show": True,
        },
    }

    # Generate networks with random data
    networks = {}
    used_cidrs = set()

    # Generate mix of different prefix lengths
    prefix_distribution = {
        (16, 20): 10,  # Larger subnets/supernets
        (20, 24): 30,  # Medium subnets
        (24, 26): 40,  # Common /24 and /25
        (26, 29): 20,  # Smaller subnets
    }

    records_generated = 0

    for (min_prefix, max_prefix), count in prefix_distribution.items():
        for _ in range(count):
            if records_generated >= num_records:
                break

            # Generate unique CIDR
            attempts = 0
            while attempts < 100:
                base_net = random.choice(base_networks)
                cidr = generate_random_subnet(base_net, min_prefix, max_prefix)

                if cidr not in used_cidrs:
                    used_cidrs.add(cidr)
                    break
                attempts += 1

            if attempts >= 100:
                continue

            # Generate random field values
            network_data = {
                "Name": f"{random.choice(['prod', 'test', 'dev', 'staging'])}-{random.choice(['web', 'app', 'db', 'cache', 'api'])}-{random.randint(1, 99)}",
                "Location": random.choice(locations),
                "Department": random.choice(departments),
                "Status": random.choice(statuses),
                "Owner": random.choice(owners),
                "Description": random.choice(descriptions),
                "VLAN": str(random.randint(10, 999)),
            }

            networks[cidr] = network_data
            records_generated += 1

    return fields, networks


def create_sample_file(filename="sample_data.yaml", num_records=100):
    """Create a sample YAML file with generated data"""

    # Generate data for Tab 1 - Corporate Networks
    fields1, networks1 = generate_sample_data(num_records // 2)

    # Generate data for Tab 2 - Data Center Networks
    fields2, networks2 = generate_sample_data(num_records // 2)

    # Modify Tab 2 fields slightly
    fields2["Region"] = {
        "controlType": "lineEdit",
        "colorMap": {r"North|South": "lightblue", r"East|West": "lightgreen"},
        "colorWeight": 3,
        "show": True,
    }

    # Add region to network data
    regions = ["North", "South", "East", "West", "Central"]
    for net_data in networks2.values():
        net_data["Region"] = random.choice(regions)

    # Create tabs structure
    tabs_data = [
        {"name": "Corporate Networks", "fields": fields1, "networks": networks1},
        {"name": "Data Center Networks", "fields": fields2, "networks": networks2},
    ]

    save_data = {"tabs": tabs_data}

    # Write to YAML file
    with open(filename, "w") as f:
        yaml.dump(save_data, f, default_flow_style=False, sort_keys=False)

    print(f"Generated {len(networks1) + len(networks2)} records across 2 tabs")
    print(f"Tab 1: {len(networks1)} networks")
    print(f"Tab 2: {len(networks2)} networks")
    print(f"Saved to: {filename}")

    # Print some statistics
    all_networks = list(networks1.keys()) + list(networks2.keys())
    prefix_counts = {}
    for net in all_networks:
        prefix = net.split("/")[1]
        prefix_counts[prefix] = prefix_counts.get(prefix, 0) + 1

    print("\nPrefix distribution:")
    for prefix in sorted(prefix_counts.keys(), key=int):
        print(f"  /{prefix}: {prefix_counts[prefix]} networks")


if __name__ == "__main__":
    create_sample_file("sample_data.yaml", num_records=100)
