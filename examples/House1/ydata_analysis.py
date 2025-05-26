import pandas as pd
import os
import matplotlib.pyplot as plt
import zipfile

# Define the directory where the CSV outputs are saved
script_dir = os.path.dirname(os.path.abspath(__file__))
output_dir = os.path.join(script_dir, "output")
plots_zip_dir = os.path.join(output_dir, "plots_archive") # New directory for plots before zipping
os.makedirs(plots_zip_dir, exist_ok=True) # Ensure this directory exists

# Define the paths to the generated CSV files for all three scenarios
monthly_5k_battery_csv = os.path.join(output_dir, "monthly_energy_summary_2023_battery_5k_kWh.csv")
monthly_nobattery_csv = os.path.join(output_dir, "monthly_energy_summary_2023_nobattery_kWh.csv")
monthly_8k_battery_csv = os.path.join(output_dir, "monthly_energy_summary_2023_battery_8k_kWh.csv")

yearly_5k_battery_csv = os.path.join(output_dir, "yearly_energy_summary_2023_battery_5k_kWh.csv")
yearly_nobattery_csv = os.path.join(output_dir, "yearly_energy_summary_2023_nobattery_kWh.csv")
yearly_8k_battery_csv = os.path.join(output_dir, "yearly_energy_summary_2023_battery_8k_kWh.csv")


print("--- Starting Energy Data Analysis from CSVs ---")

# --- 1. Load the CSV files ---
try:
    df_monthly_5k_battery = pd.read_csv(monthly_5k_battery_csv, index_col="Month")
    df_monthly_nobattery = pd.read_csv(monthly_nobattery_csv, index_col="Month")
    df_monthly_8k_battery = pd.read_csv(monthly_8k_battery_csv, index_col="Month")

    df_yearly_5k_battery = pd.read_csv(yearly_5k_battery_csv, index_col="Metric")
    df_yearly_nobattery = pd.read_csv(yearly_nobattery_csv, index_col="Metric")
    df_yearly_8k_battery = pd.read_csv(yearly_8k_battery_csv, index_col="Metric")

    print("\nSuccessfully loaded monthly and yearly summaries for all three scenarios.")

except FileNotFoundError as e:
    print(f"\nError: One or more required CSV files not found. Please ensure they are in the 'output' folder.")
    print(f"Missing file: {e.filename}")
    print("Please run the data generation script first to create the CSVs.")
    exit()

# --- 2. Display Monthly Summaries Side-by-Side ---
print("\n" + "="*80)
print("             MONTHLY ENERGY FLOW COMPARISON (kWh)             ")
print("="*80 + "\n")

print("\n--- Battery (5kWh) Scenario Monthly Summary ---")
print(df_monthly_5k_battery.to_string(float_format="%.2f"))

print("\n--- No Battery Scenario Monthly Summary ---")
print(df_monthly_nobattery.to_string(float_format="%.2f"))

print("\n--- Battery (8kWh) Scenario Monthly Summary ---")
print(df_monthly_8k_battery.to_string(float_format="%.2f"))


# --- 3. Key Metric Comparison (Yearly Totals) ---
print("\n" + "="*80)
print("             YEARLY TOTALS COMPARISON (kWh)             ")
print("="*80 + "\n")

# Combine yearly data for easier comparison across three scenarios
yearly_comparison = pd.DataFrame({
    'Battery (5kWh)': df_yearly_5k_battery['Value'],
    'No Battery': df_yearly_nobattery['Value'],
    'Battery (8kWh)': df_yearly_8k_battery['Value']
})

print(yearly_comparison.to_string(float_format="%.2f"))

# --- 4. Analyze the Impact of the Battery ---
print("\n" + "="*80)
print("             BATTERY IMPACT ANALYSIS             ")
print("="*80 + "\n")

# Common base metrics
total_demand = yearly_comparison.loc["Total Period Demand (kWh)", "No Battery"]
pv_production = yearly_comparison.loc["Total Period PV Production (kWh)", "No Battery"]

print(f"Total Annual Demand: {total_demand:.2f} kWh (Consistent across scenarios)")
print(f"Total Annual PV Production: {pv_production:.2f} kWh (Consistent across scenarios)")
print("-" * 60)

scenarios_to_compare = {
    "Battery (5kWh)": "battery_5k",
    "Battery (8kWh)": "battery_8k"
}

