import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# --- Configuration ---
script_dir = os.path.dirname(os.path.abspath(__file__))

# The input CSV for installation costs and scenario names
input_costs_csv_path = os.path.join(script_dir, "output", "scenario_net_costs.csv")
# The master CSV file containing all monthly energy flow data
input_flows_csv_path = os.path.join(script_dir, "output", "monthly_energy_flows", "monthly_energy_flows_master_table.csv")

output_breakeven_csv_path = os.path.join(script_dir, "output", "breakeven_periods.csv")
plots_output_directory = os.path.join(script_dir, "output", "breakeven_plots")
os.makedirs(plots_output_directory, exist_ok=True)

# --- Actual total annual import costs (€) from grid_import_cost_summary.csv ---
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

EXPORT_REVENUE_PRICE = 0.08  # still needed for export benefit


print("--- Starting Breakeven Period Calculation ---")

if not os.path.exists(input_costs_csv_path):
    print(f"Error: Input CSV file for costs not found at {input_costs_csv_path}.")
    print("Ensure 'annual_energy_cost_compiler' run and CSV contains 'Installation Cost' row.")
    exit()

if not os.path.exists(input_flows_csv_path):
    print(f"Error: Input master flows CSV not found at {input_flows_csv_path}.")
    print("Please run the energy flow simulation to generate this file.")
    exit()

