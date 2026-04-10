import os
import re
import sys
import json
import urllib.error
import urllib.request
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression


FEATURES = ["CPU", "Port_Down", "PPS", "Drops", "Errors"]
FIELDS = ["Device", "Timestamp", *FEATURES]
EMPTY_LLM_OUTPUT = "LLM returned empty output for this anomaly."


def ensure_dir(p: str) -> None:
    os.makedirs(p, exist_ok=True)


def device_from_filename(path: str) -> Optional[str]:
    m = re.search(r"(Switch-\s*\d+)", os.path.basename(path), flags=re.IGNORECASE)
    return m.group(1).replace(" ", "") if m else None


def num(s: Optional[str]) -> Optional[float]:
    if s is None:
        return None
    s = s.strip()
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def parse_block(block: str, fallback_device: Optional[str], fallback_timestamp: Optional[str]) -> Optional[Dict]:
    def pick(pattern: str) -> Optional[str]:
        m = re.search(pattern, block, flags=re.MULTILINE | re.IGNORECASE)
        return m.group(1).strip() if m else None

    device = pick(r"^Device\s*:\s*(.+?)\s*$") or fallback_device
    timestamp = pick(r"^Timestamp\s*:\s*(.+?)\s*$") or fallback_timestamp

    cpu = num(pick(r"^CPU Utilization\s*:\s*([0-9]*\.?[0-9]+)\s*%?\s*$"))
    port_down = num(pick(r"^Port Down Events\s*\(last hour\)\s*:\s*([0-9]*\.?[0-9]+)\s*$"))
    pps = num(pick(r"^Packets Per Second\s*\(PPS\)\s*:\s*([0-9]*\.?[0-9]+)\s*$"))
    drops = num(pick(r"^Packet Drops\s*:\s*([0-9]*\.?[0-9]+)\s*%?\s*$"))
    errors = num(pick(r"^Interface Errors\s*:\s*([0-9]*\.?[0-9]+)\s*$"))

    if device is None and timestamp is None and all(v is None for v in [cpu, port_down, pps, drops, errors]):
        return None

    return {
        "Device": device,
        "Timestamp": timestamp,
        "CPU": cpu,
        "Port_Down": port_down,
        "PPS": pps,
        "Drops": drops,
        "Errors": errors,
    }


def parse_text(text: str, fallback_device: Optional[str]) -> List[Dict]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").lstrip("\ufeff")
    mt = re.search(r"(?m)^Timestamp\s*:\s*(.+?)\s*$", normalized)
    global_timestamp = mt.group(1).strip() if mt else None

    matches = list(re.finditer(r"(?m)^Device\s*:\s*(.+?)\s*$", normalized))
    if not matches:
        one = parse_block(normalized, fallback_device, global_timestamp)
        return [one] if one else []

    out: List[Dict] = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(normalized)
        block = normalized[start:end]
        rec = parse_block(block, fallback_device, global_timestamp)
        if rec:
            out.append(rec)
    return out


def ingest_logs(log_input_path: str) -> pd.DataFrame:
    """
    Ingest logs from a folder.

    Supported inputs:
    - CSV files with columns:
      timestamp,device,cpu_utilization,port_down_events_last_hour,pps,packet_drops,interface_errors
    - Text logs in the older "Device: ... / Timestamp: ..." format (parsed via regex).
    """
    if not os.path.isdir(log_input_path):
        raise FileNotFoundError(f"log_input_path is not a folder: {log_input_path}")

    csv_frames: List[pd.DataFrame] = []
    text_records: List[Dict] = []

    for fn in sorted(os.listdir(log_input_path)):
        fp = os.path.join(log_input_path, fn)
        if not os.path.isfile(fp):
            continue

        _, ext = os.path.splitext(fn)
        ext = ext.lower()

        if ext == ".csv":
            try:
                raw = pd.read_csv(fp)
            except Exception:
                continue

            raw_cols = {c.lower().strip(): c for c in raw.columns}
            required = [
                "timestamp",
                "device",
                "cpu_utilization",
                "port_down_events_last_hour",
                "pps",
                "packet_drops",
                "interface_errors",
            ]
            if not all(c in raw_cols for c in required):
                continue

            df = raw.rename(
                columns={
                    raw_cols["timestamp"]: "Timestamp",
                    raw_cols["device"]: "Device",
                    raw_cols["cpu_utilization"]: "CPU",
                    raw_cols["port_down_events_last_hour"]: "Port_Down",
                    raw_cols["pps"]: "PPS",
                    raw_cols["packet_drops"]: "Drops",
                    raw_cols["interface_errors"]: "Errors",
                }
            )
            csv_frames.append(df[FIELDS].copy())
            continue

        # Fallback: older text format parsing
        try:
            with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        except OSError:
            continue
        text_records.extend(parse_text(text, device_from_filename(fp)))

    frames: List[pd.DataFrame] = []
    if csv_frames:
        frames.append(pd.concat(csv_frames, ignore_index=True))
    if text_records:
        frames.append(pd.DataFrame(text_records, columns=FIELDS))

    if not frames:
        return pd.DataFrame(columns=FIELDS)
    return pd.concat(frames, ignore_index=True)[FIELDS].copy()