for scenario_label in scenarios_to_compare.keys():
    print(f"\n--- Comparing {scenario_label} vs. No Battery ---")

    grid_import_current = yearly_comparison.loc["Total Period Grid Import (kWh)", scenario_label]
    grid_import_nobattery = yearly_comparison.loc["Total Period Grid Import (kWh)", "No Battery"]
    grid_export_current = yearly_comparison.loc["Total Period Grid Export (kWh)", scenario_label]
    grid_export_nobattery = yearly_comparison.loc["Total Period Grid Export (kWh)", "No Battery"]
    pv_self_consumption_current = yearly_comparison.loc["Total Period PV Self-Consumption (kWh)", scenario_label]
    pv_self_consumption_nobattery = yearly_comparison.loc["Total Period PV Self-Consumption (kWh)", "No Battery"]
    self_sufficiency_current = yearly_comparison.loc["Total Period Self-Sufficiency (kWh)", scenario_label]
    self_sufficiency_nobattery = yearly_comparison.loc["Total Period Self-Sufficiency (kWh)", "No Battery"]

    battery_charge_current = yearly_comparison.loc["Total Period Battery Charge (kWh)", scenario_label] if "Total Period Battery Charge (kWh)" in yearly_comparison.index else 0.0
    battery_discharge_current = yearly_comparison.loc["Total Period Battery Discharge (kWh)", scenario_label] if "Total Period Battery Discharge (kWh)" in yearly_comparison.index else 0.0


    print(f"  Grid Import ({scenario_label}):      {grid_import_current:.2f} kWh")
    print(f"  Grid Import (No Battery): {grid_import_nobattery:.2f} kWh")
    print(f"  Reduction in Grid Import: {grid_import_nobattery - grid_import_current:.2f} kWh")
    print("-" * 40)

    print(f"  Grid Export ({scenario_label}):      {grid_export_current:.2f} kWh")
    print(f"  Grid Export (No Battery): {grid_export_nobattery:.2f} kWh")
    print(f"  Reduction in Grid Export: {grid_export_nobattery - grid_export_current:.2f} kWh")
    print("-" * 40)

    print(f"  PV Self-Consumption ({scenario_label}):    {pv_self_consumption_current:.2f} kWh")
    print(f"  PV Self-Consumption (No Battery): {pv_self_consumption_nobattery:.2f} kWh")
    print(f"  Increase in Self-Consumption: {pv_self_consumption_current - pv_self_consumption_nobattery:.2f} kWh")
    print("-" * 40)

    print(f"  Self-Sufficiency ({scenario_label}):    {self_sufficiency_current:.2f} kWh")
    print(f"  Self-Sufficiency (No Battery): {self_sufficiency_nobattery:.2f} kWh")
    print(f"  Increase in Self-Sufficiency: {self_sufficiency_current - self_sufficiency_nobattery:.2f} kWh")
    print("-" * 40)

    print(f"  Total Battery Charge ({scenario_label}): {battery_charge_current:.2f} kWh")
    print(f"  Total Battery Discharge ({scenario_label}): {battery_discharge_current:.2f} kWh")
    print("-" * 60)


# --- 5. Visualization (using Matplotlib only, individual plots) ---
print("\nGenerating individual plots for monthly metrics across all scenarios...")

# List of metrics to plot individually
plot_metrics = [
    "Demand (kWh)", "PV Production (kWh)", "Grid Import (kWh)", "Grid Export (kWh)",
    "PV Self-Consumption (kWh)", "Self-Sufficiency (kWh)"
]

generated_plot_files = [] # To store names of all generated plot files for zipping

# Define colors for each scenario for consistency
colors = {
    'Battery (5kWh)': 'blue',
    'No Battery': 'red',
    'Battery (8kWh)': 'green'
}
linestyles = {
    'Battery (5kWh)': '-',
    'No Battery': '--',
    'Battery (8kWh)': '-.'
}
markers = {
    'Battery (5kWh)': 'o',
    'No Battery': 'x',
    'Battery (8kWh)': '^'
}

