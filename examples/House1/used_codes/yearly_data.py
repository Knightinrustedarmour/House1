import os
import pandas as pd
import argparse # Import argparse

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Define input and output directories for all scenarios
flows_dir_5k_battery = os.path.join(script_dir, "flows")
flows_dir_nobattery = os.path.join(script_dir, "flows_nobattery")
flows_dir_8k_battery = os.path.join(script_dir, "flows_8k")
flows_dir_12k_battery = os.path.join(script_dir, "flows_12k")
flows_dir_15k_battery = os.path.join(script_dir, "flows_15k")
flows_dir_20k_battery = os.path.join(script_dir, "flows_20k")
flows_dir_26k_battery = os.path.join(script_dir, "flows_26k")
flows_dir_50k_battery = os.path.join(script_dir, "flows_50k") # 50kWh battery scenario

output_dir = os.path.join(script_dir, "output")
os.makedirs(output_dir, exist_ok=True) # Create 'output' directory if it doesn't exist

# Define the target CSV files for all scenarios (all months)
target_files_5k_battery = {
    'jan': 'flow_W_jan23.csv', 'feb': 'flow_W_feb23.csv',
    'mar': 'flow_W_mar23.csv', 'apr': 'flow_W_apr23.csv', 'may': 'flow_W_may23.csv',
    'jun': 'flow_W_jun23.csv', 'jul': 'flow_W_jul23.csv', 'aug': 'flow_W_aug23.csv',
    'sep': 'flow_W_sep23.csv', 'oct': 'flow_W_oct23.csv', 'nov': 'flow_W_nov23.csv',
    'dec': 'flow_W_dec23.csv'
}

target_files_nobattery = {
    'jan': 'flow_NB_jan23.csv', 'feb': 'flow_NB_feb23.csv',
    'mar': 'flow_NB_mar23.csv', 'apr': 'flow_NB_apr23.csv', 'may': 'flow_NB_may23.csv',
    'jun': 'flow_NB_jun23.csv', 'jul': 'flow_NB_jul23.csv', 'aug': 'flow_NB_aug23.csv',
    'sep': 'flow_NB_sep23.csv', 'oct': 'flow_NB_oct23.csv', 'nov': 'flow_NB_nov23.csv',
    'dec': 'flow_NB_dec23.csv'
}

target_files_8k_battery = {
    'jan': 'flow_8k_jan23.csv', 'feb': 'flow_8k_feb23.csv',
    'mar': 'flow_8k_mar23.csv', 'apr': 'flow_8k_apr23.csv', 'may': 'flow_8k_may23.csv',
    'jun': 'flow_8k_jun23.csv', 'jul': 'flow_8k_jul23.csv', 'aug': 'flow_8k_aug23.csv',
    'sep': 'flow_8k_sep23.csv', 'oct': 'flow_8k_oct23.csv', 'nov': 'flow_8k_nov23.csv',
    'dec': 'flow_8k_dec23.csv'
}

target_files_12k_battery = {
    'jan': 'flow_12k_jan23.csv', 'feb': 'flow_12k_feb23.csv',
    'mar': 'flow_12k_mar23.csv', 'apr': 'flow_12k_apr23.csv', 'may': 'flow_12k_may23.csv',
    'jun': 'flow_12k_jun23.csv', 'jul': 'flow_12k_jul23.csv', 'aug': 'flow_12k_aug23.csv',
    'sep': 'flow_12k_sep23.csv', 'oct': 'flow_12k_oct23.csv', 'nov': 'flow_12k_nov23.csv',
    'dec': 'flow_12k_dec23.csv'
}

target_files_15k_battery = {
    'jan': 'flow_15k_jan23.csv', 'feb': 'flow_15k_feb23.csv',
    'mar': 'flow_15k_mar23.csv', 'apr': 'flow_15k_apr23.csv', 'may': 'flow_15k_may23.csv',
    'jun': 'flow_15k_jun23.csv', 'jul': 'flow_15k_jul23.csv', 'aug': 'flow_15k_aug23.csv',
    'sep': 'flow_15k_sep23.csv', 'oct': 'flow_15k_oct23.csv', 'nov': 'flow_15k_nov23.csv',
    'dec': 'flow_15k_dec23.csv'
}

