import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# --- Paths ---
script_dir = os.path.dirname(os.path.abspath(__file__))
input_dir = os.path.join(script_dir, "output", "co2_footprint_analysis_csv")
output_dir = os.path.join(script_dir, "output", "co2_footprint_analysis_plots")
os.makedirs(output_dir, exist_ok=True)

# --- Read CSVs ---
try:
    total_co2_df = pd.read_csv(os.path.join(input_dir, "annual_total_operational_co2_all_scenarios.csv"), index_col=0)
    manufacturing_df = pd.read_csv(os.path.join(input_dir, "battery_co2_manufacturing_vs_usage.csv"))
    monthly_pv_df = pd.read_csv(os.path.join(input_dir, "monthly_co2_pv_all_scenarios_wide.csv"), index_col=0)
    monthly_grid_df = pd.read_csv(os.path.join(input_dir, "monthly_co2_grid_all_scenarios_wide.csv"), index_col=0)
except FileNotFoundError as e:
    print(f"Error: One of the required CSV files was not found. Please ensure the path is correct. {e}")
    exit()

# --- Breakeven Calculations ---
df = manufacturing_df[manufacturing_df["CO2 from Battery Manufacturing (gCO2eq)"] > 0].copy()
df["Operational Breakeven Time (years)"] = (
    df["CO2 from Battery Manufacturing (gCO2eq)"] / df["CO2 from Battery Discharge (gCO2eq)"] * 20
)
df["Operational Breakeven Time (hours)"] = df["Operational Breakeven Time (years)"] * 8766
df["Energy Breakeven (kWh)"] = df["CO2 from Battery Manufacturing (gCO2eq)"] / 53 * 20

# --- Plotting Helpers ---
def annotate_bars(ax, fmt="{:.0f}", offset_factor=0.02, rotation=90, fontsize=9):
    """Annotates bars with their height values."""
    for bar in ax.patches:
        height = bar.get_height()
        if height > 0:
            offset = ax.get_ylim()[1] * offset_factor
            ax.annotate(fmt.format(height),
                        (bar.get_x() + bar.get_width() / 2, height + offset),
                        ha='center', va='bottom', fontsize=fontsize, rotation=rotation)

def order_dataframe_for_plotting(df):
    """Orders a DataFrame based on the user's requested scenario order."""
    # Updated order to match the new scenarios
    order = ["NoBattery", "5kWh", "8kWh", "12kWh", "15kWh", "20kWh", "26kWh", "50kWh"]
    # Reindex the DataFrame to ensure the correct order, filling missing values if necessary
    return df.reindex(order)

# --- Set a consistent plot style for better aesthetics ---
sns.set_theme(style="whitegrid", palette="viridis")
plt.rcParams.update({
    'font.size': 12,
    'axes.titlesize': 16,
    'axes.labelsize': 14,
    'xtick.labelsize': 12,
    'ytick.labelsize': 12,
    'legend.fontsize': 12,
    'figure.titlesize': 18
})

# --- Consolidated Plots with Ordering ---

# --- Bar Plot: Total CO2 Output (with ordering) ---
fig, ax = plt.subplots(figsize=(16, 8))
total_co2_operational = total_co2_df.iloc[0] / 1000  # Get the single row and convert to kgCO2eq
total_co2_operational = order_dataframe_for_plotting(total_co2_operational)
ax.bar(total_co2_operational.index, total_co2_operational.values, color=sns.color_palette("viridis", len(total_co2_operational)))
ax.set_ylabel("Total Operational CO2 (kgCO2eq)")
ax.set_title("Total Annual Operational CO2 Across All Scenarios")
ax.set_xticklabels(total_co2_operational.index, rotation=45, ha='right')
annotate_bars(ax, offset_factor=0.01, rotation=0, fontsize=10)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "total_yearly_co2_bar.png"))
plt.close(fig)

# --- Bar Plot: Battery Manufacturing vs Operational (in kgCO2eq/kWh) ---
fig, ax = plt.subplots(figsize=(16, 8))
df = order_dataframe_for_plotting(df.set_index("Scenario")).reset_index()
x = df["Scenario"]
x_pos = range(len(x))
width = 0.35
ax.bar([i - width / 2 for i in x_pos],
       df["CO2 from Battery Manufacturing (gCO2eq)"] / 1000,
       width, label='Manufacturing CO2')
ax.bar([i + width / 2 for i in x_pos],
       df["CO2 from Battery Discharge (gCO2eq)"] / 1000,
       width, label='Operational CO2')
ax.set_ylabel("CO2 Emissions (kgCO2eq)")
ax.set_title("Battery Manufacturing vs Operational CO2 Emissions per Scenario")
ax.set_xticks(x_pos)
ax.set_xticklabels(x, rotation=45, ha='right')
ax.legend(loc='upper left', bbox_to_anchor=(1, 1))
annotate_bars(ax, fmt="{:.0f}", offset_factor=0.01, rotation=0, fontsize=10)
plt.tight_layout(rect=[0, 0, 0.85, 1])
plt.savefig(os.path.join(output_dir, "battery_manufacturing_vs_operational_bar.png"))
plt.close(fig)

# --- Bar Plot: Operational Breakeven Time (in years) ---
fig, ax = plt.subplots(figsize=(14, 7))
df_ordered = order_dataframe_for_plotting(df.set_index("Scenario"))
bar = ax.bar(df_ordered.index, df_ordered["Operational Breakeven Time (years)"], color=sns.color_palette("magma", len(df_ordered)))
ax.set_title("Operational CO2 Breakeven Time (Years)")
ax.set_ylabel("Breakeven Time (Years)")
ax.tick_params(axis='x', rotation=45)
annotate_bars(ax, fmt="{:.1f}", offset_factor=0.01, rotation=0, fontsize=10)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "operational_breakeven_time_bar_years.png"))
plt.close(fig)

