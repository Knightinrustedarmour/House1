import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# --- Configuration ---
try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
except NameError:
    script_dir = os.getcwd()

# Input CSV
input_csv = os.path.join(script_dir, "output", "monthly_energy_flows", "monthly_energy_flows_master_table.csv")

# Output directory for plots
output_root = os.path.join(script_dir, "monthly_barplots")
os.makedirs(output_root, exist_ok=True)

# 21:9 figure dimensions
FIG_WIDTH = 21
FIG_HEIGHT = 9
sns.set(style="whitegrid", context="talk", font_scale=1.1)

# Flows to plot (as in your CSV)
FLOWS_STANDARD = [
    "Demand_Consumption",
    "Grid_Import",
    "PV_Direct_Consumption",
    "Total_PV_Production",
    "Grid_Export_to_Grid",
    "Battery_Charge",
    "Battery_Discharge"
]

LABELS_STANDARD = {
    "Demand_Consumption": "Demand [kWh]",
    "Grid_Import": "Grid Import [kWh]",
    "PV_Direct_Consumption": "PV Direct Consumption [kWh]",
    "Total_PV_Production": "Total PV Production [kWh]",
    "Grid_Export_to_Grid": "Grid Export [kWh]",
    "Battery_Charge": "Battery Charge [kWh]",
    "Battery_Discharge": "Battery Discharge [kWh]"
}

# Month mapping and order
MONTH_NAMES = {
    'jan': 'January', 'feb': 'February', 'mar': 'March', 'apr': 'April',
    'may': 'May', 'jun': 'June', 'jul': 'July', 'aug': 'August',
    'sep': 'September', 'oct': 'October', 'nov': 'November', 'dec': 'December'
}
MONTH_ORDER = list(MONTH_NAMES.keys())  # ['jan','feb',...]

# --- Load Data ---
df = pd.read_csv(input_csv)

# Ensure Month is categorical and ordered
if 'Month' in df.columns:
    df['Month'] = pd.Categorical(df['Month'], categories=MONTH_ORDER, ordered=True)
else:
    raise ValueError("Input CSV must contain a 'Month' column with abbreviations (e.g., 'jan').")

# Ensure Scenario column exists
if 'Scenario' not in df.columns:
    raise ValueError("Input CSV must contain a 'Scenario' column.")

# --- Compute fallback ratios if not present ---
# Autarky_Ratio = PV Direct Consumption / Demand (cap at 1)
if 'Autarky_Ratio' not in df.columns:
    if ('PV_Direct_Consumption' in df.columns) and ('Demand_Consumption' in df.columns):
        df['Autarky_Ratio'] = (df['PV_Direct_Consumption'] / df['Demand_Consumption']).fillna(0).clip(upper=1)
    else:
        df['Autarky_Ratio'] = 0.0

# Grid_Dependency_Ratio = Grid Import / Demand (cap at 1)
if 'Grid_Dependency_Ratio' not in df.columns:
    if ('Grid_Import' in df.columns) and ('Demand_Consumption' in df.columns):
        df['Grid_Dependency_Ratio'] = (df['Grid_Import'] / df['Demand_Consumption']).fillna(0).clip(upper=1)
    else:
        df['Grid_Dependency_Ratio'] = 0.0

# --- Existing per-scenario monthly barplots (your original) ---
for scenario in df['Scenario'].unique():
    scenario_dir = os.path.join(output_root, scenario)
    os.makedirs(scenario_dir, exist_ok=True)
    
    df_scenario = df[df['Scenario'] == scenario]
    
    for month in df_scenario['Month'].unique():
        df_month = df_scenario[df_scenario['Month'] == month]
        
        # Determine which flows to plot
        flows_to_plot = [f for f in FLOWS_STANDARD if f in df_month.columns]
        
        # Explicitly remove battery flows for PV_NoBattery scenario (if exists)
        if scenario == "PV_NoBattery":
            flows_to_plot = [f for f in flows_to_plot if f not in ["Battery_Charge", "Battery_Discharge"]]
        
        labels_to_plot = [LABELS_STANDARD[f] for f in flows_to_plot]
        
        # Sum energy values for the month
        energy_values = df_month[flows_to_plot].sum()
        
        # --- Plot ---
        plt.figure(figsize=(FIG_WIDTH, FIG_HEIGHT))
        plt.bar(labels_to_plot, energy_values, color=sns.color_palette("Set2", len(labels_to_plot)))
        plt.ylabel("Energy (kWh)")
        
        # Formatted title
        formatted_month = MONTH_NAMES.get(month, month.capitalize())
        if scenario == "PV_NoBattery":
            title_text = f"No battery | {formatted_month} | Energy summary"
        else:
            title_text = f"{scenario} battery | {formatted_month} | Energy summary"
            
        plt.title(title_text, fontsize=18, fontweight='bold', pad=14)
        plt.xticks(rotation=30, ha='right')
        
        # Remove legend
        plt.legend().set_visible(False)
        
        # Save plot (no underscores in file name; use hyphens)
        plot_filename = f"{scenario}-{month}-flows.png"
        plot_file = os.path.join(scenario_dir, plot_filename)
        plt.tight_layout()
        plt.savefig(plot_file, dpi=300)
        plt.close()
        
        print(f"Saved plot: {plot_file}")