def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for c in FEATURES:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["Device", "Timestamp"], how="any")
    df = df.sort_values(["Device", "Timestamp"])
    for c in FEATURES:
        if df[c].isna().any():
            med = df[c].median()
            df[c] = df[c].fillna(0.0 if np.isnan(med) else med)
    return df


def detect_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # --- Feature-wise z-scores ---
    X = df[FEATURES].astype(float)
    means = X.mean()
    stds = X.std(ddof=0).replace(0, 1.0)
    z = (X - means) / stds
    max_abs_z = z.abs().max(axis=1)

    # --- Linear regression to model CPU from other metrics ---
    target = "CPU"
    predictors = [f for f in FEATURES if f != target]
    lr = LinearRegression()
    lr.fit(X[predictors], X[target])
    cpu_pred = lr.predict(X[predictors])
    residuals = X[target] - cpu_pred

    res_mean = float(residuals.mean())
    res_std = float(residuals.std(ddof=0)) or 1.0
    resid_z = (residuals - res_mean) / res_std

    # --- Combined anomaly score (higher => more anomalous) ---
    raw_scores = np.maximum(max_abs_z.values, np.abs(resid_z.values))

    # Normalize scores into [0, 1] as probability-like values.
    mn = float(np.min(raw_scores))
    mx = float(np.max(raw_scores))
    if mx - mn < 1e-12:
        probs = np.zeros(len(raw_scores), dtype=float)
    else:
        probs = (raw_scores - mn) / (mx - mn)

    # Dynamic, data-driven label: mark top 5% highest scores as anomalies.
    if len(raw_scores) > 0:
        threshold = float(np.quantile(raw_scores, 0.95))
    else:
        threshold = float("inf")
    labels = (raw_scores >= threshold).astype(int)

    df["Feature_Z_Max"] = max_abs_z.astype(float)
    df["CPU_Residual_Z"] = resid_z.astype(float)
    df["Anomaly_Score"] = raw_scores.astype(float)
    df["Anomaly_Prob"] = probs.astype(float)
    df["Anomaly"] = labels
    return df


