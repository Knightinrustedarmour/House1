import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from zipfile import ZipFile
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np

# --- 1. SOC Calculation Function (Unchanged) ---
def soc(charge_series_wmin, discharge_series_wmin, index, 
        nominal_capacity_wh=5000, charge_eff=0.96, discharge_eff=0.96, 
        loss_rate=0.0005, initial_soc_wh=None, soc_min_frac=0.1):
    """
    Calculates the State of Charge (SOC) of a battery over time.
    Assumes charge_series_wmin and discharge_series_wmin are in Watt-minutes (Wmin) per 1-minute interval.
    The time step (dt_hours) for self-discharge is assumed constant 1 minute, but derived for clarity.
    Returns SOC as a list of percentage values.
    """
    
    # Convert Watt-minutes to Watt-hours for each 1-minute interval
    charge_series_wh_per_interval = charge_series_wmin / 60.0
    discharge_series_wh_per_interval = discharge_series_wmin / 60.0

    if initial_soc_wh is None:
        initial_soc_wh = 0.5 * nominal_capacity_wh

    soc_values_wh = [initial_soc_wh] # Store SOC in Wh internally
    soc_min = soc_min_frac * nominal_capacity_wh
    
    dt_hours_per_interval = 1 / 60.0 # Each step represents 1 minute = 1/60 hour

    for i in range(len(charge_series_wh_per_interval)):
        last_soc_wh = soc_values_wh[-1] 
        
        # Apply self-discharge loss for this interval
        loss_this_interval_wh = loss_rate * nominal_capacity_wh * dt_hours_per_interval
        current_soc_wh = last_soc_wh - loss_this_interval_wh

        # Apply charge and discharge for this interval
        charge_energy_wh = charge_series_wh_per_interval.iloc[i] * charge_eff
        discharge_energy_wh = discharge_series_wh_per_interval.iloc[i] / discharge_eff 
        
        current_soc_wh = current_soc_wh + charge_energy_wh - discharge_energy_wh

        # Apply capacity bounds (min/max SOC)
        current_soc_wh = max(soc_min, min(nominal_capacity_wh, current_soc_wh))
        
        soc_values_wh.append(current_soc_wh) 

    return [val / nominal_capacity_wh * 100 for val in soc_values_wh[1:]]


# --- Helper function to plot duration curves (Slightly modified to only plot monthly now) ---
def export_duration_curves(df, output_dir, scenario_name, nominal_capacity):
    duration_curve_pdf_path = os.path.join(output_dir, f"SOC_Duration_Curves_{scenario_name}.pdf")
    png_files_for_zip = []

    with PdfPages(duration_curve_pdf_path) as pdf_duration_curves:
        # Monthly SOC Duration Curves
        for month_name in df["Month"].unique():
            print(f"  Generating Monthly SOC Duration Curve for {scenario_name} - {month_name}...")
            month_df = df[df["Month"] == month_name].copy()
            month_df = month_df.sort_values("SOC_%", ascending=False).reset_index(drop=True)

            duration_hours_monthly = np.arange(1, len(month_df) + 1) / 60.0

            fig_monthly, ax_monthly = plt.subplots(figsize=(10, 10 * 13 / 21))
            ax_monthly.plot(duration_hours_monthly, month_df["SOC_%"])
            ax_monthly.set_xlabel("Duration (Hours of the month)")
            ax_monthly.set_ylabel("SOC (%)")
            ax_monthly.set_title(f"SOC Duration Curve - {scenario_name} - {month_name}")
            ax_monthly.grid(True)
            ax_monthly.set_ylim(0, 100)
            plt.tight_layout()
            pdf_duration_curves.savefig(fig_monthly)
            png_path_monthly = os.path.join(output_dir, f"{scenario_name}_{month_name}_SOC_Duration_Curve.png")
            fig_monthly.savefig(png_path_monthly, dpi=300)
            png_files_for_zip.append(png_path_monthly)
            plt.close(fig_monthly)
    
    return png_files_for_zip


