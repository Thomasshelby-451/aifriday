import csv
import random
from datetime import datetime, timedelta

# Sample values
sites = ["Chennai", "Bangalore", "Mumbai", "Delhi", "Hyderabad"]
device_models = ["Cisco2900", "JuniperEX", "Arista7050", "CiscoNexus", "HPProCurve"]
os_versions = ["v1.0", "v1.1", "v1.2", "v2.0"]

failure_reasons = [
    "Timeout",
    "Config Error",
    "Auth Failure",
    "Network Issue",
    "None"
]

def random_ip():
    return f"192.168.{random.randint(0,255)}.{random.randint(1,254)}"

def generate_record(i):
    provisioning_status = random.choice(["Success", "Failed"])
    config_drift = random.choice([True, False])
    unauthorized = random.choice([True, False])

    expected_os = random.choice(os_versions)
    actual_os = random.choice(os_versions)

    compliance_status = "Compliant"
    if config_drift or actual_os != expected_os:
        compliance_status = "Non-Compliant"

    last_provisioned = datetime.now() - timedelta(hours=random.randint(1, 100))

    return {
        "device_id": f"dev-{i:03}",
        "site": random.choice(sites),
        "device_model": random.choice(device_models),
        "os_version": actual_os,
        "expected_os_version": expected_os,
        "ip_address": random_ip(),
        "provisioning_status": provisioning_status,
        "failure_reason": "None" if provisioning_status == "Success" else random.choice(failure_reasons[:-1]),
        "last_provisioned_at": last_provisioned.strftime("%Y-%m-%d %H:%M:%S"),
        "config_drift": config_drift,
        "compliance_status": compliance_status,
        "sla_deadline_hours": random.randint(24, 72),
        "onboarding_age_hours": random.randint(1, 120),
        "unauthorized_device": unauthorized
    }

# Generate 50 records
data = [generate_record(i) for i in range(1, 51)]

# Save to CSV
with open("network_inventory.csv", "w", newline="") as file:
    writer = csv.DictWriter(file, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)

print("✅ Generated network_inventory.csv with 50 records")