

import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# --- Paths ---
script_dir = os.path.dirname(os.path.abspath(__file__))
input_dir = os.path.join(script_dir, "output", "co2_footprint_analysis_csv")
output_dir = os.path.join(script_dir, "output", "co2_footprint_analysis_plots")
os.makedirs(output_dir, exist_ok=True)

# --- Read Input CSVs ---
gco2eq_path = os.path.join(input_dir, "annual_co2_all_scenarios_gCO2eq.csv")
kgco2eq_path = os.path.join(input_dir, "annual_co2_all_scenarios_kgCO2eq.csv")

df_g = pd.read_csv(gco2eq_path, index_col=0)
df_kg = pd.read_csv(kgco2eq_path, index_col=0)

# --- Helper Functions ---
def annotate_bars(ax, fmt="{:.0f}", offset_factor=0.01, rotation=0, fontsize=11):
    """Annotate bar heights with values."""
    for bar in ax.patches:
        height = bar.get_height()
        if height > 0:
            offset = ax.get_ylim()[1] * offset_factor
            ax.annotate(fmt.format(height),
                        (bar.get_x() + bar.get_width() / 2, height + offset),
                        ha='center', va='bottom', fontsize=fontsize, rotation=rotation)

def order_dataframe_for_plotting(df):
    """Ensure consistent scenario order."""
    order = ["PV_NoBattery", "5kWh", "8kWh", "12kWh", "15kWh", "20kWh", "26kWh", "50kWh"]
    return df.reindex(order)

def save_figure(fig, name):
    """Save figure in 21:9 aspect ratio and high DPI."""
    path = os.path.join(output_dir, f"{name}.png")
    fig.savefig(path, bbox_inches="tight", dpi=300)
    plt.close(fig)
    print(f"📊 Saved: {path}")

# --- Plot Config ---
sns.set_theme(style="whitegrid", palette="viridis")
plt.rcParams.update({
    'font.size': 13,
    'axes.titlesize': 18,
    'axes.labelsize': 15,
    'xtick.labelsize': 13,
    'ytick.labelsize': 13,
    'legend.fontsize': 13,
    'figure.titlesize': 20
})

# Use 21:9 ratio → cinematic plots
FIGSIZE = (21, 9)

# --- Data Ordering ---
df_g = order_dataframe_for_plotting(df_g)
df_kg = order_dataframe_for_plotting(df_kg)

# --- Plot 1: Total Annual CO2 ---
fig, ax = plt.subplots(figsize=FIGSIZE)
ax.bar(df_kg.index, df_kg["Total Yearly CO2 Emissions (kgCO2eq)"],
       color=sns.color_palette("viridis", len(df_kg)))
ax.set_title("Total Annual CO2 Emissions per Scenario")
ax.set_ylabel("CO2 Emissions (kgCO2eq)")
ax.tick_params(axis='x', rotation=30)
annotate_bars(ax, fmt="{:,.0f}", offset_factor=0.008)
plt.tight_layout()
save_figure(fig, "total_annual_co2_bar")

# --- Plot 2: CO2 Breakdown (Stacked) ---
fig, ax = plt.subplots(figsize=FIGSIZE)
df_stacked = df_kg[[
    "Yearly CO2 from PV Manufacturing (kgCO2eq)",
    "Yearly CO2 from Battery Manufacturing (kgCO2eq)",
    "Yearly CO2 from Grid Import (kgCO2eq)"
]]
df_stacked.plot(kind="bar", stacked=True, ax=ax,
                color=["#2ca02c", "#ff7f0e", "#1f77b4"], edgecolor="black")

ax.set_title("CO2 Emission Breakdown by Source (kgCO2eq)")
ax.set_ylabel("Total CO2 Emissions (kgCO2eq)")
ax.legend(title="Source", loc="upper right", frameon=True)
ax.tick_params(axis="x", rotation=30)
plt.tight_layout()
save_figure(fig, "co2_breakdown_stacked_bar")

# --- Plot 3: PV vs Battery Manufacturing ---
fig, ax = plt.subplots(figsize=FIGSIZE)
width = 0.35
x = range(len(df_kg))
ax.bar([i - width / 2 for i in x],
       df_kg["Yearly CO2 from PV Manufacturing (kgCO2eq)"],
       width, label="PV Manufacturing", color="#2ca02c", edgecolor="black")
ax.bar([i + width / 2 for i in x],
       df_kg["Yearly CO2 from Battery Manufacturing (kgCO2eq)"],
       width, label="Battery Manufacturing", color="#ff7f0e", edgecolor="black")
ax.set_title("PV vs Battery Manufacturing CO2 Emissions")
ax.set_ylabel("CO2 Emissions (kgCO2eq)")
ax.set_xticks(x)
ax.set_xticklabels(df_kg.index, rotation=30, ha="right")
ax.legend(loc="upper right", frameon=True)
annotate_bars(ax, fmt="{:,.0f}", offset_factor=0.008)
plt.tight_layout()
save_figure(fig, "pv_vs_battery_manufacturing_bar")

# --- Plot 4: Grid Import CO2 ---
fig, ax = plt.subplots(figsize=FIGSIZE)
ax.bar(df_kg.index, df_kg["Yearly CO2 from Grid Import (kgCO2eq)"],
       color=sns.color_palette("Blues", len(df_kg)), edgecolor="black")
ax.set_title("CO2 Emissions from Grid Import per Scenario")
ax.set_ylabel("CO2 Emissions (kgCO2eq)")
ax.tick_params(axis="x", rotation=30)
annotate_bars(ax, fmt="{:,.0f}", offset_factor=0.008)
plt.tight_layout()
save_figure(fig, "grid_import_co2_bar")

# --- Plot 5: CO2 Reduction vs PV_NoBattery ---
baseline = df_kg.loc["PV_NoBattery", "Total Yearly CO2 Emissions (kgCO2eq)"]
df_kg["CO2 Reduction (kgCO2eq)"] = baseline - df_kg["Total Yearly CO2 Emissions (kgCO2eq)"]

fig, ax = plt.subplots(figsize=FIGSIZE)
colors = sns.color_palette("coolwarm", len(df_kg))
ax.bar(df_kg.index, df_kg["CO2 Reduction (kgCO2eq)"], color=colors, edgecolor="black")
ax.axhline(0, color="black", linestyle="--", linewidth=1)
ax.set_title("CO2 Reduction Compared to PV_NoBattery Baseline")
ax.set_ylabel("CO2 Reduction (kgCO2eq)")
ax.tick_params(axis="x", rotation=30)
annotate_bars(ax, fmt="{:,.0f}", offset_factor=0.008)
plt.tight_layout()
save_figure(fig, "co2_reduction_vs_baseline_bar")

# --- Summary ---
print("\n✅ All CO2 analysis plots generated successfully!")
print(f"Files saved in: {output_dir}")
