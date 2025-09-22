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
    """
    charge_series_wh_per_interval = charge_series_wmin / 60.0
    discharge_series_wh_per_interval = discharge_series_wmin / 60.0

    if initial_soc_wh is None:
        initial_soc_wh = 0.5 * nominal_capacity_wh

    soc_values_wh = [initial_soc_wh]
    soc_min = soc_min_frac * nominal_capacity_wh
    dt_hours_per_interval = 1 / 60.0

    for i in range(len(charge_series_wh_per_interval)):
        last_soc_wh = soc_values_wh[-1]
        loss_this_interval_wh = loss_rate * nominal_capacity_wh * dt_hours_per_interval
        current_soc_wh = last_soc_wh - loss_this_interval_wh
        charge_energy_wh = charge_series_wh_per_interval.iloc[i] * charge_eff
        discharge_energy_wh = discharge_series_wh_per_interval.iloc[i] / discharge_eff
        current_soc_wh = current_soc_wh + charge_energy_wh - discharge_energy_wh
        current_soc_wh = max(soc_min, min(nominal_capacity_wh, current_soc_wh))
        soc_values_wh.append(current_soc_wh)

    return [val / nominal_capacity_wh * 100 for val in soc_values_wh[1:]]

# --- Helper function to plot duration curves (Unchanged) ---
def export_duration_curves(df, output_dir, scenario_name, nominal_capacity):
    duration_curve_pdf_path = os.path.join(output_dir, f"SOC_Duration_Curves_{scenario_name}.pdf")
    png_files_for_zip = []
    with PdfPages(duration_curve_pdf_path) as pdf_duration_curves:
        print(f"  Generating Yearly SOC Duration Curve for {scenario_name}...")
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
def export_combined_heatmaps(df_flows, output_dir, scenario_name, charge_col, discharge_col):
    """
    Generates and saves combined heatmaps for battery power flow (charge - discharge).
    """
    heatmap_pdf_path = os.path.join(output_dir, f"Battery_Net_Power_Heatmaps_{scenario_name}.pdf")
    png_files_for_zip = []

    if charge_col not in df_flows.columns or discharge_col not in df_flows.columns:
        print(f"  Skipping heatmap generation for {scenario_name}: Battery charge/discharge data columns not found.")
        return []

    with PdfPages(heatmap_pdf_path) as pdf_heatmaps:
        for month_name in df_flows["Month"].unique():
            print(f"  Generating Combined Battery Net Power Heatmap for {scenario_name} - {month_name}...")
            month_df = df_flows[df_flows["Month"] == month_name].copy()
            
            charge_series = month_df[charge_col]
            discharge_series = month_df[discharge_col]
            
            net_power_wmin = charge_series - discharge_series
            net_power_hourly_wh = net_power_wmin.resample('H').sum() / 60.0

            hourly_data = pd.DataFrame({'Value': net_power_hourly_wh.values}, index=net_power_hourly_wh.index)
            hourly_data['hour'] = hourly_data.index.hour
            hourly_data['day'] = hourly_data.index.day
            pivot_table = hourly_data.pivot_table(index='hour', columns='day', values='Value').fillna(0)

            fig, ax = plt.subplots(figsize=(12, 12 * 13 / 21))
            max_val = pivot_table.abs().max().max()
            if max_val == 0:
                sns.heatmap(pivot_table, cmap="Greys", annot=False, fmt=".0f",
                            linewidths=.5, ax=ax, cbar=False)
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

# --- Main Processing Function (Corrected) ---
def process_scenario_data(scenario_name, flow_dir, file_dict, capacity, column_paths_map):
    print(f"\n--- Processing {scenario_name} Battery Data (Capacity: {capacity} Wh) ---")
    scenario_output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", scenario_name)
    os.makedirs(scenario_output_dir, exist_ok=True)
    all_monthly_dfs = []
    month_order = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
    
    charge_col_found = None
    discharge_col_found = None

    for month_abbr in month_order:
        filename = file_dict.get(month_abbr)
        if not filename:
            print(f"  Warning: No file defined for month '{month_abbr}' in {scenario_name}. Skipping.")
            continue
        filepath = os.path.join(flow_dir, filename)
        if not os.path.exists(filepath):
            print(f"  Warning: File not found: {filepath}. Skipping {month_abbr} for {scenario_name}.")
            continue
        try:
            results = pd.read_csv(filepath, header=[0, 1], index_col=0)
            results.index = pd.to_datetime(results.index, utc=True)
            monthly_data = pd.DataFrame(index=results.index)

            # Check for the presence of either header format for the battery columns
            if charge_col_found is None:
                 for col_pair in column_paths_map["Battery_charge"]:
                    if col_pair in results.columns:
                        charge_col_found = col_pair
                        break
            
            if discharge_col_found is None:
                for col_pair in column_paths_map["Battery_discharge"]:
                    if col_pair in results.columns:
                        discharge_col_found = col_pair
                        break
            
            # Use the found column names, or default to None if not found
            if charge_col_found and discharge_col_found:
                charge_series = results[charge_col_found].squeeze().clip(lower=0)
                discharge_series = results[discharge_col_found].squeeze().clip(lower=0)

                if capacity > 0:
                    soc_percent_values = soc(charge_series, discharge_series, results.index, nominal_capacity_wh=capacity)
                    monthly_data[f"SOC_{scenario_name}_%"] = pd.Series(soc_percent_values, index=results.index[:len(soc_percent_values)])
                else:
                    monthly_data[f"SOC_{scenario_name}_%"] = np.nan

                monthly_data[charge_col_found] = charge_series
                monthly_data[discharge_col_found] = discharge_series
            else:
                print(f"  Note: Battery flow columns not found in {filename} for {scenario_name}. SOC and heatmap will be skipped.")
                monthly_data[f"SOC_{scenario_name}_%"] = np.nan
            
            monthly_data['Month'] = month_abbr.capitalize()
            all_monthly_dfs.append(monthly_data)
            print(f"  Processed {filename} for {scenario_name}")
        except KeyError as e:
            print(f"  Error: Missing expected column in {filename} for {scenario_name}. Error: {e}")
        except Exception as e:
            print(f"  An unexpected error occurred while processing {filepath}: {e}")

    if not all_monthly_dfs:
        print(f"No data was processed for {scenario_name}. Skipping plotting and CSV export.")
        return

    yearly_df = pd.concat(all_monthly_dfs)
    output_csv_path = os.path.join(scenario_output_dir, f"Combined_Battery_Data_{scenario_name}.csv")
    yearly_df.to_csv(output_csv_path)
    print(f"Combined data for {scenario_name} exported to: {output_csv_path}")

    print(f"\n--- Generating plots for {scenario_name} ---")
    all_png_files = []

    # Check for SOC data before generating duration curves
    soc_column_name = f"SOC_{scenario_name}_%"
    if soc_column_name in yearly_df.columns and capacity > 0 and not yearly_df[soc_column_name].isnull().all():
        soc_for_duration_curves = yearly_df[[soc_column_name, 'Month']].copy()
        soc_for_duration_curves.rename(columns={soc_column_name: "SOC_%"}, inplace=True)
        all_png_files.extend(export_duration_curves(soc_for_duration_curves, scenario_output_dir, scenario_name, capacity))
    else:
        print(f"  Skipping SOC duration curves for {scenario_name}: No valid SOC data found or capacity is 0.")

    # Check for battery flow data before generating heatmaps
    if charge_col_found and discharge_col_found:
        if not (yearly_df[charge_col_found].sum() == 0 and yearly_df[discharge_col_found].sum() == 0):
            all_png_files.extend(export_combined_heatmaps(yearly_df, scenario_output_dir, scenario_name, charge_col_found, discharge_col_found))
        else:
            print(f"  Skipping heatmaps for {scenario_name}: No battery charge/discharge activity detected.")
    else:
        print(f"  Skipping heatmaps for {scenario_name}: Battery flow columns were not found.")

    if all_png_files:
        zip_path = os.path.join(scenario_output_dir, f"{scenario_name}_Plots.zip")
        with ZipFile(zip_path, 'w') as zipf:
            for file_path in all_png_files:
                if os.path.exists(file_path):
                    zipf.write(file_path, arcname=os.path.basename(file_path))
                    print(f"      Added {os.path.basename(file_path)} to zip.")
                else:
                    print(f"      Warning: PNG file not found for zipping: {file_path}")
        print(f"All plots for {scenario_name} zipped to: {zip_path}")
    else:
        print(f"No plots generated for {scenario_name} to zip.")
    
# --- Global Configuration (Unchanged) ---
script_dir = os.path.dirname(os.path.abspath(__file__))
column_paths_map = {
    "Battery_charge": [
        ("SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='distribution')", "SolphLabel(location='House1', mtress_component='storage1', solph_node='Battery_Storage')"),
        ("('House1', 'ElectricityCarrier', 'distribution')", "('House1', 'storage1', 'Battery_Storage')")
    ],
    "Battery_discharge": [
        ("SolphLabel(location='House1', mtress_component='storage1', solph_node='Battery_Storage')", "SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='distribution')"),
        ("('House1', 'storage1', 'Battery_Storage')", "('House1', 'ElectricityCarrier', 'distribution')")
    ]
}
scenarios_config = {
    "PV_NoBattery": {
        "flow_dir": os.path.join(script_dir, "flows"),
        "files": {
            'jan': 'flow_nobattery_jan23.csv', 'feb': 'flow_nobattery_feb23.csv',
            'mar': 'flow_nobattery_mar23.csv', 'apr': 'flow_nobattery_apr23.csv', 'may': 'flow_nobattery_may23.csv',
            'jun': 'flow_nobattery_jun23.csv', 'jul': 'flow_nobattery_jul23.csv', 'aug': 'flow_nobattery_aug23.csv',
            'sep': 'flow_nobattery_sep23.csv', 'oct': 'flow_nobattery_oct23.csv', 'nov': 'flow_nobattery_nov23.csv',
            'dec': 'flow_nobattery_dec23.csv'
        },
        "capacity": 0
    },
    "5kWh": {
        "flow_dir": os.path.join(script_dir, "flows"),
        "files": {
            'jan': 'flow_5k_jan23.csv', 'feb': 'flow_5k_feb23.csv',
            'mar': 'flow_5k_mar23.csv', 'apr': 'flow_5k_apr23.csv', 'may': 'flow_5k_may23.csv',
            'jun': 'flow_5k_jun23.csv', 'jul': 'flow_5k_jul23.csv', 'aug': 'flow_5k_aug23.csv',
            'sep': 'flow_5k_sep23.csv', 'oct': 'flow_5k_oct23.csv', 'nov': 'flow_5k_nov23.csv',
            'dec': 'flow_5k_dec23.csv'
        },
        "capacity": 5000
    },
    "8kWh": {
        "flow_dir": os.path.join(script_dir, "flows"),
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
        "flow_dir": os.path.join(script_dir, "flows"),
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
        "flow_dir": os.path.join(script_dir, "flows"),
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
        "flow_dir": os.path.join(script_dir, "flows"),
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
        "flow_dir": os.path.join(script_dir, "flows"),
        "files": {
            'jan': 'flow_26k_jan23.csv', 'feb': 'flow_26k_feb23.csv',
            'mar': 'flow_26k_mar23.csv', 'apr': 'flow_26k_apr23.csv', 'may': 'flow_26k_may23.csv',
            'jun': 'flow_26k_jun23.csv', 'jul': 'flow_26k_jul23.csv', 'aug': 'flow_26k_aug23.csv',
            'sep': 'flow_26k_sep23.csv', 'oct': 'flow_26k_oct23.csv', 'nov': 'flow_26k_nov23.csv',
            'dec': 'flow_26k_dec23.csv'
        },
        "capacity": 26000
    },
    "50kWh": {
        "flow_dir": os.path.join(script_dir, "flows"),
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

# --- Main Execution (Unchanged) ---
if __name__ == "__main__":
    os.makedirs(os.path.join(script_dir, "output"), exist_ok=True)
    parser = argparse.ArgumentParser(
        description="Calculate SOC and generate plots for battery energy flows.",
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
        exit(1)
    
    for name in scenarios_to_process:
        config = scenarios_config[name]
        process_scenario_data(name, config["flow_dir"], config["files"], config["capacity"], column_paths_map)
    print("\nAll battery SOC processing, CSV export, and plot generation completed for the selected scenario(s).")
    print("Check the 'output' folder for scenario-specific data and plots.")