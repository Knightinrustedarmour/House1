import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from zipfile import ZipFile
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
import argparse

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


# --- Helper function to plot duration curves (Unchanged) ---
def export_duration_curves(df, output_dir, scenario_name, nominal_capacity):
    duration_curve_pdf_path = os.path.join(output_dir, f"SOC_Duration_Curves_{scenario_name}.pdf")
    png_files_for_zip = []

    with PdfPages(duration_curve_pdf_path) as pdf_duration_curves:
        # Yearly SOC Duration Curve
        print(f"   Generating Yearly SOC Duration Curve for {scenario_name}...")
        yearly_soc_data = df.sort_values("SOC_%", ascending=False).reset_index(drop=True)
        duration_hours_yearly = np.arange(1, len(yearly_soc_data) + 1) / 60.0

        fig_yearly, ax_yearly = plt.subplots(figsize=(10, 10 * 13 / 21))
        ax_yearly.plot(duration_hours_yearly, yearly_soc_data["SOC_%"])
        ax_yearly.set_xlabel("Duration (Hours)")
        ax_yearly.set_ylabel("SOC (%)")
        ax_yearly.set_title(f"Yearly SOC Duration Curve - {scenario_name} (Nominal Capacity: {nominal_capacity / 1000:.1f} kWh)")
        ax_yearly.grid(True)
        ax_yearly.set_ylim(0, 100)
        plt.tight_layout()
        pdf_duration_curves.savefig(fig_yearly)
        png_path_yearly = os.path.join(output_dir, f"{scenario_name}_Yearly_SOC_Duration_Curve.png")
        fig_yearly.savefig(png_path_yearly, dpi=300)
        png_files_for_zip.append(png_path_yearly)
        plt.close(fig_yearly)

        # Monthly SOC Duration Curves
        for month_name in df["Month"].unique():
            print(f"   Generating Monthly SOC Duration Curve for {scenario_name} - {month_name}...")
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


# --- NEW/MODIFIED Helper function to plot combined heatmaps ---
def export_combined_heatmaps(df_flows, output_dir, scenario_name):
    """
    Generates and saves combined heatmaps for battery power flow (charge - discharge).
    df_flows should contain time-indexed Battery_charge_W_ and Battery_discharge_W_ columns
    for the specific scenario, named as f"Battery_charge_W_{scenario_name}" and
    f"Battery_discharge_W_{scenario_name}".
    """
    heatmap_pdf_path = os.path.join(output_dir, f"Battery_Net_Power_Heatmaps_{scenario_name}.pdf")
    png_files_for_zip = []

    # Check if battery columns exist for the current scenario
    charge_col = f"Battery_charge_W_{scenario_name}"
    discharge_col = f"Battery_discharge_W_{scenario_name}"

    if charge_col not in df_flows.columns or discharge_col not in df_flows.columns:
        print(f"   Skipping heatmap generation for {scenario_name}: Battery charge/discharge data columns not found.")
        return []

    with PdfPages(heatmap_pdf_path) as pdf_heatmaps:
        for month_name in df_flows["Month"].unique():
            print(f"   Generating Combined Battery Net Power Heatmap for {scenario_name} - {month_name}...")
            month_df = df_flows[df_flows["Month"] == month_name].copy()

            # Get charge and discharge series for the current month
            charge_series = month_df[charge_col]
            discharge_series = month_df[discharge_col]

            # Calculate net power: Charge (positive) - Discharge (negative)
            # Both are in Wmin, so the result is also in Wmin
            net_power_wmin = charge_series - discharge_series

            # Resample from Wmin (per minute) to Wh (per hour) for heatmaps
            # Sum Wmin over an hour (60 minutes) and then convert to Wh by dividing by 60.
            net_power_hourly_wh = net_power_wmin.resample('H').sum() / 60.0

            # Create a DataFrame for pivot
            hourly_data = pd.DataFrame({
                'Value': net_power_hourly_wh.values
            }, index=net_power_hourly_wh.index)
            hourly_data['hour'] = hourly_data.index.hour
            hourly_data['day'] = hourly_data.index.day

            # Pivot for heatmap
            pivot_table = hourly_data.pivot_table(index='hour', columns='day', values='Value').fillna(0)

            fig, ax = plt.subplots(figsize=(12, 12 * 13 / 21))

            # Define a diverging colormap suitable for positive and negative values
            max_val = pivot_table.abs().max().max()
            # Handle cases where max_val might be 0 (e.g., no battery activity)
            if max_val == 0:
                print(f"     No battery power flow data for {scenario_name} - {month_name}. Heatmap will be empty.")
                sns.heatmap(pivot_table, cmap="Greys", annot=False, fmt=".0f",
                            linewidths=.5, ax=ax, cbar=False) # Use a neutral cmap, no colorbar if all zeros
            else:
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


