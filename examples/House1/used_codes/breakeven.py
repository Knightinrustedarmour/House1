
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# --- Configuration ---
script_dir = os.path.dirname(os.path.abspath(__file__))
# The input CSV for installation costs and scenario names
input_csv_path = os.path.join(script_dir, "output", "scenario_net_costs.csv")
# Directory where individual yearly energy summary CSVs are located
energy_summary_dir = os.path.join(script_dir, "output")

output_breakeven_csv_path = os.path.join(script_dir, "output", "breakeven_periods.csv")
plots_output_directory = os.path.join(script_dir, "output", "breakeven_plots")
os.makedirs(plots_output_directory, exist_ok=True)

# --- Financial Parameters ---
GRID_IMPORT_PRICE = 0.35  # EUR/kWh
EXPORT_REVENUE_PRICE = 0.08 # EUR/kWh

print("--- Starting Breakeven Period Calculation ---")

if not os.path.exists(input_csv_path):
    print(f"Error: Input CSV file not found at {input_csv_path}.")
    print("Ensure 'annual_energy_cost_compiler' run and CSV contains 'Installation Cost' row.")
    exit()

# Helper function to get annual import/export from individual CSV files
def get_annual_energy_data(scenario_name, energy_files_directory):
    if scenario_name == 'NoBattery':
        filename = f"yearly_energy_summary_2023_nobattery_kWh.csv"
    else:
        # Convert '10kWh' to '10k' for filename matching
        battery_size_for_filename = scenario_name.replace('kWh', 'k')
        filename = f"yearly_energy_summary_2023_battery_{battery_size_for_filename}_kWh.csv"

    filepath = os.path.join(energy_files_directory, filename)

    if not os.path.exists(filepath):
        print(f"Warning: Energy summary file not found for {scenario_name} at {filepath}. Using 0 for import/export.")
        return 0.0, 0.0 # Return zeros if file not found

    try:
        # Read without header, assuming first column is descriptor, second is value
        energy_df = pd.read_csv(filepath, header=None)
        
        grid_import_row = energy_df[energy_df.iloc[:, 0] == 'Total Period Grid Import (kWh)']
        grid_export_row = energy_df[energy_df.iloc[:, 0] == 'Total Period Grid Export (kWh)']

        grid_import = pd.to_numeric(grid_import_row.iloc[0, 1], errors='coerce') if not grid_import_row.empty else 0.0
        grid_export = pd.to_numeric(grid_export_row.iloc[0, 1], errors='coerce') if not grid_export_row.empty else 0.0
        
        return grid_import, grid_export
    except Exception as e:
        print(f"Error reading energy data from {filepath} for {scenario_name}: {e}. Using 0 for import/export.")
        return 0.0, 0.0