try:
    # --- Load all data needed for calculations ---
    # Load costs from the previously generated CSV
    compiled_costs_df = pd.read_csv(input_costs_csv_path)
    
    # Load the master energy flows table
    master_flows_df = pd.read_csv(input_flows_csv_path)

    # Convert numeric columns in costs DataFrame
    for col in compiled_costs_df.columns:
        if col != 'Month':
            compiled_costs_df[col] = pd.to_numeric(compiled_costs_df[col], errors='coerce')

    # Extract installation costs row
    installation_costs_row = compiled_costs_df[compiled_costs_df['Month'] == 'Installation Cost'].iloc[0]
    
    # Extract scenarios to process from the costs DataFrame
    scenarios_to_process = [col for col in compiled_costs_df.columns if col not in ['Month', 'Total', 'Installation Cost']]
    
    # Sort scenarios for consistent order
    def get_sort_key_for_scenarios(scenario_name):
        try:
            return int(scenario_name.replace('kWh', '')) if 'kWh' in scenario_name else 0
        except ValueError:
            return float('inf')

    scenarios_to_process.sort(key=get_sort_key_for_scenarios)

    # --- Aggregate annual energy data from the master flows file ---
    annual_flows_df = master_flows_df.groupby('Scenario').agg(
        Grid_Import=('Grid_Import', 'sum'),
        Grid_Export_to_Grid=('Grid_Export_to_Grid', 'sum')
    ).reset_index()

    # --- Calculate the baseline energy cost (PV_NoBattery) ---
    no_battery_data = annual_flows_df[annual_flows_df['Scenario'] == 'PV_NoBattery']
    if no_battery_data.empty:
        print("Error: 'PV_NoBattery' scenario not found in the master flows data. Cannot calculate baseline.")
        exit()
    
    no_battery_annual_import_kwh = no_battery_data['Grid_Import'].iloc[0]
    no_battery_annual_export_kwh = no_battery_data['Grid_Export_to_Grid'].iloc[0]
    
    no_battery_annual_energy_cost = annual_import_costs["PV_NoBattery"]

    print(f"\nBaseline Annual Energy Cost (No Battery): {no_battery_annual_energy_cost:.2f} EUR")
    print(f"(Based on {no_battery_annual_import_kwh:.2f} kWh import and {no_battery_annual_export_kwh:.2f} kWh export)")

    breakeven_results = []
    cumulative_savings_data = []

    # --- Loop through each scenario (excluding PV_NoBattery) to calculate breakeven ---
    for scenario_name in [s for s in scenarios_to_process if s != 'PV_NoBattery']:
        scenario_data = annual_flows_df[annual_flows_df['Scenario'] == scenario_name]
        
        if scenario_data.empty:
            print(f"Warning: Data for scenario '{scenario_name}' not found. Skipping.")
            continue
            
        battery_installation_cost = installation_costs_row.get(scenario_name, 0.0)
        scenario_annual_import_kwh = scenario_data['Grid_Import'].iloc[0]
        scenario_annual_export_kwh = scenario_data['Grid_Export_to_Grid'].iloc[0]

        scenario_annual_energy_cost = annual_import_costs.get(scenario_name, np.nan)

        print(f"\n--- Scenario: {scenario_name} ---")
        print(f"  Installation Cost: {battery_installation_cost:.2f} EUR")
        print(f"  Annual Grid Import: {scenario_annual_import_kwh:.2f} kWh")
        print(f"  Annual Grid Export: {scenario_annual_export_kwh:.2f} kWh")
        print(f"  Calculated Annual Energy Cost: {scenario_annual_energy_cost:.2f} EUR")

        annual_savings = no_battery_annual_energy_cost - scenario_annual_energy_cost
        
        breakeven_period_with_setup = np.nan
        initial_investment = -battery_installation_cost
        
        # Prepare data for cumulative savings plot
        scenario_cumulative_data = [{'Year': 0, 'Cumulative_Money': initial_investment, 'Scenario': scenario_name}]
        
        if annual_savings <= 0:
            print(f"  Warning: No savings for {scenario_name} ({annual_savings:.2f} EUR). No breakeven.")
            for year in range(1, 21):
                scenario_cumulative_data.append({'Year': year, 'Cumulative_Money': initial_investment, 'Scenario': scenario_name})
        else:
            print(f"  Annual Savings: {annual_savings:.2f} EUR/year")
            breakeven_period_with_setup = battery_installation_cost / annual_savings
            print(f"  Breakeven Period: {breakeven_period_with_setup:.2f} years")
            
            cumulative_money = initial_investment
            max_years_for_plot = max(20, int(np.ceil(breakeven_period_with_setup)) + 5)
            for year in range(1, max_years_for_plot + 1):
                cumulative_money += annual_savings
                scenario_cumulative_data.append({'Year': year, 'Cumulative_Money': cumulative_money, 'Scenario': scenario_name})
        
        cumulative_savings_data.extend(scenario_cumulative_data)

        breakeven_results.append({
            'Scenario': scenario_name,
            'Installation_Cost_EUR': battery_installation_cost,
            'Annual_Grid_Import_kWh': scenario_annual_import_kwh,
            'Annual_Grid_Export_kWh': scenario_annual_export_kwh,
            'Returns_Per_Year_EUR': annual_savings,
            'Breakeven_With_Setup_Years': f"{breakeven_period_with_setup:.2f}" if pd.notna(breakeven_period_with_setup) else str(breakeven_period_with_setup)
        })

    # Convert results to DataFrame for CSV and plotting
    results_df = pd.DataFrame(breakeven_results)
    results_df.to_csv(output_breakeven_csv_path, index=False, float_format='%.2f')
    print(f"\n--- Breakeven periods saved to: {os.path.abspath(output_breakeven_csv_path)} ---")
    print("\nBreakeven Results Overview:")
    print(results_df)

    # --- Plotting Bar Graphs ---
    print("\n--- Generating Breakeven Plots ---")
    
    # Use the results_df for plotting after ensuring numeric types
    plot_df = results_df.copy()
    plot_df['Returns_Per_Year_EUR'] = pd.to_numeric(plot_df['Returns_Per_Year_EUR'], errors='coerce')
    plot_df['Breakeven_With_Setup_Years'] = pd.to_numeric(plot_df['Breakeven_With_Setup_Years'], errors='coerce')

    # 1. Bar Graph for Annual Returns
    fig1, ax1 = plt.subplots(figsize=(12, 7))
    sns.barplot(x='Scenario', y='Returns_Per_Year_EUR', data=plot_df, hue='Scenario', palette='viridis', ax=ax1, legend=False)
    ax1.set_title('Annual Returns Per Battery Scenario')
    ax1.set_xlabel('Battery Nominal Capacity')
    ax1.set_ylabel('Returns Per Year (EUR)')
    ax1.grid(axis='y', linestyle='--', alpha=0.7)
    for p in ax1.patches:
        ax1.annotate(f"{p.get_height():.2f}", (p.get_x() + p.get_width() / 2., p.get_height()), ha='center', va='center', fontsize=9, color='black', xytext=(0, 5), textcoords='offset points')
    returns_plot_path = os.path.join(plots_output_directory, "Annual_Returns_Per_Battery_Scenario.png")
    fig1.savefig(returns_plot_path, dpi=300)
    plt.close(fig1)
    print(f"Bar graph for Annual Returns saved to: {os.path.abspath(returns_plot_path)}")

    # 2. Bar Graph for Breakeven Period
    fig2, ax2 = plt.subplots(figsize=(12, 7))
    sns.barplot(x='Scenario', y='Breakeven_With_Setup_Years', data=plot_df, hue='Scenario', palette='magma', ax=ax2, legend=False)
    ax2.set_title('Breakeven Period Per Battery Scenario (With Setup Cost)')
    ax2.set_xlabel('Battery Nominal Capacity')
    ax2.set_ylabel('Breakeven Period (Years)')
    ax2.grid(axis='y', linestyle='--', alpha=0.7)
    for p in ax2.patches:
        if pd.notna(p.get_height()):
            ax2.annotate(f"{p.get_height():.2f}", (p.get_x() + p.get_width() / 2., p.get_height()), ha='center', va='center', fontsize=9, color='black', xytext=(0, 5), textcoords='offset points')
    breakeven_plot_path = os.path.join(plots_output_directory, "Breakeven_Period_Per_Battery_Scenario.png")
    fig2.savefig(breakeven_plot_path, dpi=300)
    plt.close(fig2)
    print(f"Bar graph for Breakeven Period saved to: {os.path.abspath(breakeven_plot_path)}")

    # 3. Cumulative Savings (Worm) Graph
    print("\n--- Generating Cumulative Savings Plot ---")
    cumulative_df = pd.DataFrame(cumulative_savings_data)
    
    # Sort for consistent plotting order
    cumulative_df['Battery_Size_Sort'] = cumulative_df['Scenario'].apply(lambda x: int(x.replace('kWh', '')) if 'kWh' in x else 0)
    cumulative_df = cumulative_df.sort_values(by=['Battery_Size_Sort', 'Year']).reset_index(drop=True)

    fig3, ax3 = plt.subplots(figsize=(14, 8))
    sns.lineplot(x='Year', y='Cumulative_Money', hue='Scenario', data=cumulative_df, ax=ax3, marker='o', markersize=4)
    ax3.set_title('Cumulative Financial Position Over Time (Towards Breakeven)')
    ax3.set_xlabel('Time (Years)')
    ax3.set_ylabel('Cumulative Money (EUR)')
    ax3.axhline(0, color='red', linestyle='--', linewidth=1, label='Breakeven Point (0 EUR)')
    ax3.grid(True, linestyle='--', alpha=0.7)
    ax3.legend(title='Battery Scenario')
    max_year_plot_all_scenarios = cumulative_df['Year'].max()
    ax3.set_xticks(range(0, int(max_year_plot_all_scenarios) + 1, max(1, int(max_year_plot_all_scenarios / 10))))
    ax3.set_xlim(0, max_year_plot_all_scenarios * 1.05)
    min_y = cumulative_df['Cumulative_Money'].min()
    max_y = cumulative_df['Cumulative_Money'].max()
    y_buffer = (max_y - min_y) * 0.1
    ax3.set_ylim(min_y - y_buffer, max_y + y_buffer)
    cumulative_plot_path = os.path.join(plots_output_directory, "Cumulative_Savings_Breakeven_Plot.png")
    fig3.savefig(cumulative_plot_path, dpi=300)
    plt.close(fig3)
    print(f"Cumulative savings (worm) plot saved to: {os.path.abspath(cumulative_plot_path)}")

except Exception as e:
    print(f"An error occurred: {e}")
    import traceback
    traceback.print_exc()

print(f"\nBreakeven period calculation and plotting completed. Please check the plots in: {os.path.abspath(plots_output_directory)}")