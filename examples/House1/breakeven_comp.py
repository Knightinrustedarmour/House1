import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# --- Paths ---
script_dir = os.path.dirname(os.path.abspath(__file__))
input_dir = os.path.join(script_dir, "output", "co2_footprint_analysis_csv")
output_dir = os.path.join(script_dir, "output", "breakeven_plots")
os.makedirs(output_dir, exist_ok=True)

# --- Read CSVs ---
manufacturing_df = pd.read_csv(os.path.join(input_dir, "battery_co2_manufacturing_vs_usage.csv"))
cost_breakeven_file_path = os.path.join(script_dir, "output", "breakeven_plots", "breakeven_periods.csv")
cost_breakeven_df = pd.read_csv(cost_breakeven_file_path)

# --- Breakeven Calculations (Using your provided logic) ---
df = manufacturing_df[manufacturing_df["CO2 from Battery Manufacturing (gCO2eq)"] > 0].copy()
df = pd.merge(df, cost_breakeven_df, on="Scenario")

# Calculate Operational Breakeven Time (in years) based on your formula
df["Carbon Breakeven Time (years)"] = (
    df["CO2 from Battery Manufacturing (gCO2eq)"] / df["CO2 from Battery Discharge (gCO2eq)"] * 20
)

# Add the new calculations from your snippet
df["Operational Breakeven Time (hours)"] = df["Carbon Breakeven Time (years)"] * 8766
df["Energy Breakeven (kWh)"] = df["CO2 from Battery Manufacturing (gCO2eq)"] / 53 * 20


# --- Plotting Helpers ---
def annotate_bars(ax, fmt="{:.2f}", offset_factor=0.02, rotation=90, fontsize=9):
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
    order = ["NoPV", "PV_NoBattery", "5kWh", "8kWh", "12kWh", "15kWh", "20kWh", "26kWh", "50kWh"]
    # Reindex the DataFrame to ensure the correct order, filling missing values if necessary
    return df.reindex(order)

def plot_double_bar_chart(df, y1_col, y2_col, y1_label, y2_label, title, y_label, output_path):
    """
    Creates a double bar chart for comparing two metrics per scenario.
    """
    fig, ax = plt.subplots(figsize=(14, 7))
    scenarios = df["Scenario"]
    x = np.arange(len(scenarios))
    width = 0.35

    bar1 = ax.bar(x - width/2, df[y1_col], width, label=y1_label, color=sns.color_palette("magma")[0])
    bar2 = ax.bar(x + width/2, df[y2_col], width, label=y2_label, color=sns.color_palette("viridis")[0])

    ax.set_ylabel(y_label)
    ax.set_title(title)
    ax.set_xticks(x)
    ax.set_xticklabels(scenarios, rotation=45, ha='right')
    ax.legend()

    # Annotate bars for both sets
    annotate_bars(ax, fmt="{:.2f}", offset_factor=0.01, rotation=0, fontsize=10)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close(fig)

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

# --- Plot all three breakeven comparisons ---

# Carbon vs. Cost Breakeven Time
plot_double_bar_chart(
    df=df,
    y1_col="Carbon Breakeven Time (years)",
    y2_col="Breakeven_With_Setup_Years",
    y1_label="Carbon Breakeven Time (years)",
    y2_label="Cost breakeven (years)",
    title="Carbon vs. Cost Breakeven Time",
    y_label="Breakeven Time (Years)",
    output_path=os.path.join(output_dir, "carbon_vs_cost_breakeven_bar.png")
)

# Carbon Breakeven Time (Hours)
fig, ax = plt.subplots(figsize=(14, 7))
df_ordered = order_dataframe_for_plotting(df.set_index("Scenario"))
bar = ax.bar(df_ordered.index, df_ordered["Operational Breakeven Time (hours)"], color=sns.color_palette("magma", len(df_ordered)))
ax.set_title("Operational CO2 Breakeven Time (Hours)")
ax.set_ylabel("Breakeven Time (Hours)")
ax.tick_params(axis='x', rotation=45)
annotate_bars(ax, fmt="{:,.0f}", offset_factor=0.01, rotation=0, fontsize=10)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "operational_breakeven_time_bar.png"))
plt.close(fig)

# Energy Breakeven (kWh)
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

# New plot for Cost Breakeven vs. Carbon Breakeven Time
fig, ax = plt.subplots(figsize=(14, 7))
sns.scatterplot(data=df, x="Breakeven_With_Setup_Years", y="Carbon Breakeven Time (years)", hue="Scenario", s=100, ax=ax, palette="viridis")

# Add annotations to each point
for _, row in df.iterrows():
    ax.text(row["Breakeven_With_Setup_Years"] + 0.5, row["Carbon Breakeven Time (years)"], row["Scenario"], horizontalalignment='left', size='small', color='black')

ax.set_title("Cost Breakeven vs. Carbon Breakeven Time")
ax.set_xlabel("Cost Breakeven Time (Years)")
ax.set_ylabel("Carbon Breakeven Time (Years)")
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "cost_vs_carbon_scatter.png"))
plt.close(fig)