try:
    # --- Debugging: Check write permissions and confirm plot output directory ---
    print(f"\nAttempting to save plots to: {os.path.abspath(plots_output_directory)}")
    try:
        # Test write permission by creating a dummy file
        test_file_path = os.path.join(plots_output_directory, "test_write.txt")
        with open(test_file_path, "w") as f:
            f.write("Test write succeeded.")
        os.remove(test_file_path) # Clean up dummy file
        print(f"Successfully wrote to and removed a test file in {os.path.abspath(plots_output_directory)}. Write permissions are OK.")
    except Exception as e:
        print(f"CRITICAL ERROR: Failed to write to {os.path.abspath(plots_output_directory)}. Please check directory permissions. Error: {e}")
        exit()
    # --- End Debugging Block ---

    # Load data
    compiled_df = pd.read_csv(input_csv_path)

    # Convert numeric columns
    for col in compiled_df.columns:
        if col != 'Month':
            compiled_df[col] = pd.to_numeric(compiled_df[col], errors='coerce')

    # Extract installation costs row with robust checks
    def get_row_or_exit(df, month_name):
        filtered_row = df[df['Month'] == month_name]
        if filtered_row.empty:
            print(f"Error: Required row '{month_name}' not found in '{input_csv_path}'.")
            print("Please ensure your input CSV contains this row exactly as specified.")
            exit()
        return filtered_row.iloc[0]

    installation_costs_row = get_row_or_exit(compiled_df, 'Installation Cost')
    
    # --- Determine unique scenarios from compiled_df columns ---
    # These are the columns that represent different battery scenarios
    # Exclude 'Month', 'NoBattery', and potentially other summary rows if they exist
    scenarios_to_process = [col for col in compiled_df.columns if col not in ['Month', 'NoBattery', 'Total', 'Installation Cost']]
    
    # Sort scenarios (e.g., 5kWh, 10kWh, 15kWh...) for consistent order
    def get_sort_key_for_scenarios(scenario_name):
        try:
            return int(scenario_name.replace('kWh', ''))
        except ValueError:
            return float('inf') # Puts non-numeric scenarios (if any) at the end

    scenarios_to_process.sort(key=get_sort_key_for_scenarios)

    # --- Calculate the baseline energy cost (NoBattery) ---
    no_battery_annual_import_kwh, no_battery_annual_export_kwh = get_annual_energy_data('NoBattery', energy_summary_dir)
    
    # Cost = (Import * Price) - (Export * Revenue)
    no_battery_annual_energy_cost = (no_battery_annual_import_kwh * GRID_IMPORT_PRICE) - \
                                    (no_battery_annual_export_kwh * EXPORT_REVENUE_PRICE)

    print(f"\nBaseline Annual Energy Cost (No Battery): {no_battery_annual_energy_cost:.2f} EUR")
    print(f"(Based on {no_battery_annual_import_kwh:.2f} kWh import and {no_battery_annual_export_kwh:.2f} kWh export)")
    
    breakeven_results = []
    cumulative_savings_data = []

    # Iterate through battery scenarios
    for scenario_name in scenarios_to_process:
        # Get scenario data (default 0.0 if missing)
        battery_installation_cost = installation_costs_row.get(scenario_name, 0.0)
        scenario_annual_import_kwh, scenario_annual_export_kwh = get_annual_energy_data(scenario_name, energy_summary_dir)

        # Calculate annual energy cost for scenario
        scenario_annual_energy_cost = (scenario_annual_import_kwh * GRID_IMPORT_PRICE) - \
                                      (scenario_annual_export_kwh * EXPORT_REVENUE_PRICE)

        print(f"\n--- Scenario: {scenario_name} ---")
        print(f"  Installation Cost: {battery_installation_cost:.2f} EUR")
        print(f"  Annual Grid Import: {scenario_annual_import_kwh:.2f} kWh")
        print(f"  Annual Grid Export: {scenario_annual_export_kwh:.2f} kWh")
        print(f"  Calculated Annual Energy Cost: {scenario_annual_energy_cost:.2f} EUR")

        # Calculate annual savings vs. baseline
        annual_savings = no_battery_annual_energy_cost - scenario_annual_energy_cost
        
        breakeven_period_with_setup = np.nan
        initial_investment = -battery_installation_cost
        
        max_years_for_plot_scenario = 20
        
        scenario_cumulative_data = []
        scenario_cumulative_data.append({'Year': 0, 'Cumulative_Money': initial_investment, 'Scenario': scenario_name})

        if annual_savings <= 0:
            print(f"  Warning: No savings for {scenario_name} ({annual_savings:.2f} EUR). No breakeven.")
            # Extend flat line for non-breakeven
            for year in range(1, max_years_for_plot_scenario + 1):
                scenario_cumulative_data.append({'Year': year, 'Cumulative_Money': initial_investment, 'Scenario': scenario_name})
        else:
            print(f"  Annual Savings: {annual_savings:.2f} EUR/year")

            if battery_installation_cost > 0:
                breakeven_period_with_setup = battery_installation_cost / annual_savings
                print(f"  Breakeven Period: {breakeven_period_with_setup:.2f} years")
                # Extend plot years if breakeven is longer
                max_years_for_plot_scenario = max(max_years_for_plot_scenario, int(np.ceil(breakeven_period_with_setup)) + 5)
            else:
                breakeven_period_with_setup = 0.0
                print(f"  Breakeven Period: 0.00 years (No installation cost)")
                max_years_for_plot_scenario = max_years_for_plot_scenario

            # Calculate cumulative savings for plotting
            cumulative_money = initial_investment
            for year in range(1, max_years_for_plot_scenario + 1):
                cumulative_money += annual_savings
                scenario_cumulative_data.append({'Year': year, 'Cumulative_Money': cumulative_money, 'Scenario': scenario_name})
        
        cumulative_savings_data.extend(scenario_cumulative_data)

        breakeven_results.append({
            'Scenario': scenario_name,
            'Battery_Size_kWh': scenario_name,
            'Calculated_Annual_Energy_Cost_EUR': scenario_annual_energy_cost,
            'Installation_Cost_EUR': battery_installation_cost,
            'Annual_Grid_Import_kWh': scenario_annual_import_kwh,
            'Annual_Grid_Export_kWh': scenario_annual_export_kwh,
            'Returns_Per_Year_EUR': annual_savings,
            'Breakeven_With_Setup_Years': f"{breakeven_period_with_setup:.2f}" if pd.notna(breakeven_period_with_setup) else str(breakeven_period_with_setup)
        })

    # Convert results to DataFrame for CSV
    results_df = pd.DataFrame(breakeven_results)
    
    # Re-order columns for readability
    desired_columns = [
        'Scenario', 'Battery_Size_kWh', 'Calculated_Annual_Energy_Cost_EUR', 'Installation_Cost_EUR',
        'Annual_Grid_Import_kWh', 'Annual_Grid_Export_kWh',
        'Returns_Per_Year_EUR', 'Breakeven_With_Setup_Years'
    ]
    
    # Infer Battery_Size_kWh and sort
    results_df['Battery_Size_Num'] = results_df['Scenario'].apply(lambda x: int(x.replace('kWh', '')) if 'kWh' in x else 0)
    results_df = results_df.sort_values(by='Battery_Size_Num').reset_index(drop=True)
    results_df['Battery_Size_kWh'] = results_df['Battery_Size_Num'].apply(lambda x: f"{int(x)} kWh" if x > 0 else "No Battery")
    results_df = results_df.drop(columns=['Battery_Size_Num'])

    results_df = results_df[desired_columns]

    results_df.to_csv(output_breakeven_csv_path, index=False, float_format='%.2f')
    print(f"\n--- Breakeven periods saved to: {os.path.abspath(output_breakeven_csv_path)} ---")
    print("\nBreakeven Results Overview:")
    print(results_df)

    # --- Plotting Bar Graphs ---
    print("\n--- Generating Breakeven Plots ---")

    # Ensure numeric types for plotting
    plot_df = results_df.copy()
    plot_df['Returns_Per_Year_EUR'] = pd.to_numeric(plot_df['Returns_Per_Year_EUR'], errors='coerce')
    plot_df['Breakeven_With_Setup_Years'] = pd.to_numeric(plot_df['Breakeven_With_Setup_Years'], errors='coerce')

    # Sort plotting DataFrame by battery size
    plot_df['Battery_Size_Sort'] = plot_df['Scenario'].apply(lambda x: int(x.replace('kWh', '')) if 'kWh' in x else 0)
    plot_df = plot_df.sort_values(by='Battery_Size_Sort').reset_index(drop=True)


    # 1. Bar Graph for Annual Returns
    fig1, ax1 = plt.subplots(figsize=(12, 7))
    sns.barplot(x='Battery_Size_kWh', y='Returns_Per_Year_EUR', data=plot_df, hue='Battery_Size_kWh', palette='viridis', ax=ax1, legend=False)
    ax1.set_title('Annual Returns Per Battery Scenario')
    ax1.set_xlabel('Battery Nominal Capacity')
    ax1.set_ylabel('Returns Per Year (EUR)')
    ax1.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Add value labels
    for p in ax1.patches:
        ax1.annotate(f"{p.get_height():.2f}", 
                     (p.get_x() + p.get_width() / 2., p.get_height()), 
                     ha='center', va='center', fontsize=9, color='black', xytext=(0, 5), 
                     textcoords='offset points')

    returns_plot_path = os.path.join(plots_output_directory, "Annual_Returns_Per_Battery_Scenario2.png")
    fig1.savefig(returns_plot_path, dpi=300)
    plt.close(fig1)
    print(f"Bar graph for Annual Returns saved to: {os.path.abspath(returns_plot_path)}")


    # 2. Bar Graph for Breakeven Period
    fig2, ax2 = plt.subplots(figsize=(12, 7))
    sns.barplot(x='Battery_Size_kWh', y='Breakeven_With_Setup_Years', data=plot_df, hue='Battery_Size_kWh', palette='magma', ax=ax2, legend=False)
    ax2.set_title('Breakeven Period Per Battery Scenario (With Setup Cost)')
    ax2.set_xlabel('Battery Nominal Capacity')
    ax2.set_ylabel('Breakeven Period (Years)')
    ax2.grid(axis='y', linestyle='--', alpha=0.7)

    # Add value labels
    for p in ax2.patches:
        if pd.notna(p.get_height()):
            ax2.annotate(f"{p.get_height():.2f}", 
                         (p.get_x() + p.get_width() / 2., p.get_height()), 
                         ha='center', va='center', fontsize=9, color='black', xytext=(0, 5), 
                         textcoords='offset points')
    
    breakeven_plot_path = os.path.join(plots_output_directory, "Breakeven_Period_Per_Battery_Scenario2.png")
    fig2.savefig(breakeven_plot_path, dpi=300)
    plt.close(fig2)
    print(f"Bar graph for Breakeven Period saved to: {os.path.abspath(breakeven_plot_path)}")

    # --- 3. Cumulative Savings (Worm) Graph ---
    print("\n--- Generating Cumulative Savings Plot ---")

    cumulative_df = pd.DataFrame(cumulative_savings_data)
    
    # Sort for consistent plotting order
    cumulative_df['Battery_Size_Sort'] = cumulative_df['Scenario'].apply(lambda x: int(x.replace('kWh', '')) if 'kWh' in x else 0)
    cumulative_df = cumulative_df.sort_values(by=['Battery_Size_Sort', 'Year']).reset_index(drop=True)


    fig3, ax3 = plt.subplots(figsize=(14, 8))
    
    # Plot lines for each scenario
    sns.lineplot(x='Year', y='Cumulative_Money', hue='Scenario', data=cumulative_df, ax=ax3, marker='o', markersize=4)

    ax3.set_title('Cumulative Financial Position Over Time (Towards Breakeven)')
    ax3.set_xlabel('Time (Years)')
    ax3.set_ylabel('Cumulative Money (EUR)')
    ax3.axhline(0, color='red', linestyle='--', linewidth=1, label='Breakeven Point (0 EUR)')
    ax3.grid(True, linestyle='--', alpha=0.7)
    ax3.legend(title='Battery Scenario')

    # Adjust x-axis ticks and limits
    max_year_plot_all_scenarios = cumulative_df['Year'].max()
    ax3.set_xticks(range(0, int(max_year_plot_all_scenarios) + 1, max(1, int(max_year_plot_all_scenarios / 10))))
    ax3.set_xlim(0, max_year_plot_all_scenarios * 1.05) 
    
    # Adjust y-axis limits
    min_y = cumulative_df['Cumulative_Money'].min()
    max_y = cumulative_df['Cumulative_Money'].max()
    y_buffer = (max_y - min_y) * 0.1 
    ax3.set_ylim(min_y - y_buffer, max_y + y_buffer)


    cumulative_plot_path = os.path.join(plots_output_directory, "Cumulative_Savings_Breakeven_Plot2.png")
    fig3.savefig(cumulative_plot_path, dpi=300)
    plt.close(fig3)
    print(f"Cumulative savings (worm) plot saved to: {os.path.abspath(cumulative_plot_path)}")


except Exception as e:
    print(f"An error occurred: {e}")
    import traceback
    traceback.print_exc()

print(f"\nBreakeven period calculation and plotting completed. Please check the plots in: {os.path.abspath(plots_output_directory)}")