# --- Plotting function for monthly data ---
def plot_monthly_metric(metric, df_5k, df_nobat, df_8k, plot_dir, colors, linestyles, markers):
    fig, ax = plt.subplots(figsize=(10, 10 * 13 / 21)) # Maintain 21:13 ratio

    # Plot for Battery (5kWh) - using drawstyle='steps-post'
    if metric in df_5k.columns:
        ax.plot(df_5k.index, df_5k[metric],
                label='Battery (5kWh)', marker=markers['Battery (5kWh)'],
                linestyle=linestyles['Battery (5kWh)'], color=colors['Battery (5kWh)'],
                drawstyle='steps-post')
    # Plot for No Battery - using drawstyle='steps-post'
    if metric in df_nobat.columns:
        ax.plot(df_nobat.index, df_nobat[metric],
                label='No Battery', marker=markers['No Battery'],
                linestyle=linestyles['No Battery'], color=colors['No Battery'],
                drawstyle='steps-post')
    # Plot for Battery (8kWh) - using drawstyle='steps-post'
    if metric in df_8k.columns:
        ax.plot(df_8k.index, df_8k[metric],
                label='Battery (8kWh)', marker=markers['Battery (8kWh)'],
                linestyle=linestyles['Battery (8kWh)'], color=colors['Battery (8kWh)'],
                drawstyle='steps-post')
    else:
        print(f"Skipping plot for '{metric}': Data not fully available across all scenarios.")
        plt.close(fig)
        return None

    ax.set_ylabel(metric)
    ax.set_xlabel("Month")
    ax.set_title(f'Monthly {metric} Comparison Across Scenarios', fontsize=14)
    ax.legend(loc='best') # Legend inside the plot, matplotlib determines best location
    ax.grid(True, linestyle='--', alpha=0.7)
    plt.xticks(rotation=45, ha='right')

    filename = f"monthly_{metric.replace(' (kWh)', '').replace(' ', '_').lower()}_comparison.png"
    filepath = os.path.join(plot_dir, filename)
    plt.tight_layout()
    plt.savefig(filepath)
    plt.close(fig)
    return filepath

for metric in plot_metrics:
    filepath = plot_monthly_metric(metric, df_monthly_5k_battery, df_monthly_nobattery, df_monthly_8k_battery, plots_zip_dir, colors, linestyles, markers)
    if filepath:
        generated_plot_files.append(filepath)
        print(f"Saved: {filepath}")

# Bar chart for yearly totals comparison (key metrics) - remains a bar chart
yearly_plot_metrics_order = [
    "Total Period Demand (kWh)",
    "Total Period PV Production (kWh)",
    "Total Period Grid Import (kWh)",
    "Total Period Grid Export (kWh)",
    "Total Period PV Self-Consumption (kWh)",
    "Total Period Self-Sufficiency (kWh)",
    "Overall Self-Consumption Rate (%)",
    "Overall Self-Sufficiency Rate (%)"
]

if "Total Period Battery Charge (kWh)" in yearly_comparison.index:
    yearly_plot_metrics_order.append("Total Period Battery Charge (kWh)")
if "Total Period Battery Discharge (kWh)" in yearly_comparison.index:
    yearly_plot_metrics_order.append("Total Period Battery Discharge (kWh)")

bar_chart_data = yearly_comparison.loc[yearly_plot_metrics_order]

fig2, ax2 = plt.subplots(figsize=(12, 12 * 13 / 21)) # Maintain 21:13 ratio
bar_chart_data.plot(kind='bar', ax=ax2, width=0.7)
ax2.set_title('Yearly Energy Totals Comparison Across Scenarios', fontsize=16)
ax2.set_ylabel('Value (kWh or %)')
ax2.set_xlabel('Metric')
ax2.set_xticklabels([label.replace(' (kWh)', '').replace(' (%)', '') for label in bar_chart_data.index], rotation=45, ha='right')
ax2.yaxis.grid(True, linestyle='--', alpha=0.7)
ax2.legend(title="Scenario", loc='best')
plt.tight_layout()
yearly_bar_filepath = os.path.join(plots_zip_dir, 'yearly_energy_comparison_bar.png')
plt.savefig(yearly_bar_filepath)
generated_plot_files.append(yearly_bar_filepath)
print(f"Saved: {yearly_bar_filepath}")
plt.close(fig2)


# --- Create a zip file of all generated plots ---
zip_filename = os.path.join(output_dir, "energy_plots_2023_kWh_3scenarios.zip")
print(f"\nCreating zip archive: {zip_filename}")

with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for plot_file in generated_plot_files:
        zipf.write(plot_file, os.path.basename(plot_file))
        print(f"  Added {os.path.basename(plot_file)} to zip.")

print(f"All plots successfully zipped to: {zip_filename}")

# Clean up the temporary plots directory
try:
    os.rmdir(plots_zip_dir)
    print(f"Temporary plots directory removed: {plots_zip_dir}")
except OSError as e:
    print(f"Error removing temporary plots directory {plots_zip_dir}: {e}")


print("\n--- Energy Data Analysis Complete ---")
print("Check the 'output' folder for CSV summaries and the .zip file containing plots.")