# --- Bar Plot: Energy Breakeven ---
fig, ax = plt.subplots(figsize=(14, 7))
df_ordered = order_dataframe_for_plotting(df.set_index("Scenario"))
bar = ax.bar(df_ordered.index, df_ordered["Energy Breakeven (kWh)"], color=sns.color_palette("plasma", len(df_ordered)))
ax.set_title("Energy Breakeven Point vs Battery CO2 Emissions")
ax.set_ylabel("Energy (kWh)")
ax.tick_params(axis='x', rotation=45)
annotate_bars(ax, fmt="{:.0f}", offset_factor=0.01, rotation=0, fontsize=10)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "energy_breakeven_bar.png"))
plt.close(fig)

# --- Line Plot: Monthly PV CO2 ---
fig, ax = plt.subplots(figsize=(16, 8))
monthly_pv_df_ordered = order_dataframe_for_plotting(monthly_pv_df.T).T
for col in monthly_pv_df_ordered.columns:
    ax.plot(monthly_pv_df_ordered.index, monthly_pv_df_ordered[col], label=col, linewidth=2)
ax.set_title("Monthly CO2 Emissions from PV Production")
ax.set_ylabel("CO2 Emissions (gCO2eq)")
ax.set_xlabel("Month")
ax.set_xticks(monthly_pv_df_ordered.index)
ax.set_xticklabels(monthly_pv_df_ordered.index.map(str), rotation=45)
ax.legend(ncol=2, bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0.)
plt.tight_layout(rect=[0, 0, 0.85, 1])
plt.savefig(os.path.join(output_dir, "monthly_pv_co2_line_plot.png"))
plt.close(fig)

# --- Line Plot: Monthly Grid CO2 ---
fig, ax = plt.subplots(figsize=(16, 8))
monthly_grid_df_ordered = order_dataframe_for_plotting(monthly_grid_df.T).T
for col in monthly_grid_df_ordered.columns:
    ax.plot(monthly_grid_df_ordered.index, monthly_grid_df_ordered[col], label=col, linewidth=2)
ax.set_title("Monthly CO2 Emissions from Grid Import")
ax.set_ylabel("CO2 Emissions (gCO2eq)")
ax.set_xlabel("Month")
ax.set_xticks(monthly_grid_df_ordered.index)
ax.set_xticklabels(monthly_grid_df_ordered.index.map(str), rotation=45)
ax.legend(ncol=2, bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0.)
plt.tight_layout(rect=[0, 0, 0.85, 1])
plt.savefig(os.path.join(output_dir, "monthly_grid_co2_line_plot.png"))
plt.close(fig)

# --- Annual CO2 Impact: PV (with ordering) ---
fig, ax = plt.subplots(figsize=(14, 7))
annual_pv_co2 = monthly_pv_df.sum() / 1000
annual_pv_co2 = order_dataframe_for_plotting(annual_pv_co2)
ax.bar(annual_pv_co2.index, annual_pv_co2.values, color=sns.color_palette("Greens_d", len(annual_pv_co2)))
ax.set_title("Annual CO2 Impact from PV Production")
ax.set_ylabel("Annual CO2 Emissions (kgCO2eq)")
ax.set_xticklabels(annual_pv_co2.index, rotation=45, ha='right')
annotate_bars(ax, offset_factor=0.01, rotation=0, fontsize=10)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "annual_co2_pv_bar.png"))
plt.close(fig)

# --- Annual CO2 Impact: Grid (with ordering) ---
fig, ax = plt.subplots(figsize=(14, 7))
annual_grid_co2 = monthly_grid_df.sum() / 1000
annual_grid_co2 = order_dataframe_for_plotting(annual_grid_co2)
ax.bar(annual_grid_co2.index, annual_grid_co2.values, color=sns.color_palette("Blues_d", len(annual_grid_co2)))
ax.set_title("Annual CO2 Impact from Grid Import")
ax.set_ylabel("Annual CO2 Emissions (kgCO2eq)")
ax.set_xticklabels(annual_grid_co2.index, rotation=45, ha='right')
annotate_bars(ax, offset_factor=0.01, rotation=0, fontsize=10)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "annual_co2_grid_bar.png"))
plt.close(fig)

# --- Carbon Offset Plot ---
fig, ax = plt.subplots(figsize=(16, 8))
total_co2_operational = total_co2_df.iloc[0] / 1000
total_co2_operational = order_dataframe_for_plotting(total_co2_operational)
baseline_emissions = total_co2_operational.loc["NoBattery"]
carbon_offset = (baseline_emissions - total_co2_operational)
scenarios_to_color = [s for s in carbon_offset.index if s != "NoBattery"]
num_colors = len(scenarios_to_color)
palette = sns.color_palette("viridis", num_colors)
color_map = {scenario: palette[i] for i, scenario in enumerate(scenarios_to_color)}
color_map["NoBattery"] = 'lightgray'
bar_colors = [color_map[s] for s in carbon_offset.index]
ax.bar(carbon_offset.index, carbon_offset.values, color=bar_colors)
ax.set_ylabel("Carbon Offset (kgCO2eq)")
ax.set_title("Annual Carbon Offset Compared to 'NoBattery' Baseline")
ax.set_xticklabels(carbon_offset.index, rotation=45, ha='right')
ax.axhline(0, color='black', linewidth=0.8, linestyle='--')
annotate_bars(ax, fmt="{:,.0f}", offset_factor=0.01, rotation=0, fontsize=10)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "annual_carbon_offset_bar.png"))
plt.close(fig)