# --- Main Processing Function (Modified for SOC and Heatmap calls) ---
def process_scenario_data(scenario_name, flow_dir, file_dict, capacity, column_paths_map):
    print(f"\n--- Processing {scenario_name} Battery Data (Capacity: {capacity} Wh) ---")

    # Ensure output directories exist for this scenario
    scenario_output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", scenario_name)
    os.makedirs(scenario_output_dir, exist_ok=True)

    all_monthly_dfs = []
    month_order = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']

    has_battery_columns = True # Assume true, then check if 'Battery_charge' or 'Battery_discharge' are missing.
                               # This helps the 'NoBattery' case where the files might genuinely not have these columns.

    for month_abbr in month_order:
        filename = file_dict.get(month_abbr)
        if not filename:
            print(f"   Warning: No file defined for month '{month_abbr}' in {scenario_name}. Skipping.")
            continue

        filepath = os.path.join(flow_dir, filename)

        if not os.path.exists(filepath):
            print(f"   Warning: File not found: {filepath}. Skipping {month_abbr} for {scenario_name}.")
            continue

        try:
            results = pd.read_csv(filepath, header=[0, 1], index_col=0)
            results.index = pd.to_datetime(results.index, utc=True)

            monthly_data = pd.DataFrame(index=results.index)

            # Check if battery columns exist in the loaded data for the current scenario
            if column_paths_map["Battery_charge"] in results.columns and column_paths_map["Battery_discharge"] in results.columns:
                charge_series = results[[column_paths_map["Battery_charge"]]].squeeze()
                discharge_series = results[[column_paths_map["Battery_discharge"]]].squeeze()

                charge_series = charge_series.clip(lower=0)
                discharge_series = discharge_series.clip(lower=0)

                # Only calculate SOC if capacity is greater than 0
                if capacity > 0:
                    soc_percent_values = soc(
                        charge_series,
                        discharge_series,
                        results.index,
                        nominal_capacity_wh=capacity
                    )
                    monthly_data[f"SOC_{scenario_name}_%"] = pd.Series(soc_percent_values, index=results.index[:len(soc_percent_values)])
                else: # Capacity is 0 (e.g., NoBattery scenario)
                    monthly_data[f"SOC_{scenario_name}_%"] = np.nan # SOC is not applicable

                monthly_data[f"Battery_charge_W_{scenario_name}"] = charge_series
                monthly_data[f"Battery_discharge_W_{scenario_name}"] = discharge_series
            else:
                has_battery_columns = False # Set flag if columns are missing
                print(f"   Note: Battery flow columns not found in {filename} for {scenario_name}. SOC and heatmap will be skipped.")
                monthly_data[f"Battery_charge_W_{scenario_name}"] = 0.0
                monthly_data[f"Battery_discharge_W_{scenario_name}"] = 0.0
                monthly_data[f"SOC_{scenario_name}_%"] = np.nan

            monthly_data['Month'] = month_abbr.capitalize()
            all_monthly_dfs.append(monthly_data)

            print(f"   Processed {filename} for {scenario_name}")

        except KeyError as e:
            print(f"   Error: Missing expected column in {filename} for {scenario_name}. Error: {e}")
            has_battery_columns = False # Treat as if columns were missing
        except Exception as e:
            print(f"   An unexpected error occurred while processing {filepath}: {e}")
            has_battery_columns = False # Treat as if columns were missing

    if not all_monthly_dfs:
        print(f"No data was processed for {scenario_name}. Skipping plotting and CSV export.")
        return

    yearly_df = pd.concat(all_monthly_dfs)

    output_csv_path = os.path.join(scenario_output_dir, f"Combined_Battery_Data_{scenario_name}.csv")
    yearly_df.to_csv(output_csv_path)
    print(f"Combined data for {scenario_name} exported to: {output_csv_path}")

    # Generate plots only if capacity > 0 AND battery columns were found
    print(f"\n--- Generating plots for {scenario_name} ---")
    all_png_files = []

    if capacity > 0 and has_battery_columns:
        # Only generate SOC duration curves if SOC data is present and not all NaN
        if f"SOC_{scenario_name}_%" in yearly_df.columns and not yearly_df[f"SOC_{scenario_name}_%"].isnull().all():
            soc_for_duration_curves = yearly_df[[f"SOC_{scenario_name}_%", 'Month']].copy()
            soc_for_duration_curves.rename(columns={f"SOC_{scenario_name}_%": "SOC_%"}, inplace=True)
            all_png_files.extend(export_duration_curves(soc_for_duration_curves, scenario_output_dir, scenario_name, capacity))
        else:
            print(f"   Skipping SOC duration curves for {scenario_name}: No valid SOC data found (e.g., all NaNs).")

        # Only generate heatmaps if battery flow data has actual activity
        if not (yearly_df[f"Battery_charge_W_{scenario_name}"].sum() == 0 and yearly_df[f"Battery_discharge_W_{scenario_name}"].sum() == 0):
            all_png_files.extend(export_combined_heatmaps(yearly_df, scenario_output_dir, scenario_name))
        else:
            print(f"   Skipping heatmaps for {scenario_name}: No battery charge/discharge activity detected.")
    else:
        print(f"   Skipping all plots for {scenario_name}: Battery capacity is 0 Wh or battery flow columns were not found.")

    # Create a zip archive of all generated PNGs for the scenario
    if all_png_files:
        zip_path = os.path.join(scenario_output_dir, f"{scenario_name}_Plots.zip")
        with ZipFile(zip_path, 'w') as zipf:
            for file_path in all_png_files:
                if os.path.exists(file_path):
                    zipf.write(file_path, arcname=os.path.basename(file_path))
                    print(f"     Added {os.path.basename(file_path)} to zip.")
                else:
                    print(f"     Warning: PNG file not found for zipping: {file_path}")
        print(f"All plots for {scenario_name} zipped to: {zip_path}")
    else:
        print(f"No plots generated for {scenario_name} to zip.")