target_files_20k_battery = {
    'jan': 'flow_20k_jan23.csv', 'feb': 'flow_20k_feb23.csv',
    'mar': 'flow_20k_mar23.csv', 'apr': 'flow_20k_apr23.csv', 'may': 'flow_20k_may23.csv',
    'jun': 'flow_20k_jun23.csv', 'jul': 'flow_20k_jul23.csv', 'aug': 'flow_20k_aug23.csv',
    'sep': 'flow_20k_sep23.csv', 'oct': 'flow_20k_oct23.csv', 'nov': 'flow_20k_nov23.csv',
    'dec': 'flow_20k_dec23.csv'
}

target_files_26k_battery = {
    'jan': 'flow_26k_jan23.csv', 'feb': 'flow_26k_feb23.csv',
    'mar': 'flow_26k_mar23.csv', 'apr': 'flow_26k_apr23.csv', 'may': 'flow_26k_may23.csv',
    'jun': 'flow_26k_jun23.csv', 'jul': 'flow_26k_jul23.csv', 'aug': 'flow_26k_aug23.csv',
    'sep': 'flow_26k_sep23.csv', 'oct': 'flow_26k_oct23.csv', 'nov': 'flow_26k_nov23.csv',
    'dec': 'flow_26k_dec23.csv'
}

target_files_50k_battery = {
    'jan': 'flow_50k_jan23.csv', 'feb': 'flow_50k_feb23.csv',
    'mar': 'flow_50k_mar23.csv', 'apr': 'flow_50k_apr23.csv', 'may': 'flow_50k_may23.csv',
    'jun': 'flow_50k_jun23.csv', 'jul': 'flow_50k_jul23.csv', 'aug': 'flow_50k_aug23.csv',
    'sep': 'flow_50k_sep23.csv', 'oct': 'flow_50k_oct23.csv', 'nov': 'flow_50k_nov23.csv',
    'dec': 'flow_50k_dec23.csv'
}


column_paths = {
    "Battery_charge": ("SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='distribution')", "SolphLabel(location='House1', mtress_component='storage1', solph_node='Battery_Storage')"),
    "Battery_discharge": ("SolphLabel(location='House1', mtress_component='storage1', solph_node='Battery_Storage')", "SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='distribution')"),
    "PV_production": ("SolphLabel(location='House1', mtress_component='PV', solph_node='source')", "SolphLabel(location='House1', mtress_component='PV', solph_node='connection')"),
    "PV_distribution": ("SolphLabel(location='House1', mtress_component='PV', solph_node='connection')", "SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='distribution')"),
    "Demand2": ("SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='distribution')", "SolphLabel(location='House1', mtress_component='demand', solph_node='input')"),
    "Grid_import": ("SolphLabel(location='House1', mtress_component='ElectricityGridConnection', solph_node='grid_import')", "SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='distribution')"),
    "Grid_export": ("SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='feed_in')", "SolphLabel(location='House1', mtress_component='ElectricityGridConnection', solph_node='grid_export')")
}

# Conversion factor from Watt-minutes (Wmin) to KiloWatt-hours (kWh)
WATT_MIN_TO_KWH = 1 / 60000

