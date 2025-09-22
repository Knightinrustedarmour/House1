import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.ticker as mtick

# --- Configuration ---
# Use a high-DPI for cleaner, sharper plots
DPI_VALUE = 300
# Set a clean seaborn style for better aesthetics
sns.set_style("whitegrid")
plt.rcParams['font.size'] = 10 # Set a base font size

# --- Directories ---
script_dir = os.path.dirname(os.path.abspath(__file__))
input_file = os.path.join(script_dir, "output", "monthly_energy_flows", "monthly_energy_flows_master_table.csv")
output_dir = os.path.join(script_dir, "output", "monthly_plots")
os.makedirs(output_dir, exist_ok=True)

# --- Load Data ---
df = pd.read_csv(input_file)

# --- Helper: Aggregate annual totals ---
annual = df.groupby("Scenario").sum(numeric_only=True).reset_index()

# --- Helper: Annotate bars with cleaner labels ---
def annotate_bars(ax, fmt="{:.0f}"):
    for p in ax.patches:
        height = p.get_height()
        if not pd.isna(height) and height > 0:
            if height >= 1000:
                label = f"{height/1000:.1f}k"
            else:
                label = fmt.format(height)
            ax.annotate(label,
                        (p.get_x() + p.get_width() / 2., height),
                        ha="center", va="bottom", fontsize=8, rotation=90,
                        xytext=(0, 5), textcoords="offset points")

# --- Helper: Order scenarios for consistent plotting ---
def order_scenarios(df_to_plot):
    scenario_order = sorted(df_to_plot["Scenario"].unique(), 
                            key=lambda x: int(''.join(filter(str.isdigit, x))) if 'kWh' in x else 0)
    return df_to_plot.set_index("Scenario").reindex(scenario_order).reset_index()

# ------------------ 1. Grid Import vs Export per Scenario ------------------
ordered_annual = order_scenarios(annual)
fig, ax = plt.subplots(figsize=(10, 6))
width = 0.35
scenarios = ordered_annual["Scenario"]
x = range(len(scenarios))

p1 = ax.bar([i - width/2 for i in x], ordered_annual["Grid_Import"], width, label="Grid Import", color="#3498db")
p2 = ax.bar([i + width/2 for i in x], ordered_annual["Grid_Export_to_Grid"], width, label="Grid Export", color="#2ecc71")
annotate_bars(ax)

ax.set_xticks(list(x))
ax.set_xticklabels(scenarios, rotation=45)
ax.set_ylabel("Energy [kWh]", fontsize=12)
ax.set_title("Annual Grid Import vs. Grid Export per Scenario", fontsize=14)
ax.legend()
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "1_grid_import_vs_export.png"), dpi=DPI_VALUE)
plt.close()


# ------------------ 2. Monthly Profiles per Flow (choose 1 scenario) ------------------
for scenario_choice in df["Scenario"].unique():
    df_scenario = df[df["Scenario"] == scenario_choice]

    plt.figure(figsize=(12, 6))
    for flow in ["Total_PV_Production", "Demand_Consumption", 
                 "Grid_Import", "Grid_Export_to_Grid", 
                 "Battery_Charge", "Battery_Discharge"]:
        if flow in df_scenario.columns:
            plt.plot(df_scenario["Month"], df_scenario[flow], marker="o", label=flow, linewidth=2)

    plt.ylabel("Energy [kWh]", fontsize=12)
    plt.title(f"Monthly Profiles for Scenario: {scenario_choice}", fontsize=14)
    plt.legend()
    plt.tight_layout()

    filename = f"2_monthly_profiles_{scenario_choice}.png".replace("/", "_")
    plt.savefig(os.path.join(output_dir, filename), dpi=DPI_VALUE)
    plt.close()

print("✅ Monthly profile plots generated for all scenarios")
print("-------------------------------------------------------")


# ------------------ 4. Scenario Comparison for Total Annual Values ------------------
flows_of_interest = ["Grid_Import", "Grid_Export_to_Grid", "Total_PV_Production", "Demand_Consumption"]
ordered_annual = order_scenarios(annual)
annual_plot = ordered_annual.set_index("Scenario")[flows_of_interest]

ax = annual_plot.plot(kind="bar", figsize=(12, 6))
plt.ylabel("Energy [kWh]", fontsize=12)
plt.title("Annual Totals by Scenario", fontsize=14)
annotate_bars(ax)
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "4_scenario_comparison.png"), dpi=DPI_VALUE)
plt.close()

print("-------------------------------------------------------")


# ------------------ 6. PV Utilisation (Direct vs Feed-in) ------------------
ordered_annual = order_scenarios(annual)
pv_util = ordered_annual[["Scenario", "PV_Direct_Consumption", "PV_to_Grid_Feedin"]].set_index("Scenario")

ax = pv_util.plot(kind="bar", stacked=True, figsize=(12, 6), colormap="viridis")
plt.ylabel("Energy [kWh]", fontsize=12)
plt.title("PV Utilisation: Direct Consumption vs. Grid Feed-in", fontsize=14)
annotate_bars(ax)
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "6_pv_utilisation.png"), dpi=DPI_VALUE)
plt.close()

print("-------------------------------------------------------")


# ------------------ 7. Grid Dependency Ratio ------------------
ordered_annual = order_scenarios(annual)
grid_dep = ordered_annual[["Scenario", "Grid_Import", "Demand_Consumption"]].copy()
grid_dep["Grid_Share_%"] = 100 * grid_dep["Grid_Import"] / grid_dep["Demand_Consumption"]

fig, ax = plt.subplots(figsize=(10, 6))
sns.barplot(x="Scenario", y="Grid_Share_%", data=grid_dep, ax=ax, palette="plasma")
ax.set_ylabel("Grid Dependency [% of Demand]", fontsize=12)
ax.set_title("Grid Dependency Ratio per Scenario", fontsize=14)
ax.yaxis.set_major_formatter(mtick.PercentFormatter())
ax.set_xlabel("Scenario", fontsize=12)
ax.set_xticklabels(grid_dep["Scenario"], rotation=45)

for p in ax.patches:
    height = p.get_height()
    ax.annotate(f"{height:.1f}%",
                (p.get_x() + p.get_width() / 2., height),
                ha="center", va="bottom", fontsize=8,
                xytext=(0, 5), textcoords="offset points")

plt.tight_layout()
plt.savefig(os.path.join(output_dir, "7_grid_dependency_ratio.png"), dpi=DPI_VALUE)
plt.close()

print(f"✅ All plots with improved aesthetics and annotations saved in: {output_dir}")