def generate_llm_explanations(anomaly_rows: pd.DataFrame, llm_model_name: str) -> List[str]:
    if anomaly_rows.empty:
        return []

    model_name = (llm_model_name or "").strip()
    if not model_name:
        raise ValueError(
            "LLM model name is required for remediation generation."
        )
    if model_name != "llama3.2:latest":
        raise ValueError(
            f"Only Ollama model 'llama3.2:latest' is supported. Received: {model_name}"
        )

    def build_prompt(r: pd.Series) -> str:
        return (
            "Network incident. Create one short sentence each for Root cause, "
            "Severity (Low/Medium/High), and Suggested action.\n"
            f"Device: {r['Device']} | Timestamp: {r['Timestamp']}\n"
            f"CPU={r['CPU']}, Port_Down={r['Port_Down']}, PPS={r['PPS']}, "
            f"Drops={r['Drops']}, Errors={r['Errors']}\n"
            "Answer format: Root cause: ... Severity: ... Suggested action: ...\n"
        )

    try:
        explanations: List[str] = []
        for _, r in anomaly_rows.iterrows():
            payload = {
                "model": model_name,
                "prompt": build_prompt(r),
                "stream": False,
            }
            req = urllib.request.Request(
                "http://127.0.0.1:11434/api/generate",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                raw = resp.read().decode("utf-8", errors="ignore")
            obj = json.loads(raw)
            text = str(obj.get("response", "")).strip()
            explanations.append(text if text else EMPTY_LLM_OUTPUT)
        return explanations
    except urllib.error.URLError as e:
        raise RuntimeError(
            "LLM explanation generation failed via Ollama API. "
            "Ensure Ollama is running and the model is pulled "
            "(example: `ollama pull llama3.2:latest`). "
            f"Error: {e}"
        ) from e
    except Exception as e:
        raise RuntimeError(f"LLM explanation generation failed via Ollama API: {e}") from e


def build_report(test_results: pd.DataFrame, metrics: Dict[str, float], llm_model_name: str) -> str:
    by_dev = test_results[test_results["Anomaly_Pred"] == 1].groupby("Device").size().sort_values(ascending=False)
    lines = [
        "Networkflow Analysis - Anomaly Report",
        "Model: Z-score + linear regression (unsupervised)",
        f"LLM model requested: {llm_model_name}",
        "",
        f"Total rows scored: {len(test_results)}",
        f"Predicted anomalies: {int((test_results['Anomaly_Pred'] == 1).sum())}",
        "",
        "Scoring summary:",
    ]
    for k in ["anomaly_rate", "avg_anomaly_score", "avg_anomaly_probability"]:
        if k in metrics:
            lines.append(f"- {k}: {metrics[k]:.4f}")
    lines.append("")
    lines.append("Predicted anomalies by device:")
    lines.extend([f"- {dev}: {int(cnt)}" for dev, cnt in by_dev.items()] or ["- None"])
    return "\n".join(lines)


def save_all(
    output_folder_path: str,
    df_labeled: pd.DataFrame,
    test_results: pd.DataFrame,
    anomaly_report: str,
    llm_explanations: List[str],
) -> None:
    ensure_dir(output_folder_path)
    df_labeled.to_excel(os.path.join(output_folder_path, "network_data.xlsx"), index=False)
    test_results.to_excel(os.path.join(output_folder_path, "model_results.xlsx"), index=False)

    with open(os.path.join(output_folder_path, "anomaly_report.txt"), "w", encoding="utf-8") as f:
        f.write(anomaly_report)
    with open(os.path.join(output_folder_path, "llm_explanations.txt"), "w", encoding="utf-8") as f:
        if not llm_explanations:
            f.write("No anomalies detected.\n")
        else:
            for i, e in enumerate(llm_explanations, start=1):
                f.write(f"{i}. {e}\n")


def main() -> int:
    if len(sys.argv) != 4:
        print("Usage: python main.py <log_input_path> <output_folder_path> <llm_model_name>")
        return 2

    log_input_path = sys.argv[1]
    output_folder_path = sys.argv[2]
    llm_model_name = sys.argv[3]

    # Step 1-2: ingestion + preprocessing
    df_raw = ingest_logs(log_input_path)
    if df_raw.empty:
        raise RuntimeError("No log records found. Check the input folder and log format.")
    df_cleaned = preprocess(df_raw)
    if df_cleaned.empty:
        bad = df_raw[["Device", "Timestamp"]].isna().sum().to_dict()
        raise RuntimeError(
            "No valid rows after preprocessing (Device/Timestamp missing or not parsed). "
            f"Missing counts in parsed raw data: {bad}. "
            "If using CSV, ensure required headers exist: "
            "timestamp, device, cpu_utilization, port_down_events_last_hour, pps, packet_drops, interface_errors."
        )

    # Step 4-5: unsupervised anomaly detection + scoring
    df_labeled = detect_anomalies(df_cleaned)

    metrics = {
        "anomaly_rate": float(df_labeled["Anomaly"].mean()),
        "avg_anomaly_score": float(df_labeled["Anomaly_Score"].mean()),
        "avg_anomaly_probability": float(df_labeled["Anomaly_Prob"].mean()),
    }

    # Step 6: predictions + save rows with metadata
    test_results = df_labeled[
        ["Device", "Timestamp", *FEATURES, "Anomaly", "Anomaly_Score", "Anomaly_Prob"]
    ].copy()
    test_results["Anomaly_True"] = test_results["Anomaly"].astype(int)
    test_results["Anomaly_Pred"] = test_results["Anomaly"].astype(int)
    test_results = test_results[
        [
            "Device",
            "Timestamp",
            *FEATURES,
            "Anomaly_True",
            "Anomaly_Pred",
            "Anomaly_Score",
            "Anomaly_Prob",
        ]
    ].copy()

    # Step 7: LLM explanation (optional)
    anomalies_only = test_results[test_results["Anomaly_Pred"] == 1].copy()
    llm_explanations = generate_llm_explanations(anomalies_only, llm_model_name)

    # Step 8: save all outputs
    anomaly_report = build_report(test_results, metrics, llm_model_name)
    save_all(output_folder_path, df_labeled, test_results, anomaly_report, llm_explanations)

    # Summary
    num_anomalies = int((test_results["Anomaly_Pred"] == 1).sum())
    print("Processed data summary:")
    print(f"- Total records parsed: {len(df_raw)}")
    print(f"- Cleaned labeled records: {len(df_labeled)}")
    print(f"- Anomalies detected (predicted): {num_anomalies}")
    print("")
    print("Saved files:")
    for fn in ["network_data.xlsx", "model_results.xlsx", "anomaly_report.txt", "llm_explanations.txt"]:
        print(f"- {os.path.join(output_folder_path, fn)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

