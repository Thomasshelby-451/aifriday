def compute_metrics(devices):

    total = len(devices)

    compliant = devices[devices["Compliance"] == "Compliant"].shape[0]

    drifted = devices[devices["Drift_Event"] > 0].shape[0]
    critical_drifts = devices[devices["Drift_Event"] >= 3].shape[0]

    provisioning_failures = devices[
        devices["Provision_Status"] == "Failure"
    ].shape[0]

    auto_remediated = devices[
        devices["Provision_Status"] == "Success"
    ].shape[0]

    avg_provision_time = round(devices["Provision_Time(min)"].mean(), 2)

    compliance_score = round((compliant / total) * 100) if total else 0

    return {
        "total": total,
        "compliant": compliant,
        "compliance_score": compliance_score,
        "drifted": drifted,
        "critical_drifts": critical_drifts,
        "provisioning_failures": provisioning_failures,
        "auto_remediated": auto_remediated,
        "avg_provision_time": avg_provision_time
    }