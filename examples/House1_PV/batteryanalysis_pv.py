import os
import pandas as pd
import numpy as np
import argparse
import traceback

# --- 1. SOC Calculation Function ---
def soc(charge_series_wmin, discharge_series_wmin, index,
        nominal_capacity_wh=5000, charge_eff=0.96, discharge_eff=0.96,
        loss_rate=0.0005, initial_soc_wh=None, soc_min_frac=0.1):
    """
    Calculates the State of Charge (SOC) of a battery over time.
    Assumes charge_series_wmin and discharge_series_wmin are in Watt-minutes (Wmin) per 1-minute interval.
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


# --- Helper Function to Find Correct Column Path in MultiIndex DataFrame ---
def find_column_name(results_columns, potential_paths):
    """
    Finds the correct multi-index column tuple from the available ones by checking both 
    tuple and string representations.
    """
    for path in potential_paths:
        # Check if the tuple (path) exists in the DataFrame columns
        if path in results_columns:
            return path
        # Also check if the string representation of the tuple exists
        if str(path) in results_columns:
            return str(path)
    return None


# --- Main Processing Function ---
def process_scenario_data(scenario_name, flow_dir, file_dict, capacity, column_paths_map):
    print(f"\n--- Processing {scenario_name} Battery Data (Capacity: {capacity} Wh) ---")

    # Ensure output directories exist for this scenario
    # Using a reliable method to get the script's directory for absolute pathing
    script_dir = os.path.dirname(os.path.abspath(__file__))
    scenario_output_dir = os.path.join(script_dir, "output", scenario_name)
    os.makedirs(scenario_output_dir, exist_ok=True)

    all_monthly_dfs = []
    month_order = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']

    has_battery_columns = True
    charge_col_name = None
    discharge_col_name = None

    # --- Step 1: Find the correct column names from the first available file ---
    first_file_path = None
    for month_abbr in month_order:
        filename = file_dict.get(month_abbr)
        if filename:
            first_file_path = os.path.join(flow_dir, filename)
            if os.path.exists(first_file_path):
                break
    
    if first_file_path:
        try:
            temp_df = pd.read_csv(first_file_path, header=[0, 1], index_col=0)
            charge_col_name = find_column_name(temp_df.columns, column_paths_map["Battery_Charge"])
            discharge_col_name = find_column_name(temp_df.columns, column_paths_map["Battery_Discharge"])
            
            if not charge_col_name or not discharge_col_name:
                has_battery_columns = False
                print(f"    ERROR: Required battery flow columns not found in {os.path.basename(first_file_path)}.")
                print(f"    Available columns are: {list(temp_df.columns)}")
                print("    --- Please check the expected paths against the available columns ---")
                
        except Exception as e:
            print(f"    ERROR reading first file for column check ({os.path.basename(first_file_path)}): {e}")
            has_battery_columns = False
    
    # If we couldn't find the file or the columns, we can't proceed with SOC calculation
    if not has_battery_columns and capacity > 0:
         print(f"    Skipping SOC calculation for {scenario_name} due to missing input columns.")

    # --- Step 2: Process all monthly files ---
    for month_abbr in month_order:
        filename = file_dict.get(month_abbr)
        if not filename:
            continue

        filepath = os.path.join(flow_dir, filename)

        if not os.path.exists(filepath):
            print(f"    Warning: File not found: {filepath}. Skipping {month_abbr} for {scenario_name}.")
            continue

        try:
            results = pd.read_csv(filepath, header=[0, 1], index_col=0)
            # Ensure the index is datetime for consistency
            try:
                results.index = pd.to_datetime(results.index, utc=True)
            except Exception as e:
                print(f"    Warning: Could not convert index to datetime in {filename}: {e}")
                
            monthly_data = pd.DataFrame(index=results.index)

            if has_battery_columns and capacity > 0 and charge_col_name and discharge_col_name:
                
                # Use the column names identified in Step 1
                charge_series = results[charge_col_name].squeeze()
                discharge_series = results[discharge_col_name].squeeze()

                # Ensure flows are non-negative
                charge_series = charge_series.clip(lower=0)
                discharge_series = discharge_series.clip(lower=0)

                # Calculate SOC
                soc_percent_values = soc(
                    charge_series,
                    discharge_series,
                    results.index,
                    nominal_capacity_wh=capacity
                )
                
                # Check for length mismatch before assigning
                data_index = results.index[:len(soc_percent_values)]
                if len(data_index) == len(soc_percent_values):
                    monthly_data[f"SOC_{scenario_name}_%"] = pd.Series(soc_percent_values, index=data_index)
                else:
                    # Should not happen if SOC function is correct, but safe check
                    print(f"    Warning: Length mismatch in {filename}. Skipping SOC calculation.")
                    monthly_data[f"SOC_{scenario_name}_%"] = np.nan

                monthly_data[f"Battery_charge_W_{scenario_name}"] = charge_series
                monthly_data[f"Battery_discharge_W_{scenario_name}"] = discharge_series
            
            else:
                # Case for NoBattery or scenario where required columns are legitimately missing
                monthly_data[f"Battery_charge_W_{scenario_name}"] = 0.0
                monthly_data[f"Battery_discharge_W_{scenario_name}"] = 0.0
                monthly_data[f"SOC_{scenario_name}_%"] = np.nan
                # If capacity is 0, this is expected behavior.
                if capacity > 0:
                    print(f"    Note: No SOC or flow data calculated for {scenario_name}-{month_abbr}.")

            monthly_data['Month'] = month_abbr.capitalize()
            all_monthly_dfs.append(monthly_data)

            print(f"    Processed {filename}")

        except Exception as e:
            print(f"    An unexpected error occurred while processing {filepath}: {e}")
            traceback.print_exc() 

    if not all_monthly_dfs:
        print(f"No valid data was processed for {scenario_name}. Skipping CSV export.")
        return

    # --- Step 3: Combine and Export Data ---
    yearly_df = pd.concat(all_monthly_dfs)

    output_csv_path = os.path.join(scenario_output_dir, f"Combined_Battery_Data_{scenario_name}.csv")
    yearly_df.to_csv(output_csv_path)
    print(f"\nCombined data for {scenario_name} exported to: {output_csv_path}")

    print(f"--- Skipping all plots for {scenario_name} as requested. ---")


# --- Global Configuration ---
# Setting script_dir here ensures it's available for global use
script_dir = os.path.dirname(os.path.abspath(__file__))

column_paths = {
    # Provide ALL known possible formats for the multi-index column header here
    # The find_column_name function will select the correct one from the list.
    "Battery_Charge": [
            ("SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='distribution')", "SolphLabel(location='House1', mtress_component='storage1', solph_node='Battery_Storage')"),
            ("('House1', 'ElectricityCarrier', 'distribution')", "('House1', 'storage1', 'Battery_Storage')"),
            # Add any other observed formats here if the script fails again.
        ],
    "Battery_Discharge": [
            ("SolphLabel(location='House1', mtress_component='storage1', solph_node='Battery_Storage')", "SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='distribution')"),
            ("('House1', 'storage1', 'Battery_Storage')", "('House1', 'ElectricityCarrier', 'distribution')"),
            # Add any other observed formats here if the script fails again.
        ]
}

scenarios_config = {
    "5kWh": {
        "flow_dir": os.path.join(script_dir, "flows"),
        "files": {
            'jan': 'flow_5k_jan23.csv', 'feb': 'flow_5k_feb23.csv', 'mar': 'flow_5k_mar23.csv', 
            'apr': 'flow_5k_apr23.csv', 'may': 'flow_5k_may23.csv', 'jun': 'flow_5k_jun23.csv', 
            'jul': 'flow_5k_jul23.csv', 'aug': 'flow_5k_aug23.csv', 'sep': 'flow_5k_sep23.csv', 
            'oct': 'flow_5k_oct23.csv', 'nov': 'flow_5k_nov23.csv', 'dec': 'flow_5k_dec23.csv'
        },
        "capacity": 5000
    },
    
    
    "8kWh": {
        "flow_dir": os.path.join(script_dir, "flows"),
        "files": {
            'jan': 'flow_8k_jan23.csv', 'feb': 'flow_8k_feb23.csv', 'mar': 'flow_8k_mar23.csv', 
            'apr': 'flow_8k_apr23.csv', 'may': 'flow_8k_may23.csv', 'jun': 'flow_8k_jun23.csv', 
            'jul': 'flow_8k_jul23.csv', 'aug': 'flow_8k_aug23.csv', 'sep': 'flow_8k_sep23.csv', 
            'oct': 'flow_8k_oct23.csv', 'nov': 'flow_8k_nov23.csv', 'dec': 'flow_8k_dec23.csv'
        },
        "capacity": 8000
    },
    "12kWh": {
        "flow_dir": os.path.join(script_dir, "flows"),
        "files": {
            'jan': 'flow_12k_jan23.csv', 'feb': 'flow_12k_feb23.csv', 'mar': 'flow_12k_mar23.csv', 
            'apr': 'flow_12k_apr23.csv', 'may': 'flow_12k_may23.csv', 'jun': 'flow_12k_jun23.csv', 
            'jul': 'flow_12k_jul23.csv', 'aug': 'flow_12k_aug23.csv', 'sep': 'flow_12k_sep23.csv', 
            'oct': 'flow_12k_oct23.csv', 'nov': 'flow_12k_nov23.csv', 'dec': 'flow_12k_dec23.csv'
        },
        "capacity": 12000
    },
    "15kWh": {
        "flow_dir": os.path.join(script_dir, "flows"),
        "files": {
            'jan': 'flow_15k_jan23.csv', 'feb': 'flow_15k_feb23.csv', 'mar': 'flow_15k_mar23.csv', 
            'apr': 'flow_15k_apr23.csv', 'may': 'flow_15k_may23.csv', 'jun': 'flow_15k_jun23.csv', 
            'jul': 'flow_15k_jul23.csv', 'aug': 'flow_15k_aug23.csv', 'sep': 'flow_15k_sep23.csv', 
            'oct': 'flow_15k_oct23.csv', 'nov': 'flow_15k_nov23.csv', 'dec': 'flow_15k_dec23.csv'
        },
        "capacity": 15000
    },
    "20kWh": {
        "flow_dir": os.path.join(script_dir, "flows"),
        "files": {
            'jan': 'flow_20k_jan23.csv', 'feb': 'flow_20k_feb23.csv', 'mar': 'flow_20k_mar23.csv', 
            'apr': 'flow_20k_apr23.csv', 'may': 'flow_20k_may23.csv', 'jun': 'flow_20k_jun23.csv', 
            'jul': 'flow_20k_jul23.csv', 'aug': 'flow_20k_aug23.csv', 'sep': 'flow_20k_sep23.csv', 
            'oct': 'flow_20k_oct23.csv', 'nov': 'flow_20k_nov23.csv', 'dec': 'flow_20k_dec23.csv'
        },
        "capacity": 20000
    },
    "26kWh": {
        "flow_dir": os.path.join(script_dir, "flows"),
        "files": {
            'jan': 'flow_26k_jan23.csv', 'feb': 'flow_26k_feb23.csv', 'mar': 'flow_26k_mar23.csv', 
            'apr': 'flow_26k_apr23.csv', 'may': 'flow_26k_may23.csv', 'jun': 'flow_26k_jun23.csv', 
            'jul': 'flow_26k_jul23.csv', 'aug': 'flow_26k_aug23.csv', 'sep': 'flow_26k_sep23.csv', 
            'oct': 'flow_26k_oct23.csv', 'nov': 'flow_26k_nov23.csv', 'dec': 'flow_26k_dec23.csv'
        },
        "capacity": 26000
    },
    "50kWh": {
        "flow_dir": os.path.join(script_dir, "flows"), 
        "files": {
            'jan': 'flow_50k_jan23.csv', 'feb': 'flow_50k_feb23.csv', 'mar': 'flow_50k_mar23.csv', 
            'apr': 'flow_50k_apr23.csv', 'may': 'flow_50k_may23.csv', 'jun': 'flow_50k_jun23.csv', 
            'jul': 'flow_50k_jul23.csv', 'aug': 'flow_50k_aug23.csv', 'sep': 'flow_50k_sep23.csv', 
            'oct': 'flow_50k_oct23.csv', 'nov': 'flow_50k_nov23.csv', 'dec': 'flow_50k_dec23.csv'
        },
        "capacity": 50000
    }
}


# --- Main Execution ---
if __name__ == "__main__":
    os.makedirs(os.path.join(script_dir, "output"), exist_ok=True)

    parser = argparse.ArgumentParser(
        description="Calculate SOC and export combined battery data for multiple scenarios.",
        formatter_class=argparse.RawTextHelpFormatter
    )

    available_scenario_names = sorted(list(scenarios_config.keys()))

    parser.add_argument(
        '--scenario',
        type=str,
        choices=available_scenario_names + ['all'],
        help=f"Specify the scenario to analyze.\n"
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
        process_scenario_data(name, config["flow_dir"], config["files"], config["capacity"], column_paths)

    print("\n✅ All battery SOC processing and CSV export completed for the selected scenario(s).")
    print(f"Check the '{os.path.join(script_dir, 'output')}' folder for scenario-specific data.")