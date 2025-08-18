import os
import pandas as pd
import numpy as np

# --- Configuration ---
# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Set the base directory where your monthly CSVs are located, and where the output CSV will be saved.
output_directory = os.path.join(script_dir, "output") 

# Output CSV file path for the new requested format
output_csv_path = os.path.join(output_directory, "scenario_net_costs.csv") # New filename

# Energy cost/revenue rates
IMPORT_COST_PER_KWH = 0.35  # EUR/kWh
EXPORT_REVENUE_PER_KWH = 0.08 # EUR/kWh

# Define scenarios with their capacities and corresponding CSV naming patterns
scenarios_config = {
    "5kWh": { "capacity": 5000, "file_prefix": "battery_5k" },
    "NoBattery": { "capacity": 0, "file_prefix": "nobattery" }, 
    "8kWh": { "capacity": 8000, "file_prefix": "battery_8k" },
    "12kWh": { "capacity": 12000, "file_prefix": "battery_12k" },
    "15kWh": { "capacity": 15000, "file_prefix": "battery_15k" },
    "20kWh": { "capacity": 20000, "file_prefix": "battery_20k" },
    "26kWh": { "capacity": 26000, "file_prefix": "battery_26k" },
    "50kWh": { "capacity": 50000, "file_prefix": "battery_50k" }
}

# Manually provided lower-end setup costs (from previous chat)
installation_costs = {
    "NoBattery": 0, # Assuming no installation cost for no battery scenario
    "5kWh": 6400,
    "8kWh": 9600,
    "12kWh": 12800,
    "15kWh": 16000,
    "20kWh": 22400,
    "26kWh": 28800,
    "50kWh": 51200
}

# Dictionary to store monthly net costs for each scenario
monthly_net_costs_by_scenario = {}
all_months = [] # To keep track of all unique months encountered

print(f"--- Starting Annual Energy Cost Calculation ---")
print(f"Reading monthly summaries from: {output_directory}")

os.makedirs(output_directory, exist_ok=True)

# Loop through each scenario to find and process its monthly CSV
for scenario_name, config in scenarios_config.items():
    csv_filename = f"monthly_energy_summary_2023_{config['file_prefix']}_kWh.csv"
    full_csv_path = os.path.join(output_directory, csv_filename)

    print(f"\nProcessing scenario: {scenario_name} (Looking for: {csv_filename})")

    if not os.path.exists(full_csv_path):
        print(f"  Warning: CSV file not found at {full_csv_path}. Skipping this scenario.")
        monthly_net_costs_by_scenario[scenario_name] = pd.Series([]) # Add empty series for missing scenario
        continue

    try:
        monthly_df = pd.read_csv(full_csv_path)

        if 'Grid Import (kWh)' not in monthly_df.columns or 'Grid Export (kWh)' not in monthly_df.columns:
            print(f"  Error: Required columns 'Grid Import (kWh)' or 'Grid Export (kWh)' not found in {csv_filename}. Skipping.")
            monthly_net_costs_by_scenario[scenario_name] = pd.Series([])
            continue
        
        # Calculate monthly import cost and export revenue
        monthly_df['Import_Cost (EUR)'] = monthly_df['Grid Import (kWh)'] * IMPORT_COST_PER_KWH
        monthly_df['Export_Revenue (EUR)'] = monthly_df['Grid Export (kWh)'] * EXPORT_REVENUE_PER_KWH

        # Calculate monthly net cost (cost - revenue)
        monthly_df['Net_Monthly_Cost (EUR)'] = monthly_df['Import_Cost (EUR)'] - monthly_df['Export_Revenue (EUR)']

        # Store monthly net costs, indexed by month
        # Ensure 'Month' column is treated as index for aligning data
        monthly_net_costs_series = monthly_df.set_index('Month')['Net_Monthly_Cost (EUR)']
        monthly_net_costs_by_scenario[scenario_name] = monthly_net_costs_series
        
        # Collect all unique months
        if not all_months: # Only populate all_months from the first successfully processed scenario
             all_months = monthly_df['Month'].tolist()

        print(f"  Successfully processed. Monthly Net Costs collected.")

    except Exception as e:
        print(f"  An error occurred while processing {full_csv_path}: {e}")
        monthly_net_costs_by_scenario[scenario_name] = pd.Series([]) # Ensure a placeholder even on error

if not monthly_net_costs_by_scenario:
    print("\nNo data was successfully processed for any scenario. Output CSV will not be created.")
else:
    # Create the base DataFrame for the output
    # Use all_months to ensure consistent row order, even if some scenarios miss data
    final_output_df = pd.DataFrame({'Month': all_months})
    final_output_df = final_output_df.set_index('Month')

    # Add scenario columns with monthly net costs
    for scenario_name, net_costs_series in monthly_net_costs_by_scenario.items():
        # Rename columns to match desired output
        column_name = scenario_name # E.g., "5kWh", "NoBattery"
        final_output_df[column_name] = net_costs_series

    # Calculate and add 'Total' row (annual net cost)
    annual_total_row = pd.DataFrame(columns=final_output_df.columns)
    annual_total_row.loc['Total'] = final_output_df.sum()
    final_output_df = pd.concat([final_output_df, annual_total_row])

    # Add 'Installation Cost' row
    installation_cost_row = pd.DataFrame(columns=final_output_df.columns)
    installation_cost_values = {}
    for scenario_name_key, cost_value in installation_costs.items():
        if scenario_name_key in final_output_df.columns:
            installation_cost_values[scenario_name_key] = cost_value
        else:
            installation_cost_values[scenario_name_key] = np.nan # Or 0 if preferred for missing scenarios
    
    # Ensure all scenarios columns are present in installation_cost_values
    for col in final_output_df.columns:
        if col not in installation_cost_values:
            installation_cost_values[col] = np.nan # Fill missing scenario columns with NaN

    installation_cost_row.loc['Installation Cost'] = pd.Series(installation_cost_values)
    final_output_df = pd.concat([final_output_df, installation_cost_row])

    # Reset index to make 'Month' a regular column again
    final_output_df = final_output_df.reset_index().rename(columns={'index': 'Month'})

    # Format all numerical columns to 2 decimal points
    for col in final_output_df.columns:
        if col != 'Month':
            final_output_df[col] = final_output_df[col].round(2)
            # Convert to string to ensure '.00' is kept for whole numbers
            final_output_df[col] = final_output_df[col].apply(lambda x: f"{x:.2f}" if pd.notna(x) else '')

    # Ensure columns order based on your request: Month, 5kWh, 8kWh, etc.
    # Dynamically build scenario column names based on scenarios_config order
    ordered_scenario_columns = [s for s in scenarios_config.keys()]
    final_column_order = ['Month'] + ordered_scenario_columns
    final_output_df = final_output_df[final_column_order]

    # Save the compiled data to a new CSV
    final_output_df.to_csv(output_csv_path, index=False)
    print(f"\n--- Detailed monthly energy costs compiled to: {output_csv_path} ---")
    print("\nCompiled Data Overview:")
    print(final_output_df)

print("\nAnnual energy cost calculation completed.")
