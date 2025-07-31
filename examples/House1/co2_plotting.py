import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# --- Paths ---
script_dir = os.path.dirname(os.path.abspath(__file__))
input_dir = os.path.join(script_dir, "output", "carbon_footprint_analysis_csv")
output_dir = os.path.join(script_dir, "output", "carbon_footprint_analysis_plots")
os.makedirs(output_dir, exist_ok=True)

# --- Read CSVs ---
manufacturing_df = pd.read_csv(os.path.join(input_dir, "battery_co2_manufacturing_vs_usage.csv"))
total_co2_df = pd.read_csv(os.path.join(input_dir, "annual_total_operational_co2_all_scenarios.csv"), index_col=0)
monthly_pv_df = pd.read_csv(os.path.join(input_dir, "monthly_co2_pv_all_scenarios_wide.csv"), index_col=0)
monthly_grid_df = pd.read_csv(os.path.join(input_dir, "monthly_co2_grid_all_scenarios_wide.csv"), index_col=0)

# --- Breakeven Calculations ---
df = manufacturing_df[manufacturing_df["CO2 from Battery Manufacturing (gCO2eq)"] > 0].copy()
df["Operational Breakeven Time (hours)"] = ( # Changed column name to hours
    df["CO2 from Battery Manufacturing (gCO2eq)"] / df["CO2 from Battery Discharge (gCO2eq)"] * 365 * 20 * 24 # Multiplied by 20 and 24 (for hours)
)
df["Energy Breakeven (kWh)"] = df["CO2 from Battery Manufacturing (gCO2eq)"] / 53  # gCO2eq/kWh for discharge

# --- Annotate function ---
def annotate_bars(ax, fmt="{:.0f}", offset_factor=0.02, rotation=90, fontsize=9):
    """Annotates bars with their height values."""
    for bar in ax.patches:
        height = bar.get_height()
        if height > 0:
            # Calculate offset dynamically based on plot height
            offset = ax.get_ylim()[1] * offset_factor
            ax.annotate(fmt.format(height),
                        (bar.get_x() + bar.get_width() / 2, height + offset),
                        ha='center', va='bottom', fontsize=fontsize, rotation=rotation)

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

# --- Bar Plot: Battery Manufacturing vs Operational (in kgCO2eq/kWh) ---
fig, ax = plt.subplots(figsize=(16, 8)) # Increased figure width
x = df["Scenario"]
x_pos = range(len(x))
width = 0.35

ax.bar([i - width / 2 for i in x_pos],
       df["CO2 from Battery Manufacturing (gCO2eq)"] / 1000,
       width, label='Manufacturing CO₂') # Improved label

ax.bar([i + width / 2 for i in x_pos],
       df["CO2 from Battery Discharge (gCO2eq)"] / 1000,
       width, label='Operational CO₂') # Improved label

ax.set_ylabel("CO₂ Emissions (kgCO₂eq/kWh)") # More descriptive label
ax.set_title("Battery Manufacturing vs Operational CO₂ Emissions per Scenario") # More descriptive title
ax.set_xticks(x_pos)
ax.set_xticklabels(x, rotation=45)
ax.legend(loc='upper left', bbox_to_anchor=(1, 1)) # Move legend outside to prevent overlap
annotate_bars(ax, fmt="{:.0f}", offset_factor=0.01, rotation=0, fontsize=10) # Adjust annotation for clarity
plt.tight_layout(rect=[0, 0, 0.85, 1]) # Adjust layout to make space for legend
plt.savefig(os.path.join(output_dir, "battery_manufacturing_vs_operational_bar.png"))
plt.close(fig) # Close figure to free memory

# --- Bar Plot: Total CO₂ Output ---
fig, ax = plt.subplots(figsize=(16, 8)) # Increased figure width
total = total_co2_df.sum(axis=0) / 1000  # Convert to kgCO2eq
ax.bar(total.index, total.values, color=sns.color_palette("viridis", len(total))) # Add color palette
ax.set_ylabel("Total CO₂ Emissions (kgCO₂eq)")
ax.set_title("Total Annual CO₂ Emissions Across All Scenarios")
ax.set_xticklabels(total.index, rotation=45)
annotate_bars(ax, offset_factor=0.01, rotation=0, fontsize=10)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "total_yearly_co2_bar.png"))
plt.close(fig)