# Function to perform the analysis for a given scenario
def analyze_scenario(scenario_identifier, flows_directory, target_files_dict, display_name, has_battery=True):
    print(f"\n{'='*60}")
    print(f"         ANALYSIS FOR SCENARIO: {display_name.upper()}         ")
    print(f"{'='*60}\n")

    monthly_dataframes = {}
    for month_abbr, filename in target_files_dict.items():
        filepath = os.path.join(flows_directory, filename)
        try:
            results = pd.read_csv(filepath, header=[0, 1], index_col=0)
            df = pd.DataFrame()

            for col_name, col_path in column_paths.items():
                if "Battery" in col_name and not has_battery:
                    df[col_name] = 0.0 # Explicitly set to zero for no-battery scenario
                elif col_path in results.columns:
                    df[col_name] = results[[col_path]].squeeze()
                else:
                    print(f"    Warning: Column '{col_name}' with path {col_path} not found in {filename} for {display_name}. Filling with zeros.")
                    df[col_name] = 0.0

            df.index = pd.to_datetime(df.index, utc=True)
            monthly_dataframes[month_abbr] = df

        except FileNotFoundError:
            print(f"Error: File not found: {filename} for {display_name}. Skipping this month.")

    monthly_summary = {}
    sorted_month_abbrs = list(target_files_dict.keys()) # Ensure chronological order

    for month_abbr in sorted_month_abbrs:
        if month_abbr in monthly_dataframes:
            df = monthly_dataframes[month_abbr]

            total_demand_wmin = df["Demand2"].sum()
            total_pv_production_wmin = df["PV_production"].sum()
            total_pv_distribution_wmin = df["PV_distribution"].sum()
            total_grid_import_wmin = df["Grid_import"].sum()
            total_grid_export_wmin = df["Grid_export"].sum()
            total_battery_charge_wmin = df["Battery_charge"].sum() if has_battery else 0.0
            total_battery_discharge_wmin = df["Battery_discharge"].sum() if has_battery else 0.0

            # Convert Wmin to kWh
            total_demand_kwh = total_demand_wmin * WATT_MIN_TO_KWH
            total_pv_production_kwh = total_pv_production_wmin * WATT_MIN_TO_KWH
            total_pv_distribution_kwh = total_pv_distribution_wmin * WATT_MIN_TO_KWH
            total_grid_import_kwh = total_grid_import_wmin * WATT_MIN_TO_KWH
            total_grid_export_kwh = total_grid_export_wmin * WATT_MIN_TO_KWH
            total_battery_charge_kwh = total_battery_charge_wmin * WATT_MIN_TO_KWH
            total_battery_discharge_kwh = total_battery_discharge_wmin * WATT_MIN_TO_KWH

            # PV Self-Consumption: Directly from PV_distribution, no clipping
            pv_self_consumption_kwh = total_pv_distribution_kwh

            # Self-Sufficiency: No clipping applied
            # For this context, assuming self-sufficiency is (total demand - grid import) makes most sense
            self_sufficiency_kwh = total_demand_kwh - total_grid_import_kwh


            monthly_data_row = {
                "Demand (kWh)": total_demand_kwh,
                "PV Production (kWh)": total_pv_production_kwh,
                "Grid Import (kWh)": total_grid_import_kwh,
                "Grid Export (kWh)": total_grid_export_kwh,
                "PV Self-Consumption (kWh)": pv_self_consumption_kwh,
                "Self-Sufficiency (kWh)": self_sufficiency_kwh,
                "Self-Consumption Rate (%)": (pv_self_consumption_kwh / total_pv_production_kwh * 100) if total_pv_production_kwh > 0 else 0,
                "Self-Sufficiency Rate (%)": (self_sufficiency_kwh / total_demand_kwh * 100) if total_demand_kwh > 0 else 0
            }
            if has_battery:
                monthly_data_row["Battery Charge (kWh)"] = total_battery_charge_kwh
                monthly_data_row["Battery Discharge (kWh)"] = total_battery_discharge_kwh

            monthly_summary[month_abbr] = monthly_data_row

    summary_df = pd.DataFrame.from_dict(monthly_summary, orient='index').reindex(sorted_month_abbrs)
    summary_df.index.name = "Month"

    print(f"\n--- MONTHLY ENERGY FLOW SUMMARY ({display_name.upper()}) ---")
    print(f"        (All values in KiloWatt-hours)        \n")
    print(summary_df.to_string(float_format="%.2f") + "\n")

    print(f"\n--- TOTAL ENERGY FLOW SUMMARY (Jan-Dec, {display_name.upper()}) ---")
    print(f"        (All values in KiloWatt-hours)        \n")

    total_demand_period_kwh = sum(data["Demand (kWh)"] for data in monthly_summary.values())
    total_pv_production_period_kwh = sum(data["PV Production (kWh)"] for data in monthly_summary.values())
    total_grid_import_period_kwh = sum(data["Grid Import (kWh)"] for data in monthly_summary.values())
    total_grid_export_period_kwh = sum(data["Grid Export (kWh)"] for data in monthly_summary.values())

    total_battery_charge_period_kwh = sum(data.get("Battery Charge (kWh)", 0.0) for data in monthly_summary.values())
    total_battery_discharge_period_kwh = sum(data.get("Battery Discharge (kWh)", 0.0) for data in monthly_summary.values())

    total_pv_self_consumption_period_kwh = sum(data["PV Self-Consumption (kWh)"] for data in monthly_summary.values())
    total_self_sufficiency_period_kwh = total_demand_period_kwh - total_grid_import_kwh

    print(f"Total Period Demand:           {total_demand_period_kwh:.2f} kWh")
    print(f"Total Period PV Production:    {total_pv_production_period_kwh:.2f} kWh")
    print(f"Total Period Grid Import:      {total_grid_import_period_kwh:.2f} kWh")
    print(f"Total Period Grid Export:      {total_grid_export_period_kwh:.2f} kWh")
    if has_battery:
        print(f"Total Period Battery Charge: {total_battery_charge_period_kwh:.2f} kWh")
        print(f"Total Period Battery Discharge: {total_battery_discharge_period_kwh:.2f} kWh")
    print(f"Total Period PV Self-Consumption: {total_pv_self_consumption_period_kwh:.2f} kWh")
    print(f"Total Period Self-Sufficiency: {total_self_sufficiency_period_kwh:.2f} kWh")


    overall_self_consumption_rate = (total_pv_self_consumption_period_kwh / total_pv_production_period_kwh * 100) if total_pv_production_period_kwh > 0 else 0
    overall_self_sufficiency_rate = (total_self_sufficiency_period_kwh / total_demand_period_kwh * 100) if total_demand_period_kwh > 0 else 0

    print(f"\nOverall Self-Consumption Rate: {overall_self_consumption_rate:.2f}%")
    print(f"Overall Self-Sufficiency Rate: {overall_self_sufficiency_rate:.2f}%")

    print(f"\n{'='*60}\n")

    # --- Save to CSV ---
    # Filenames based on scenario identifier and kWh unit
    monthly_csv_filename = f"monthly_energy_summary_2023_{scenario_identifier}_kWh.csv"
    yearly_csv_filename = f"yearly_energy_summary_2023_{scenario_identifier}_kWh.csv"

    monthly_summary_csv_path = os.path.join(output_dir, monthly_csv_filename)
    summary_df.to_csv(monthly_summary_csv_path, float_format="%.2f")
    print(f"Monthly energy summary saved to: {monthly_summary_csv_path}")

    yearly_metrics = [
        "Total Period Demand (kWh)",
        "Total Period PV Production (kWh)",
        "Total Period Grid Import (kWh)",
        "Total Period Grid Export (kWh)",
        "Total Period PV Self-Consumption (kWh)",
        "Total Period Self-Sufficiency (kWh)",
        "Overall Self-Consumption Rate (%)",
        "Overall Self-Sufficiency Rate (%)"
    ]
    yearly_values = [
        total_demand_period_kwh,
        total_pv_production_period_kwh,
        total_grid_import_period_kwh,
        total_grid_export_period_kwh,
        total_pv_self_consumption_period_kwh,
        total_self_sufficiency_period_kwh,
        overall_self_consumption_rate,
        overall_self_sufficiency_rate
    ]

    if has_battery:
        yearly_metrics.insert(4, "Total Period Battery Charge (kWh)")
        yearly_values.insert(4, total_battery_charge_period_kwh)
        yearly_metrics.insert(5, "Total Period Battery Discharge (kWh)")
        yearly_values.insert(5, total_battery_discharge_period_kwh)


    yearly_summary_data = {
        "Metric": yearly_metrics,
        "Value": yearly_values
    }
    yearly_summary_df = pd.DataFrame(yearly_summary_data)
    yearly_summary_df.set_index("Metric", inplace=True)

    yearly_summary_csv_path = os.path.join(output_dir, yearly_csv_filename)
    yearly_summary_df.to_csv(yearly_summary_csv_path, float_format="%.2f")
    print(f"Yearly energy summary saved to: {yearly_summary_csv_path}")
    return summary_df, yearly_summary_df


