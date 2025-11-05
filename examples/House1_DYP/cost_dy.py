import os
import pandas as pd
import numpy as np

# --- Configuration ---
script_dir = os.path.dirname(os.path.abspath(__file__))
# New input file path
input_csv_path = os.path.join(script_dir, "output", "monthly_energy_flows", "monthly_energy_flows_master_table.csv")
output_directory = os.path.join(script_dir, "output")
output_csv_path = os.path.join(output_directory, "scenario_net_costs.csv")

# Energy cost/revenue rates (adjust as needed)
# --- Replace fixed import cost with actual annual totals ---
EXPORT_REVENUE_PER_KWH = 0.08  # EUR/kWh (kept same)

# Actual total annual import costs (€) from grid_import_cost_summary.csv
annual_import_costs = {
    "PV_NoBattery": 2785.928865,
    "5kWh": 2447.080309,
    "8kWh": 2285.073499,
    "12kWh": 2100.318959,
    "15kWh": 1984.787786,
    "20kWh": 1828.227125,
    "26kWh": 1694.282317,
    "50kWh": 1433.947132
}

# Define scenarios with their capacities and corresponding CSV naming patterns
scenarios_config = {
    # Added the 'PV_NoBattery' scenario with 0 capacity
    "PV_NoBattery": {"capacity": 0, "file_prefix": "pv_nobattery"}, 
    "5kWh": {"capacity": 5000, "file_prefix": "battery_5k"},
    "8kWh": {"capacity": 8000, "file_prefix": "battery_8k"},
    "12kWh": {"capacity": 12000, "file_prefix": "battery_12k"},
    "15kWh": {"capacity": 15000, "file_prefix": "battery_15k"},
    "20kWh": {"capacity": 20000, "file_prefix": "battery_20k"},
    "26kWh": {"capacity": 26000, "file_prefix": "battery_26k"},
    "50kWh": {"capacity": 50000, "file_prefix": "battery_50k"}
}

# --- Installation cost calculator ---
def calculate_installation_cost(kwh_capacity):
    if kwh_capacity == 0:
        return 0
    cap_kWh = kwh_capacity / 1000.0
    
    # Assumptions (adjustable)
    battery_unit_cost = 399
    bos_unit_cost = 50
    inverter_fixed = 1200
    inverter_per_kwh = 30
    labor_fixed = 400
    labor_per_kwh = 30
    permits = 300
    transport_fixed = 100
    transport_per_kwh = 5
    contingency_rate = 0.10
    vat_rate = 0.19
    
    battery_cost = battery_unit_cost * cap_kWh
    bos_cost = bos_unit_cost * cap_kWh
    inverter_cost = inverter_fixed + inverter_per_kwh * cap_kWh
    labor_cost = labor_fixed + labor_per_kwh * cap_kWh
    transport_cost = transport_fixed + transport_per_kwh * cap_kWh
    
    subtotal = battery_cost + bos_cost + inverter_cost + labor_cost + permits + transport_cost
    contingency = contingency_rate * subtotal
    total_ex_vat = subtotal + contingency
    total_inc_vat = total_ex_vat * (1 + vat_rate)
    
    return round(total_inc_vat, 2)

# Dynamically build installation_costs dictionary
installation_costs = {
    name: calculate_installation_cost(cfg["capacity"])
    for name, cfg in scenarios_config.items()
}

# --- Main Script Execution ---
os.makedirs(output_directory, exist_ok=True)

print(f"--- Starting Annual Energy Cost Calculation ---")
print(f"Reading data from: {input_csv_path}")

if not os.path.exists(input_csv_path):
    print(f"Error: Input file not found at {input_csv_path}. Please run the data processing script first.")
else:
    try:
        df_master = pd.read_csv(input_csv_path)

        required_columns = ['Scenario', 'Month', 'Grid_Import', 'Grid_Export_to_Grid']
        if not all(col in df_master.columns for col in required_columns):
            print(f"Error: The input CSV is missing one or more of the required columns: {required_columns}")
        else:
            monthly_net_costs = {}
            unique_months = sorted(df_master['Month'].unique())

            for scenario_name in df_master['Scenario'].unique():
                scenario_df = df_master[df_master['Scenario'] == scenario_name].copy()
                
                scenario_df['Import_Cost (EUR)'] = annual_import_costs.get(scenario_name, np.nan) / len(unique_months)

                scenario_df['Export_Revenue (EUR)'] = scenario_df['Grid_Export_to_Grid'] * EXPORT_REVENUE_PER_KWH
                
                scenario_df['Net_Monthly_Cost (EUR)'] = scenario_df['Import_Cost (EUR)'] - scenario_df['Export_Revenue (EUR)']
                
                monthly_net_costs[scenario_name] = scenario_df.set_index('Month')['Net_Monthly_Cost (EUR)']

            # Create the final output DataFrame with all scenarios
            final_output_df = pd.DataFrame(index=unique_months)
            
            for scenario_name in monthly_net_costs.keys():
                final_output_df[scenario_name] = monthly_net_costs[scenario_name]
            
            # Use the scenarios_config keys to explicitly define the order, including 'NoBattery'
            ordered_scenario_columns = list(scenarios_config.keys())
            final_output_df = final_output_df[ordered_scenario_columns]

            # Calculate and add 'Total' row (annual net cost)
            annual_total_row = pd.DataFrame(final_output_df.sum(numeric_only=True)).T
            annual_total_row.index = ['Total']
            final_output_df = pd.concat([final_output_df, annual_total_row])
            
            # Add 'Installation Cost' row
            installation_cost_row = pd.DataFrame(
                [installation_costs.get(col, np.nan) for col in final_output_df.columns],
                index=final_output_df.columns
            ).T
            installation_cost_row.index = ['Installation Cost']
            final_output_df = pd.concat([final_output_df, installation_cost_row])

            # Reset index and format output
            final_output_df = final_output_df.reset_index().rename(columns={'index': 'Month'})
            
            for col in final_output_df.columns:
                if col != 'Month':
                    final_output_df[col] = pd.to_numeric(final_output_df[col], errors='coerce').round(2)
                    final_output_df[col] = final_output_df[col].apply(lambda x: f"{x:.2f}" if pd.notna(x) else '')
            
            # Save the compiled data to a new CSV
            final_output_df.to_csv(output_csv_path, index=False)
            print(f"\n--- Detailed monthly energy costs compiled to: {output_csv_path} ---")
            print("\nCompiled Data Overview:")
            print(final_output_df)

    except Exception as e:
        print(f"An error occurred: {e}")

print("\nAnnual energy cost calculation completed.")