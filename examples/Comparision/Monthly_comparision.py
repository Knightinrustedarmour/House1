import os
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# ----------------------------------------
# Configuration & Setup
# ----------------------------------------
try:   
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    file_path = os.path.join("Monthly_data.xlsx")
except NameError:
    print("Warning: Could not determine script directory. Ensure 'file_path' is correct.")
    file_path = os.path.join("Monthly_data.xlsx")

sheets = ["Original", "Additional PV", "Dynamic", "Load Shift"]
output_dir = "Matrix_Comparision_Plots"
os.makedirs(output_dir, exist_ok=True)

# Visual style
sns.set(style="whitegrid", context="talk")
plt.rcParams.update({'axes.titlesize': 12, 'axes.labelsize': 11})

# ----------------------------------------
# Helper functions
# ----------------------------------------
def extract_battery_size(name):
    """Extract numeric battery size in kWh, or 0 for 'PV_NoBattery'."""
    if "NoBattery" in str(name):
        return 0
    m = re.search(r"(\d+)", str(name))
    return float(m.group(1)) if m else np.nan

# ----------------------------------------
# Load & preprocess
# ----------------------------------------
data = []
for sheet in sheets:
    df = pd.read_excel(file_path, sheet_name=sheet)
    df.columns = df.columns.str.strip()
    df["Battery_kWh"] = df["Scenario"].apply(extract_battery_size)
    df["Sheet"] = sheet

    # For Additional PV: combine total PV production if PV2 exists
    if sheet == "Additional PV" and "Total_PV2_Production" in df.columns:
        df["Total_PV_Production"] = (
            df["Total_PV_Production"].fillna(0) + df["Total_PV2_Production"].fillna(0)
        )

    # Derived metrics
    df["SelfSufficiency"] = df["PV_Direct_Consumption"] / df["Demand_Consumption"]
    df["PV_SelfUse"] = df["PV_Direct_Consumption"] + df["Battery_Charge"]
    df["PV_Utilization"] = df["PV_SelfUse"] / df["Total_PV_Production"].replace({0: np.nan})
    df["Grid_Dependency"] = df["Grid_Import"] / df["Demand_Consumption"]
    df["PV_to_Demand_Ratio"] = df["Total_PV_Production"] / df["Demand_Consumption"]
    df["Net_Grid_Exchange"] = df["Grid_Import"] - df["Grid_Export_Sink"]
    data.append(df)

df_all = pd.concat(data, ignore_index=True)

# ----------------------------------------
# Aggregate annual metrics
# ----------------------------------------
agg = df_all.groupby(["Sheet", "Battery_kWh"], as_index=False).agg({
    "SelfSufficiency": "mean",
    "PV_Utilization": "mean",
    "Grid_Dependency": "mean",
    "PV_to_Demand_Ratio": "mean",
    "Net_Grid_Exchange": "mean",
    "Grid_Import": "sum",
    "Grid_Export_Sink": "sum",
})

# ----------------------------------------
# Metric setup
# ----------------------------------------
metrics = [
    ("PV_Utilization", "PV Utilization"),
    ("Grid_Dependency", "Grid Dependency"),
    ("PV_to_Demand_Ratio", "PV-to-Demand Ratio"),
    ("SelfSufficiency", "Self-Sufficiency"),
    ("Net_Grid_Exchange", "Net Grid Exchange [kWh]"),
    ("Grid_Import", "Grid Import [kWh]"),
    ("Grid_Export_Sink", "Grid Export [kWh]"),
]

# Define color palette per sheet
color_palette = sns.color_palette("viridis", len(sheets))
COLOR_MAP = {sheet: color_palette[i] for i, sheet in enumerate(sheets)}

# ----------------------------------------
# Create matrix of plots
# ----------------------------------------
nrows = 1  # all sheets on same plot per metric (color-coded)
ncols = len(metrics)
fig, axes = plt.subplots(nrows=1, ncols=ncols, figsize=(4.5 * ncols, 5), sharey=False)
plt.subplots_adjust(wspace=0.35, hspace=0.25)

for j, (col, label) in enumerate(metrics):
    ax = axes[j]
    for sheet in sheets:
        df = agg[agg["Sheet"] == sheet].sort_values("Battery_kWh")
        ax.plot(
            df["Battery_kWh"],
            df[col],
            marker="o",
            linewidth=2,
            color=COLOR_MAP[sheet],
            label=sheet
        )

    ax.set_title(label, fontsize=13, fontweight="bold")
    ax.set_xlabel("Battery Size (kWh)")
    ax.grid(True, alpha=0.3)
    if j == 0:
        ax.set_ylabel("Value")
    ax.legend(title="Scenario", fontsize=9, loc="best")

plt.suptitle("Matrix Comparison: Scenarios vs Battery Sizes Across Key Energy Metrics", fontsize=16, fontweight="bold", y=1.05)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "Scenario_Battery_Matrix_AllMetrics.png"), dpi=300, bbox_inches="tight")
plt.show()

print(f"✅ Matrix comparison plot saved in: {os.path.abspath(output_dir)}")

# ----------------------------------------
# Individual metric plots (larger figures)
# ----------------------------------------
for col, label in metrics:
    plt.figure(figsize=(8, 6))
    for sheet in sheets:
        df = agg[agg["Sheet"] == sheet].sort_values("Battery_kWh")
        plt.plot(
            df["Battery_kWh"],
            df[col],
            marker="o",
            linewidth=2.5,
            color=COLOR_MAP[sheet],
            label=sheet
        )
    
    plt.title(f"{label} vs Battery Size Across Scenarios", fontsize=14, fontweight="bold")
    plt.xlabel("Battery Size (kWh)")
    plt.ylabel(label)
    plt.grid(True, alpha=0.3)
    plt.legend(title="Scenario", fontsize=10, loc="best")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f"{col}_comparison.png"), dpi=300, bbox_inches="tight")
    plt.close()

print(f"✅ Individual metric plots saved in: {os.path.abspath(output_dir)}")