print("✅ Original monthly bar plots generated.")

# ---------------------------------------------------------------------
# --- PART A: Annual comparison bar charts (one chart per comparison) ---
# We'll compute annual sums across months for each scenario and create grouped bar charts.
# Comparisons requested:
# 1) Grid Import vs Grid Export
# 2) Battery Charge vs Battery Discharge
# 3) PV Distribution (Total PV Production) vs PV Self-Use (PV Direct Consumption)
# 4) Autarky Ratios (single bar per scenario)
# 5) Grid Dependency Ratios (single bar per scenario)
# ---------------------------------------------------------------------

annual_dir = os.path.join(output_root, "annual-comparisons")
os.makedirs(annual_dir, exist_ok=True)

# Aggregate annual sums per scenario
agg_cols_energy = [c for c in [
    "Grid_Import",
    "Grid_Export_to_Grid",
    "Battery_Charge",
    "Battery_Discharge",
    "Total_PV_Production",
    "PV_Direct_Consumption",
    "Demand_Consumption"
] if c in df.columns]

annual = df.groupby('Scenario')[agg_cols_energy].sum().reset_index()

# Also aggregate ratios (take mean weighted by months or simple average - here simple average across months)
annual_ratios = df.groupby('Scenario')[['Autarky_Ratio', 'Grid_Dependency_Ratio']].mean().reset_index()

# 1) Grid Import vs Grid Export
plotname = "Grid Import vs Export"
plot_folder = os.path.join(annual_dir, "Grid Import vs Export")
os.makedirs(plot_folder, exist_ok=True)

x = np.arange(len(annual['Scenario']))
width = 0.35

fig, ax = plt.subplots(figsize=(21,9))
if 'Grid_Import' in annual.columns:
    ax.bar(x - width/2, annual['Grid_Import'], width, label='Grid Import (kWh)', color='tab:blue')
if 'Grid_Export_to_Grid' in annual.columns:
    ax.bar(x + width/2, annual['Grid_Export_to_Grid'], width, label='Grid Export (kWh)', color='tab:orange')