# --- CENTRAL SCENARIO CONFIGURATION ---
# This dictionary maps simple scenario names to their full analysis parameters.
# Add or remove scenarios here as needed.
scenario_definitions = {
    "5kWh": {
        "identifier": "battery_5k",
        "flows_dir": flows_dir_5k_battery,
        "target_files": target_files_5k_battery,
        "display_name": "Battery (5kWh)",
        "has_battery": True
    },
    "NoBattery": {
        "identifier": "nobattery",
        "flows_dir": flows_dir_nobattery,
        "target_files": target_files_nobattery,
        "display_name": "No Battery",
        "has_battery": False
    },
    "8kWh": {
        "identifier": "battery_8k",
        "flows_dir": flows_dir_8k_battery,
        "target_files": target_files_8k_battery,
        "display_name": "Battery (8kWh)",
        "has_battery": True
    },
    "12kWh": {
        "identifier": "battery_12k",
        "flows_dir": flows_dir_12k_battery,
        "target_files": target_files_12k_battery,
        "display_name": "Battery (12kWh)",
        "has_battery": True
    },
    "15kWh": {
        "identifier": "battery_15k",
        "flows_dir": flows_dir_15k_battery,
        "target_files": target_files_15k_battery,
        "display_name": "Battery (15kWh)",
        "has_battery": True
    },
    "20kWh": {
        "identifier": "battery_20k",
        "flows_dir": flows_dir_20k_battery,
        "target_files": target_files_20k_battery,
        "display_name": "Battery (20kWh)",
        "has_battery": True
    },
    "26kWh": {
        "identifier": "battery_26k",
        "flows_dir": flows_dir_26k_battery,
        "target_files": target_files_26k_battery,
        "display_name": "Battery (26kWh)",
        "has_battery": True
    },
    "50kWh": { # NEW 50kWh entry
        "identifier": "battery_50k",
        "flows_dir": flows_dir_50k_battery,
        "target_files": target_files_50k_battery,
        "display_name": "Battery (50kWh)",
        "has_battery": True
    }
}


