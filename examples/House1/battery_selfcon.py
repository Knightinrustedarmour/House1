import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns # For enhanced plot aesthetics
import numpy as np

# --- Configuration ---
script_dir = os.path.dirname(os.path.abspath(__file__))
# Define the output directory for this specific plot
output_directory = os.path.join(script_dir, "output", "combined_energy_metrics_plots") 

# Ensure the output directory exists
os.makedirs(output_directory, exist_ok=True)

print("--- Starting Combined Energy Metrics Plot Generation ---")

# Define scenarios with their capacities for data retrieval
scenarios_to_plot = {
    "5kWh": { "capacity": 5000 },
    "NoBattery": { "capacity": 0 }, 
    "8kWh": { "capacity": 8000 },
    "12kWh": { "capacity": 12000 },
    "15kWh": { "capacity": 15000 },
    "20kWh": { "capacity": 20000 },
    "26kWh": { "capacity": 26000 },
    "50kWh": { "capacity": 50000 }
}

# Define the specific rows to extract from the summary CSVs
required_rows = {
    "PV Self-Consumption (kWh)": "Total Period PV Self-Consumption (kWh)",
    "Grid Export (kWh)": "Total Period Grid Export (kWh)",
    "Net Cost (€)": "Total Net Cost (eur)" # Match the exact row name from your CSV
}
collected_data_points = []

# --- Collect Data from CSVs ---
print("\n--- Collecting Energy Metrics Data from CSVs ---")
for scenario_name, config in scenarios_to_plot.items():
    battery_size_kwh = config["capacity"] / 1000
    
    # Construct the expected CSV filename based on scenario name and capacity
    if scenario_name == "NoBattery":
        csv_filename = "yearly_energy_summary_2023_nobattery_kWh.csv"
    else:
        csv_filename = f"yearly_energy_summary_2023_battery_{int(battery_size_kwh)}k_kWh.csv"
    
    # Corrected path: CSVs are directly in the base_output_directory
    csv_path = os.path.join(script_dir, "output", csv_filename) # Explicitly use script_dir/output

    if not os.path.exists(csv_path):
        print(f"  Warning: Summary CSV not found for {scenario_name} at {csv_path}. Skipping this scenario.")
        continue

    try:
        summary_df = pd.read_csv(csv_path, header=None, index_col=0)
        
        for metric_label, row_name_in_csv in required_rows.items():
            if row_name_in_csv in summary_df.index:
                value = float(summary_df.loc[row_name_in_csv, 1])
                collected_data_points.append({
                    'Battery_Size_kWh': battery_size_kwh,
                    'Value': value,
                    'Metric_Type': metric_label, # Use the descriptive label
                    'Scenario': scenario_name 
                })
                print(f"  Collected {metric_label} for {scenario_name}: {value:.2f}.")
            else:
                print(f"  Warning: '{row_name_in_csv}' not found in {csv_path}. Skipping {metric_label} for {scenario_name}.")

    except Exception as e:
        print(f"  An error occurred while reading or processing {csv_path}: {e}. Skipping {scenario_name}.")

if not collected_data_points:
    print("No valid data points were collected for plotting. Exiting.")
    exit()

# Create a single DataFrame from all collected data
plot_df = pd.DataFrame(collected_data_points)

# Sort by Battery_Size_kWh for cleaner plotting order
plot_df = plot_df.sort_values(by=['Battery_Size_kWh', 'Metric_Type']).reset_index(drop=True)

# --- Plot Data ---
plot_png_path = os.path.join(output_directory, "Energy_Metrics_Combined_Plot_vs_Battery_Size.png") # Updated filename

print("\n--- Generating Energy Metrics Combined Plot ---")

# Set up the plot
fig, ax = plt.subplots(figsize=(14, 9)) # Slightly larger figure for three data series

# Use seaborn for a scatter plot, using 'Metric_Type' for hue
sns.scatterplot(
    x='Battery_Size_kWh', 
    y='Value',             # 'Value' column holds all three metrics
    hue='Metric_Type',     # Differentiate metrics by color
    data=plot_df, 
    s=300,                 # Size of dots
    ax=ax,
    palette={
        'PV Self-Consumption (kWh)': 'green', 
        'Grid Export (kWh)': 'blue', # New color for Grid Export
        'Net Cost (€)': 'purple'
    }, 
    legend='full',
    zorder=2 # Ensure dots are on top of grid
)

# Add text labels next to each point for clarity
for i, row in plot_df.iterrows():
    # Adjust text offset dynamically to minimize overlap for three series
    text_offset_x = 0.1 # Default small x offset
    text_offset_y = 15 # Default positive y offset for labels
    
    if row['Battery_Size_kWh'] == 0:
        text_offset_x = 0.05 # Smaller x offset for 'No Battery'
    
    # Fine-tune y-offsets for each metric type for better separation
    if row['Metric_Type'] == 'PV Self-Consumption (kWh)':
        text_offset_y = 15
    elif row['Metric_Type'] == 'Grid Export (kWh)':
        text_offset_y = 0 # Center or slightly offset
    elif row['Metric_Type'] == 'Net Cost (€)':
        text_offset_y = -15 # Move cost label slightly down

    # Format value based on metric type (no decimals for kWh, 0 for EUR)
    formatted_value = f"{row['Value']:.0f}"
    if row['Metric_Type'] == 'Net Cost (€)':
        formatted_value = f"{row['Value']:.0f}" # Keep as whole for Euros

    ax.text(
        row['Battery_Size_kWh'] + text_offset_x, 
        row['Value'] + text_offset_y, 
        formatted_value, 
        ha='left', va='center', fontsize=9, color='dimgray'
    )

ax.set_title("Battery Nominal Capacity vs. Yearly PV Self-Consumption, Grid Export, and Net Cost (2023)") # Updated title
ax.set_xlabel("Battery Nominal Capacity (kWh)")
ax.set_ylabel("Value (kWh / €)") # Y-axis represents both kWh and Euros
ax.grid(True, linestyle='--', alpha=0.7, zorder=1) # Grid behind dots

# Set x-ticks to precisely match your battery sizes
unique_capacities_kwh = sorted(plot_df['Battery_Size_kWh'].unique())
ax.set_xticks(unique_capacities_kwh)
# Ensure labels are whole numbers without decimals
ax.set_xticklabels([f"{int(x)} kWh" for x in unique_capacities_kwh])

# Set x-axis limits to start from 0 and extend slightly beyond max capacity
ax.set_xlim(left=0, right=max(unique_capacities_kwh) * 1.1)

# Ensure y-axis starts from 0 (energy and cost are typically non-negative)
ax.set_ylim(bottom=0)

plt.tight_layout()

# Save plot as PNG
fig.savefig(plot_png_path, dpi=300)
print(f"Plot saved to: {plot_png_path}")
plt.close(fig)

print("\nCombined energy metrics plot generation completed.")