ax.set_ylabel('Energy (kWh)')
ax.set_title('Annual Grid Import vs Grid Export by Scenario', fontsize=16, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(annual['Scenario'], rotation=45, ha='right')
ax.legend()
plt.tight_layout()
pngfile = os.path.join(plot_folder, f"{plotname}.png")
plt.savefig(pngfile, dpi=300)
plt.close()
print(f"Saved annual comparison: {pngfile}")

# 2) Battery Charge vs Battery Discharge
plotname = "Battery Charge vs Discharge"
plot_folder = os.path.join(annual_dir, "Battery Charge vs Discharge")
os.makedirs(plot_folder, exist_ok=True)

fig, ax = plt.subplots(figsize=(21,9))
if 'Battery_Charge' in annual.columns:
    ax.bar(x - width/2, annual['Battery_Charge'], width, label='Battery Charge (kWh)', color='tab:green')
if 'Battery_Discharge' in annual.columns:
    ax.bar(x + width/2, annual['Battery_Discharge'], width, label='Battery Discharge (kWh)', color='tab:red')

ax.set_ylabel('Energy (kWh)')
ax.set_title('Annual Battery Charge vs Discharge by Scenario', fontsize=16, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(annual['Scenario'], rotation=45, ha='right')
ax.legend()
plt.tight_layout()
pngfile = os.path.join(plot_folder, f"{plotname}.png")
plt.savefig(pngfile, dpi=300)
plt.close()
print(f"Saved annual comparison: {pngfile}")

# 3) PV Distribution vs PV Self-Use (use Total_PV_Production and PV_Direct_Consumption)
plotname = "PV Production vs PV Self Use"
plot_folder = os.path.join(annual_dir, "PV Production vs Self Use")
os.makedirs(plot_folder, exist_ok=True)

fig, ax = plt.subplots(figsize=(21,9))
if 'Total_PV_Production' in annual.columns:
    ax.bar(x - width/2, annual['Total_PV_Production'], width, label='Total PV Production (kWh)', color='tab:purple')
if 'PV_Direct_Consumption' in annual.columns:
    ax.bar(x + width/2, annual['PV_Direct_Consumption'], width, label='PV Self Use (kWh)', color='tab:olive')

ax.set_ylabel('Energy (kWh)')
ax.set_title('Annual PV Production vs PV Self Use by Scenario', fontsize=16, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(annual['Scenario'], rotation=45, ha='right')
ax.legend()
plt.tight_layout()
pngfile = os.path.join(plot_folder, f"{plotname}.png")
plt.savefig(pngfile, dpi=300)
plt.close()
print(f"Saved annual comparison: {pngfile}")

# 4) Autarky Ratios
plotname = "Autarky Ratios"
plot_folder = os.path.join(annual_dir, "Autarky Ratios")
os.makedirs(plot_folder, exist_ok=True)

fig, ax = plt.subplots(figsize=(21,9))
ax.bar(annual_ratios['Scenario'], annual_ratios['Autarky_Ratio'], color=sns.color_palette("Set2", len(annual_ratios)))
ax.set_ylabel('Autarky Ratio')
ax.set_title('Annual Autarky Ratio by Scenario', fontsize=16, fontweight='bold')
ax.set_xticklabels(annual_ratios['Scenario'], rotation=45, ha='right')
plt.tight_layout()
pngfile = os.path.join(plot_folder, f"{plotname}.png")
plt.savefig(pngfile, dpi=300)
plt.close()
print(f"Saved annual comparison: {pngfile}")

# 5) Grid Dependency Ratios
plotname = "Grid Dependency Ratios"
plot_folder = os.path.join(annual_dir, "Grid Dependency Ratios")
os.makedirs(plot_folder, exist_ok=True)

fig, ax = plt.subplots(figsize=(21,9))
ax.bar(annual_ratios['Scenario'], annual_ratios['Grid_Dependency_Ratio'], color=sns.color_palette("Set2", len(annual_ratios)))
ax.set_ylabel('Grid Dependency Ratio')
ax.set_title('Annual Grid Dependency Ratio by Scenario', fontsize=16, fontweight='bold')
ax.set_xticklabels(annual_ratios['Scenario'], rotation=45, ha='right')
plt.tight_layout()
pngfile = os.path.join(plot_folder, f"{plotname}.png")
plt.savefig(pngfile, dpi=300)
plt.close()
print(f"Saved annual comparison: {pngfile}")

# ---------------------------------------------------------------------
# --- PART B: Worm plots (monthly curves) for each parameter ---
# Each parameter -> 1 figure. X axis = months (Jan..Dec). One curve per scenario.
# ---------------------------------------------------------------------

worm_dir = os.path.join(output_root, "worm-plots")
os.makedirs(worm_dir, exist_ok=True)

# Parameters to create worm plots for (energy flows and ratios)
worm_parameters = [
    "Grid_Import",
    "Grid_Export_to_Grid",
    "Battery_Charge",
    "Battery_Discharge",
    "Total_PV_Production",
    "PV_Direct_Consumption",
    "Autarky_Ratio",
    "Grid_Dependency_Ratio"
]

# Build monthly pivot table: index Month, columns Scenario, values = sum of parameter per month
monthly_grouped = df.groupby(['Month', 'Scenario'])[worm_parameters].sum().reset_index()

# For each parameter, create a pivot table month x scenario
for param in worm_parameters:
    if param not in monthly_grouped.columns:
        print(f"Skipping worm plot for {param}: column not present.")
        continue

    param_folder = os.path.join(worm_dir, param.replace('_', ' '))
    os.makedirs(param_folder, exist_ok=True)

    pivot = monthly_grouped.pivot(index='Month', columns='Scenario', values=param)
    # Reindex rows to ensure month order
    pivot = pivot.reindex(MONTH_ORDER)

    # Convert month index to readable labels
    month_labels = [MONTH_NAMES[m] for m in pivot.index]

    plt.figure(figsize=(21,9))
    palette = sns.color_palette("tab10", n_colors=len(pivot.columns))
    for idx, scenario in enumerate(pivot.columns):
        series = pivot[scenario].fillna(0).values
        plt.plot(month_labels, series, marker='o', label=scenario, linewidth=2, alpha=0.9)

    plt.title(f"{param.replace('_', ' ')} - Monthly behavior by scenario", fontsize=16, fontweight='bold')
    plt.ylabel(param.replace('_', ' '))
    plt.xlabel('Month')
    plt.xticks(rotation=45)
    plt.grid(True, linestyle='--', alpha=0.4)
    plt.legend(title='Scenario', bbox_to_anchor=(1.02, 1), loc='upper left')
    plt.tight_layout()

    pngfile = os.path.join(param_folder, f"{param.replace('_', ' ')} - Monthly Curve.png")
    plt.savefig(pngfile, dpi=300)
    plt.close()
    print(f"Saved worm plot: {pngfile}")

print("✅ All annual comparisons and worm plots generated successfully.")