# --- Bar Plot: Operational Breakeven Time (in hours) ---
fig, ax = plt.subplots(figsize=(14, 7)) # Increased figure width
bar = ax.bar(df["Scenario"], df["Operational Breakeven Time (hours)"], color=sns.color_palette("magma", len(df["Scenario"]))) # Changed column name
ax.set_title("Operational CO₂ Breakeven Time (Hours)") # Changed title
ax.set_ylabel("Breakeven Time (Hours)") # Changed label
ax.tick_params(axis='x', rotation=45)
annotate_bars(ax, fmt="{:.0f}", offset_factor=0.01, rotation=0, fontsize=10)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "operational_breakeven_time_bar.png"))
plt.close(fig)

# --- Bar Plot: Energy Breakeven ---
fig, ax = plt.subplots(figsize=(14, 7)) # Increased figure width
bar = ax.bar(df["Scenario"], df["Energy Breakeven (kWh)"], color=sns.color_palette("plasma", len(df["Scenario"])))
ax.set_title("Energy Breakeven Point vs Battery CO₂ Emissions")
ax.set_ylabel("Energy (kWh)")
ax.tick_params(axis='x', rotation=45)
annotate_bars(ax, fmt="{:.0f}", offset_factor=0.01, rotation=0, fontsize=10)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "energy_breakeven_bar.png"))
plt.close(fig)

# --- Line Plot: Monthly PV CO₂ ---
fig, ax = plt.subplots(figsize=(16, 8)) # Increased figure width
for col in monthly_pv_df.columns:
    ax.plot(monthly_pv_df.index, monthly_pv_df[col], label=col, linewidth=2) # Changed to plot
ax.set_title("Monthly CO₂ Emissions from PV Production")
ax.set_ylabel("CO₂ Emissions (gCO₂eq)")
ax.set_xlabel("Month")
ax.set_xticks(monthly_pv_df.index) # Ensure all months are shown
ax.set_xticklabels(monthly_pv_df.index.map(str), rotation=45)
ax.legend(ncol=2, bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0.) # Adjust legend position
plt.tight_layout(rect=[0, 0, 0.85, 1]) # Adjust layout to make space for legend
plt.savefig(os.path.join(output_dir, "monthly_pv_co2_line_plot.png")) # Changed filename
plt.close(fig)

# --- Line Plot: Monthly Grid CO₂ ---
fig, ax = plt.subplots(figsize=(16, 8)) # Increased figure width
for col in monthly_grid_df.columns:
    ax.plot(monthly_grid_df.index, monthly_grid_df[col], label=col, linewidth=2) # Changed to plot
ax.set_title("Monthly CO₂ Emissions from Grid Import")
ax.set_ylabel("CO₂ Emissions (gCO₂eq)")
ax.set_xlabel("Month")
ax.set_xticks(monthly_grid_df.index) # Ensure all months are shown
ax.set_xticklabels(monthly_grid_df.index.map(str), rotation=45)
ax.legend(ncol=2, bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0.) # Adjust legend position
plt.tight_layout(rect=[0, 0, 0.85, 1]) # Adjust layout to make space for legend
plt.savefig(os.path.join(output_dir, "monthly_grid_co2_line_plot.png")) # Changed filename
plt.close(fig)

# --- Annual CO2 Impact: PV ---
fig, ax = plt.subplots(figsize=(14, 7)) # Increased figure width
annual_pv_co2 = monthly_pv_df.sum() / 1000  # to kgCO2eq
ax.bar(annual_pv_co2.index, annual_pv_co2.values, color=sns.color_palette("Greens_d", len(annual_pv_co2)))
ax.set_title("Annual CO₂ Impact from PV Production")
ax.set_ylabel("Annual CO₂ Emissions (kgCO₂eq)")
ax.set_xticklabels(annual_pv_co2.index, rotation=45)
annotate_bars(ax, offset_factor=0.01, rotation=0, fontsize=10)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "annual_co2_pv_bar.png"))
plt.close(fig)

# --- Annual CO2 Impact: Grid ---
fig, ax = plt.subplots(figsize=(14, 7)) # Increased figure width
annual_grid_co2 = monthly_grid_df.sum() / 1000  # to kgCO2eq
ax.bar(annual_grid_co2.index, annual_grid_co2.values, color=sns.color_palette("Blues_d", len(annual_grid_co2)))
ax.set_title("Annual CO₂ Impact from Grid Import")
ax.set_ylabel("Annual CO₂ Emissions (kgCO₂eq)")
ax.set_xticklabels(annual_grid_co2.index, rotation=45)
annotate_bars(ax, offset_factor=0.01, rotation=0, fontsize=10)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "annual_co2_grid_bar.png"))
plt.close(fig)