if __name__ == "__main__":
    # --- Argument Parsing ---
    parser = argparse.ArgumentParser(
        description="Analyze energy flows for specific or all battery scenarios.",
        formatter_class=argparse.RawTextHelpFormatter # For better help message formatting
    )
    
    # Get available scenario names for choices, sorted for clarity
    available_scenarios = sorted(list(scenario_definitions.keys()))
    
    parser.add_argument(
        '--scenario',
        type=str,
        choices=available_scenarios + ['all'], # Allow selecting 'all' or specific scenarios
        help=f"Specify the scenario to analyze.\n"
             f"Choose from: {', '.join(available_scenarios)}\n"
             f"Use 'all' to run analysis for all scenarios (default).",
        default='all' # Default to 'all' if no argument is given
    )
    args = parser.parse_args()

    # --- Conditional Execution ---
    if args.scenario == 'all':
        print("Analyzing all scenarios...")
        for scenario_name, params in scenario_definitions.items():
            # Ensure output directory for each scenario exists
            scenario_output_path = os.path.join(output_dir, params["identifier"])
            os.makedirs(scenario_output_path, exist_ok=True)
            analyze_scenario(
                params["identifier"],
                params["flows_dir"],
                params["target_files"],
                params["display_name"],
                params["has_battery"]
            )
    else:
        # Check if the chosen scenario exists in our definitions
        if args.scenario in scenario_definitions:
            params = scenario_definitions[args.scenario]
            print(f"Analyzing only the '{args.scenario}' scenario...")
            # Ensure output directory for the selected scenario exists
            scenario_output_path = os.path.join(output_dir, params["identifier"])
            os.makedirs(scenario_output_path, exist_ok=True)
            analyze_scenario(
                params["identifier"],
                params["flows_dir"],
                params["target_files"],
                params["display_name"],
                params["has_battery"]
            )
        else:
            print(f"Error: Scenario '{args.scenario}' not recognized. Please choose from {available_scenarios} or 'all'.")

    print("\nAnalysis execution complete.")