# --- Helper function to plot combined heatmaps (Unchanged) ---
def export_combined_heatmaps(df_flows, output_dir, scenario_name):
    """
    Generates and saves combined heatmaps for battery power flow (charge - discharge).
    df_flows should contain time-indexed Battery_charge_W and Battery_discharge_W in Wmin.
    """
    heatmap_pdf_path = os.path.join(output_dir, f"Battery_Net_Power_Heatmaps_{scenario_name}.pdf")
    png_files_for_zip = []

    with PdfPages(heatmap_pdf_path) as pdf_heatmaps:
        for month_name in df_flows["Month"].unique():
            print(f"  Generating Combined Battery Net Power Heatmap for {scenario_name} - {month_name}...")
            month_df = df_flows[df_flows["Month"] == month_name].copy()
            
            charge_series = month_df[f"Battery_charge_W_{scenario_name}"]
            discharge_series = month_df[f"Battery_discharge_W_{scenario_name}"]

            net_power_wmin = charge_series - discharge_series

            net_power_hourly_wh = net_power_wmin.resample('H').sum() / 60.0
            
            hourly_data = pd.DataFrame({
                'Value': net_power_hourly_wh.values
            }, index=net_power_hourly_wh.index)
            hourly_data['hour'] = hourly_data.index.hour
            hourly_data['day'] = hourly_data.index.day

            pivot_table = hourly_data.pivot_table(index='hour', columns='day', values='Value').fillna(0)

            fig, ax = plt.subplots(figsize=(12, 12 * 13 / 21))
            
            max_val = pivot_table.abs().max().max()
            sns.heatmap(pivot_table, cmap="coolwarm", annot=False, fmt=".0f", 
                        linewidths=.5, ax=ax, center=0, vmin=-max_val, vmax=max_val)
            
            ax.set_title(f"Battery Net Power Heatmap (Wh/Hour) - {scenario_name} - {month_name}")
            ax.set_xlabel("Day of Month")
            ax.set_ylabel("Hour of Day")
            plt.tight_layout()
            pdf_heatmaps.savefig(fig)
            png_path = os.path.join(output_dir, f"{scenario_name}_{month_name}_Battery_Net_Power_Heatmap.png")
            fig.savefig(png_path, dpi=300)
            png_files_for_zip.append(png_path)
            plt.close(fig)
            
    return png_files_for_zip

# --- NEW: Function to plot yearly SOC comparison ---
def plot_yearly_soc_comparison(yearly_dfs_dict, main_output_dir):
    print("\n--- Generating Yearly SOC Comparison Plot ---")
    
    fig, ax = plt.subplots(figsize=(12, 12 * 13 / 21))
    
    comparison_pdf_path = os.path.join(main_output_dir, "Yearly_SOC_Comparison.pdf")
    comparison_png_path = os.path.join(main_output_dir, "Yearly_SOC_Comparison.png")

    with PdfPages(comparison_pdf_path) as pdf_comparison:
        for scenario_name, df in yearly_dfs_dict.items():
            # Extract SOC data for the current scenario
            soc_column = f"SOC_{scenario_name}_%"
            if soc_column not in df.columns:
                print(f"  Warning: SOC column '{soc_column}' not found for {scenario_name}. Skipping comparison for this scenario.")
                continue
            
            yearly_soc_data = df.sort_values(soc_column, ascending=False).reset_index(drop=True)
            duration_hours_yearly = np.arange(1, len(yearly_soc_data) + 1) / 60.0
            
            ax.plot(duration_hours_yearly, yearly_soc_data[soc_column], label=f"{scenario_name} Battery")
            
        ax.set_xlabel("Duration (Hours)")
        ax.set_ylabel("SOC (%)")
        ax.set_title("Yearly SOC Duration Curve Comparison")
        ax.grid(True)
        ax.set_ylim(0, 100)
        ax.legend()
        plt.tight_layout()
        
        pdf_comparison.savefig(fig)
        fig.savefig(comparison_png_path, dpi=300)
        plt.close(fig)
    
    print(f"Yearly SOC Comparison PDF saved at: {comparison_pdf_path}")
    print(f"Yearly SOC Comparison PNG saved at: {comparison_png_path}")
    
    return [comparison_png_path]