# --- Global Configuration (Updated with 50kWh scenario) ---
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
    "NoBattery": {
        "flow_dir": os.path.join(script_dir, "flows_nobattery"),
        "files": {
            'jan': 'flow_NB_jan23.csv', 'feb': 'flow_NB_feb23.csv',
            'mar': 'flow_NB_mar23.csv', 'apr': 'flow_NB_apr23.csv', 'may': 'flow_NB_may23.csv',
            'jun': 'flow_NB_jun23.csv', 'jul': 'flow_NB_jul23.csv', 'aug': 'flow_NB_aug23.csv',
            'sep': 'flow_NB_sep23.csv', 'oct': 'flow_NB_oct23.csv', 'nov': 'flow_NB_nov23.csv',
            'dec': 'flow_NB_dec23.csv'
        },
        "capacity": 0 # Explicitly 0 for no battery
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
    },
    "12kWh": {
        "flow_dir": os.path.join(script_dir, "flows_12k"),
        "files": {
            'jan': 'flow_12k_jan23.csv', 'feb': 'flow_12k_feb23.csv',
            'mar': 'flow_12k_mar23.csv', 'apr': 'flow_12k_apr23.csv', 'may': 'flow_12k_may23.csv',
            'jun': 'flow_12k_jun23.csv', 'jul': 'flow_12k_jul23.csv', 'aug': 'flow_12k_aug23.csv',
            'sep': 'flow_12k_sep23.csv', 'oct': 'flow_12k_oct23.csv', 'nov': 'flow_12k_nov23.csv',
            'dec': 'flow_12k_dec23.csv'
        },
        "capacity": 12000
    },
    "15kWh": {
        "flow_dir": os.path.join(script_dir, "flows_15k"),
        "files": {
            'jan': 'flow_15k_jan23.csv', 'feb': 'flow_15k_feb23.csv',
            'mar': 'flow_15k_mar23.csv', 'apr': 'flow_15k_apr23.csv', 'may': 'flow_15k_may23.csv',
            'jun': 'flow_15k_jun23.csv', 'jul': 'flow_15k_jul23.csv', 'aug': 'flow_15k_aug23.csv',
            'sep': 'flow_15k_sep23.csv', 'oct': 'flow_15k_oct23.csv', 'nov': 'flow_15k_nov23.csv',
            'dec': 'flow_15k_dec23.csv'
        },
        "capacity": 15000
    },
    "20kWh": {
        "flow_dir": os.path.join(script_dir, "flows_20k"),
        "files": {
            'jan': 'flow_20k_jan23.csv', 'feb': 'flow_20k_feb23.csv',
            'mar': 'flow_20k_mar23.csv', 'apr': 'flow_20k_apr23.csv', 'may': 'flow_20k_may23.csv',
            'jun': 'flow_20k_jun23.csv', 'jul': 'flow_20k_jul23.csv', 'aug': 'flow_20k_aug23.csv',
            'sep': 'flow_20k_sep23.csv', 'oct': 'flow_20k_oct23.csv', 'nov': 'flow_20k_nov23.csv',
            'dec': 'flow_20k_dec23.csv'
        },
        "capacity": 20000
    },
    "26kWh": {
        "flow_dir": os.path.join(script_dir, "flows_26k"),
        "files": {
            'jan': 'flow_26k_jan23.csv', 'feb': 'flow_26k_feb23.csv',
            'mar': 'flow_26k_mar23.csv', 'apr': 'flow_26k_apr23.csv', 'may': 'flow_26k_may23.csv',
            'jun': 'flow_26k_jun23.csv', 'jul': 'flow_26k_jul23.csv', 'aug': 'flow_26k_aug23.csv',
            'sep': 'flow_26k_sep23.csv', 'oct': 'flow_26k_oct23.csv', 'nov': 'flow_26k_nov23.csv',
            'dec': 'flow_26k_dec23.csv'
        },
        "capacity": 26000
    },
    # --- NEW: 50kWh Scenario ---
    "50kWh": {
        "flow_dir": os.path.join(script_dir, "flows_50k"), # Make sure this folder exists
        "files": {
            'jan': 'flow_50k_jan23.csv', 'feb': 'flow_50k_feb23.csv',
            'mar': 'flow_50k_mar23.csv', 'apr': 'flow_50k_apr23.csv', 'may': 'flow_50k_may23.csv',
            'jun': 'flow_50k_jun23.csv', 'jul': 'flow_50k_jul23.csv', 'aug': 'flow_50k_aug23.csv',
            'sep': 'flow_50k_sep23.csv', 'oct': 'flow_50k_oct23.csv', 'nov': 'flow_50k_nov23.csv',
            'dec': 'flow_50k_dec23.csv'
        },
        "capacity": 50000
    }
}


