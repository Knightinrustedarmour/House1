import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import numpy as np
import re

# --- Configuration & Setup ---
try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    file_path = os.path.join("Cost_table.xlsx")
except NameError:
    print("Warning: Could not determine script directory. Ensure 'file_path' is correct.")
    file_path = os.path.join("Cost_table.xlsx")

sheets = ["Orginal", "Additional PV", "Dynamic", "Load Shift"]

output_dir = "inter_scenario_plots"
os.makedirs(output_dir, exist_ok=True)

FIG_WIDTH = 14
FIG_HEIGHT = 6

sns.set(style="whitegrid", context="talk", font_scale=1.1)

# --- Helper function to extract battery size ---
def extract_battery_size(scenario_name):
    if "NoBattery" in str(scenario_name):
        return 0
    m = re.search(r"(\d+)", str(scenario_name))
    return float(m.group(1)) if m else np.nan

# --- Load Data ---
print(f"Loading data from: {file_path}")
data = {}

for sheet in sheets:
    try:
        df = pd.read_excel(file_path, sheet_name=sheet)
        df.columns = df.columns.str.strip()
        df["Scenario"] = df["Scenario"].astype(str)
        df["Battery_kW"] = df["Scenario"].apply(extract_battery_size)
        data[sheet] = df
    except Exception as e:
        print(f"Error loading sheet '{sheet}': {e}")

print("Data loaded successfully for all cases.")

# --- Plotting Functions ---
def investment_vs_cumulative_bar_plot(df, case_name):
    df = df.sort_values("Battery_kW")
    df["Cost Difference from base scenario"] = pd.to_numeric(df["Cost Difference from base scenario"], errors="coerce")
    df["Investment cost"] = pd.to_numeric(df["Investment cost"], errors="coerce")
    df["Cumulative_20yr_Savings"] = 20 * df["Cost Difference from base scenario"] - df["Investment cost"]
    
    battery_sizes = df["Battery_kW"].tolist()
    cumulative_savings = df["Cumulative_20yr_Savings"].tolist()
    investment_costs = df["Investment cost"].tolist()
    
    x = np.arange(len(battery_sizes))
    width = 0.4

    plt.figure(figsize=(FIG_WIDTH, FIG_HEIGHT))
    plt.bar(x - width/2, investment_costs, width=width, label="Investment Cost (€)", color=sns.color_palette("viridis", 3)[1])
    plt.bar(x + width/2, cumulative_savings, width=width, label="20-Year Cumulative Savings (€)", color=sns.color_palette("viridis", 3)[0])

    for i in range(len(x)):
        plt.text(x[i] - width/2, investment_costs[i] + max(investment_costs)*0.02, f"€{investment_costs[i]:,.0f}", ha="center", va="bottom", fontsize=9)
        plt.text(x[i] + width/2, cumulative_savings[i] + max(cumulative_savings)*0.02, f"€{cumulative_savings[i]:,.0f}", ha="center", va="bottom", fontsize=9)

    plt.xticks(x, [f"{int(b)} kW" if b > 0 else "NoBatt" for b in battery_sizes])
    plt.xlabel("Battery Size", fontsize=14)
    plt.ylabel("Euros (€)", fontsize=14)
    plt.title(f"{case_name}: Investment vs 20-Year Cumulative Savings", fontsize=18, fontweight="bold", pad=20)
    plt.grid(axis="y", linestyle="--", alpha=0.6)
    plt.legend(fontsize=11)
    plt.tight_layout()
    
    case_dir = os.path.join(output_dir, case_name.replace(" ", "_"))
    os.makedirs(case_dir, exist_ok=True)
    filename = os.path.join(case_dir, f"Investment_vs_Cumulative_20yr_{case_name.replace(' ', '_')}.png")
    plt.savefig(filename, dpi=300)
    plt.close()
    print(f"✅ Saved Investment vs Cumulative Savings plot for {case_name}")

def grid_import_difference_bar_plot(df, case_name):
    df = df.sort_values("Battery_kW")

    # Compute Grid Import Difference if column missing
    if "Grid import difference from the base case scenario" not in df.columns:
        if 0 in df["Battery_kW"].values:
            base_import = df.loc[df["Battery_kW"] == 0, "Annual Grid Import"].values[0]
            df["Grid_import_diff"] = df["Annual Grid Import"] - base_import
            print(f"ℹ️ Calculated Grid Import Difference from 0 kW base for {case_name}")
        else:
            print(f"⚠️ No 0 kW base scenario found for {case_name}, skipping Grid Import Difference plot.")
            return
    else:
        df["Grid_import_diff"] = pd.to_numeric(df["Grid import difference from the base case scenario"], errors="coerce")
    
    battery_sizes = df["Battery_kW"].tolist()
    grid_diff = df["Grid_import_diff"].tolist()
    
    x = np.arange(len(battery_sizes))
    width = 0.6

    plt.figure(figsize=(FIG_WIDTH, FIG_HEIGHT))
    plt.bar(x, grid_diff, width=width, color=sns.color_palette("Set2", len(grid_diff))[0])
    
    for i in range(len(x)):
        plt.text(x[i], grid_diff[i] + max(grid_diff)*0.02, f"{grid_diff[i]:,.0f}", ha="center", va="bottom", fontsize=9)
    
    plt.xticks(x, [f"{int(b)} kW" if b > 0 else "NoBatt" for b in battery_sizes])
    plt.xlabel("Battery Size", fontsize=14)
    plt.ylabel("Grid Import Difference (kWh)", fontsize=14)
    plt.title(f"{case_name}: Grid Import Difference vs Battery Size", fontsize=18, fontweight="bold", pad=20)
    plt.grid(axis="y", linestyle="--", alpha=0.6)
    plt.tight_layout()
    
    case_dir = os.path.join(output_dir, case_name.replace(" ", "_"))
    os.makedirs(case_dir, exist_ok=True)
    filename = os.path.join(case_dir, f"Grid_Import_Difference_{case_name.replace(' ', '_')}.png")
    plt.savefig(filename, dpi=300)
    plt.close()
    print(f"✅ Saved Grid Import Difference plot for {case_name}")


# --- Generate Plots ---
print("Generating all inter-scenario plots...")

for sheet, df in data.items():
    print(f"\nProcessing sheet: {sheet}")
    print("Columns available:", df.columns.tolist())
    
    if {"Cost Difference from base scenario", "Investment cost", "Battery_kW"}.issubset(df.columns):
        investment_vs_cumulative_bar_plot(df, sheet)
    else:
        print(f"⚠️ Required financial columns missing for {sheet}, skipping Investment vs Cumulative Savings plot.")
    
    grid_import_difference_bar_plot(df, sheet)

print(f"\n✅ All applicable plots generated successfully in '{output_dir}' folder.")