# --- Main Processing Function (Modified to return yearly_df) ---
def process_scenario_data(scenario_name, flow_dir, file_dict, capacity):
    print(f"\n--- Processing {scenario_name} Battery Data (Capacity: {capacity} Wh) ---")
    
    scenario_output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", scenario_name)
    os.makedirs(scenario_output_dir, exist_ok=True)

    all_monthly_dfs = [] 

    for month_abbr, filename in file_dict.items():
        filepath = os.path.join(flow_dir, filename)
        
        if not os.path.exists(filepath):
            print(f"  Warning: File not found: {filepath}. Skipping {month_abbr} for {scenario_name}.")
            continue

        try:
            results = pd.read_csv(filepath, header=[0, 1], index_col=0)
            results.index = pd.to_datetime(results.index, utc=True)

            monthly_data = pd.DataFrame(index=results.index)
            
            charge_series = results[[column_paths["Battery_charge"]]].squeeze()
            discharge_series = results[[column_paths["Battery_discharge"]]].squeeze()

            charge_series = charge_series.clip(lower=0)
            discharge_series = discharge_series.clip(lower=0)
            
            soc_percent_values = soc(
                charge_series, 
                discharge_series, 
                results.index, 
                nominal_capacity_wh=capacity
            )
            
            monthly_data[f"Battery_charge_W_{scenario_name}"] = charge_series
            monthly_data[f"Battery_discharge_W_{scenario_name}"] = discharge_series
            monthly_data[f"SOC_{scenario_name}_%"] = pd.Series(soc_percent_values, index=results.index[:len(soc_percent_values)])
            
            monthly_data['Month'] = month_abbr.capitalize()
            all_monthly_dfs.append(monthly_data)
            
            print(f"  Processed {filename} for {scenario_name}")

        except KeyError as e:
            print(f"  Error: Missing expected column in {filename} for {scenario_name}. Error: {e}")
        except Exception as e:
            print(f"  An unexpected error occurred while processing {filepath}: {e}")

    if not all_monthly_dfs:
        print(f"No data was processed for {scenario_name}. Skipping plotting and CSV export.")
        return None # Return None if no data processed

    yearly_df = pd.concat(all_monthly_dfs)
    
    output_csv_path = os.path.join(scenario_output_dir, f"Combined_Battery_Data_{scenario_name}.csv")
    yearly_df.to_csv(output_csv_path)
    print(f"Combined data for {scenario_name} exported to: {output_csv_path}")

    # Generate plots
    print(f"\n--- Generating plots for {scenario_name} ---")
    all_png_files = []

    # Get SOC data for duration curves
    soc_for_duration_curves = yearly_df[[f"SOC_{scenario_name}_%", 'Month']].copy()
    soc_for_duration_curves.rename(columns={f"SOC_{scenario_name}_%": "SOC_%"}, inplace=True)
    all_png_files.extend(export_duration_curves(soc_for_duration_curves, scenario_output_dir, scenario_name, capacity))

    # Get Flow data for combined heatmaps
    all_png_files.extend(export_combined_heatmaps(yearly_df, scenario_output_dir, scenario_name))

    # Create a zip archive of all generated PNGs for the scenario
    zip_path = os.path.join(scenario_output_dir, f"{scenario_name}_Plots.zip")
    with ZipFile(zip_path, 'w') as zipf:
        for file_path in all_png_files:
            if os.path.exists(file_path):
                zipf.write(file_path, arcname=os.path.basename(file_path))
            else:
                print(f"  Warning: PNG file not found for zipping: {file_path}")
    print(f"All plots for {scenario_name} zipped to: {zip_path}")
    
    return yearly_df # Return the yearly_df for comparison


# --- Global Configuration (Unchanged) ---
script_dir = os.path.dirname(os.path.abspath(__file__))

column_paths = {
    "Battery_charge": ("SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='distribution')", "SolphLabel(location='House1', mtress_component='storage1', solph_node='Battery_Storage')"),
    "Battery_discharge": ("SolphLabel(location='House1', mtress_component='storage1', solph_node='Battery_Storage')", "SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='distribution')")
}

scenarios_config = {
    "5kWh": {
        "flow_dir": os.path.join(script_dir, "flows"),
        "files": {
            'jan': 'flow_W_jan23.csv', 'feb': 'flow_W_feb23.csv',
            'mar': 'flow_W_mar23.csv', 'apr': 'flow_W_apr23.csv', 'may': 'flow_W_may23.csv',
            'jun': 'flow_W_jun23.csv', 'jul': 'flow_W_jul23.csv', 'aug': 'flow_W_aug23.csv',
            'sep': 'flow_W_sep23.csv', 'oct': 'flow_W_oct23.csv', 'nov': 'flow_W_nov23.csv',
            'dec': 'flow_W_dec23.csv'
        },
        "capacity": 5000
    },
    "8kWh": {
        "flow_dir": os.path.join(script_dir, "flows_8k"),
        "files": {
            'jan': 'flow_8k_jan23.csv', 'feb': 'flow_8k_feb23.csv',
            'mar': 'flow_8k_mar23.csv', 'apr': 'flow_8k_apr23.csv', 'may': 'flow_8k_may23.csv',
            'jun': 'flow_8k_jun23.csv', 'jul': 'flow_8k_jul23.csv', 'aug': 'flow_8k_aug23.csv',
            'sep': 'flow_8k_sep23.csv', 'oct': 'flow_8k_oct23.csv', 'nov': 'flow_8k_nov23.csv',
            'dec': 'flow_8k_dec23.csv'
        },
        "capacity": 8000
    }
}


# --- Main Execution ---
if __name__ == "__main__":
    main_output_base_dir = os.path.join(script_dir, "output")
    os.makedirs(main_output_base_dir, exist_ok=True)
    
    all_yearly_dfs = {}

    for name, config in scenarios_config.items():
        yearly_df_for_scenario = process_scenario_data(name, config["flow_dir"], config["files"], config["capacity"])
        if yearly_df_for_scenario is not None:
            all_yearly_dfs[name] = yearly_df_for_scenario

    # Plot the yearly SOC comparison only if there's more than one scenario processed
    if len(all_yearly_dfs) > 1:
        plot_yearly_soc_comparison(all_yearly_dfs, main_output_base_dir)
    elif len(all_yearly_dfs) == 1:
        print("\nOnly one scenario processed. Yearly SOC comparison plot requires at least two scenarios.")
    else:
        print("\nNo scenarios processed. Cannot generate yearly SOC comparison plot.")

    print("\nAll battery SOC processing, CSV export, and plot generation completed.")