# --- Main Execution ---
if __name__ == "__main__":
    os.makedirs(os.path.join(script_dir, "output"), exist_ok=True)

    parser = argparse.ArgumentParser(
        description="Calculate SOC and generate heatmaps for battery energy flows.",
        formatter_class=argparse.RawTextHelpFormatter
    )

    available_scenario_names = sorted(list(scenarios_config.keys()))

    parser.add_argument(
        '--scenario',
        type=str,
        choices=available_scenario_names + ['all'],
        help=f"Specify the scenario to analyze and plot battery data.\n"
             f"Choose from: {', '.join(available_scenario_names)}\n"
             f"Use 'all' to process all defined scenarios (default).",
        default='all'
    )
    args = parser.parse_args()

    scenarios_to_process = []
    if args.scenario == 'all':
        scenarios_to_process = available_scenario_names
        print("Processing all defined scenarios...")
    elif args.scenario in scenarios_config:
        scenarios_to_process = [args.scenario]
        print(f"Processing only the '{args.scenario}' scenario...")
    else:
        print(f"Error: Scenario '{args.scenario}' not recognized. Please choose from {available_scenario_names} or 'all'.")
        exit(1) # Exit with an error code

    for name in scenarios_to_process:
        config = scenarios_config[name]
        # Always call process_scenario_data for all scenarios.
        # Inside process_scenario_data, it will decide whether to calculate SOC and generate plots
        # based on the 'capacity' and the actual presence of battery columns.
        process_scenario_data(name, config["flow_dir"], config["files"], config["capacity"], column_paths)

    print("\nAll battery SOC processing, CSV export, and plot generation completed for the selected scenario(s).")
    print("Check the 'output' folder for scenario-specific data and plots.")