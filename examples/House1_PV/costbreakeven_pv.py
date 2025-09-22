import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# --- Configuration ---
script_dir = os.path.dirname(os.path.abspath(__file__))

# The input CSV for installation costs and scenario names
input_costs_csv_path = os.path.join(script_dir, "output", "scenario_net_costs.csv")
# The input CSV with all annual energy flows
input_energy_flows_path = os.path.join(script_dir, "output", "energy_flow_master_table", "annual_energy_flows_master_table.csv")

output_breakeven_csv_path = os.path.join(script_dir, "output", "breakeven_periods.csv")
plots_output_directory = os.path.join(script_dir, "output", "breakeven_plots")
os.makedirs(plots_output_directory, exist_ok=True)

# --- Financial Parameters ---
GRID_IMPORT_PRICE = 0.35  # EUR/kWh
EXPORT_REVENUE_PRICE = 0.08  # EUR/kWh

print("--- Starting Breakeven Period Calculation ---")

if not os.path.exists(input_costs_csv_path):
    print(f"Error: Installation costs CSV file not found at {input_costs_csv_path}.")
    print("Ensure 'annual_energy_cost_compiler' run and CSV contains 'Installation Cost' row.")
    exit()

if not os.path.exists(input_energy_flows_path):
    print(f"Error: Annual energy flows master table not found at {input_energy_flows_path}.")
    print("Ensure the previous script successfully created this file.")
    exit()

try:
    # --- Debugging: Check write permissions and confirm plot output directory ---
    print(f"\nAttempting to save plots to: {os.path.abspath(plots_output_directory)}")
    try:
        # Test write permission by creating a dummy file
        test_file_path = os.path.join(plots_output_directory, "test_write.txt")
        with open(test_file_path, "w") as f:
            f.write("Test write succeeded.")
        os.remove(test_file_path)  # Clean up dummy file
        print(f"Successfully wrote to and removed a test file in {os.path.abspath(plots_output_directory)}. Write permissions are OK.")
    except Exception as e:
        print(f"CRITICAL ERROR: Failed to write to {os.path.abspath(plots_output_directory)}. Please check directory permissions. Error: {e}")
        exit()
    # --- End Debugging Block ---

    # --- Load and Prepare Data ---
    # Load the installation costs
    compiled_costs_df = pd.read_csv(input_costs_csv_path)
    
    # Load the annual energy flows master table
    annual_flows_df = pd.read_csv(input_energy_flows_path)
    annual_flows_df.set_index('Scenario', inplace=True)

    # Extract the installation costs, assuming 'Month' column exists
    installation_costs_row = compiled_costs_df[compiled_costs_df['Month'] == 'Installation Cost']
    
    if installation_costs_row.empty:
        print("Error: 'Installation Cost' row not found in the input CSV.")
        exit()

    # Convert row to a dictionary for easy lookup
    installation_costs = installation_costs_row.iloc[0].drop('Month').to_dict()
    
    # Clean up installation cost dictionary keys and convert values to numeric
    installation_costs = {k: pd.to_numeric(v, errors='coerce') for k, v in installation_costs.items()}
    
    # --- Calculate Costs and Breakeven Periods ---
    
    # Create a new DataFrame for calculations
    breakeven_df = annual_flows_df.copy()
    
    # Calculate annual energy costs for each scenario
    breakeven_df['Annual_Import_Cost'] = breakeven_df['Grid_Import'] * GRID_IMPORT_PRICE
    breakeven_df['Annual_Export_Revenue'] = breakeven_df['Grid_Export_to_Grid'] * EXPORT_REVENUE_PRICE
    breakeven_df['Annual_Net_Energy_Cost'] = breakeven_df['Annual_Import_Cost'] - breakeven_df['Annual_Export_Revenue']
    
    # Add installation costs from the dictionary
    breakeven_df['Installation_Cost_EUR'] = breakeven_df.index.map(installation_costs).fillna(0)
    
    # Get the baseline cost from the 'PV_NoBattery' scenario
    no_battery_cost = breakeven_df.loc['PV_NoBattery', 'Annual_Net_Energy_Cost']
    
    # Calculate annual savings against the baseline
    breakeven_df['Annual_Savings_EUR'] = no_battery_cost - breakeven_df['Annual_Net_Energy_Cost']
    
    # Calculate breakeven period
    breakeven_df['Breakeven_With_Setup_Years'] = breakeven_df.apply(
        lambda row: row['Installation_Cost_EUR'] / row['Annual_Savings_EUR'] if row['Annual_Savings_EUR'] > 0 else np.inf, 
        axis=1
    )
    
    # Prepare the final results DataFrame
    breakeven_results_df = breakeven_df.rename(columns={
        'Annual_Net_Energy_Cost': 'Calculated_Annual_Energy_Cost_EUR',
        'Annual_Savings_EUR': 'Returns_Per_Year_EUR',
        'Grid_Import': 'Annual_Grid_Import_kWh',
        'Grid_Export_to_Grid': 'Annual_Grid_Export_kWh'
    }).copy()

    # Add Scenario and Battery Size columns
    breakeven_results_df['Scenario'] = breakeven_results_df.index
    breakeven_results_df['Battery_Size_kWh'] = breakeven_results_df['Scenario'].apply(
        lambda x: x.replace('kWh', '') if 'kWh' in x else 'No Battery'
    )
    
    # Sort for consistent output
    breakeven_results_df['sort_key'] = breakeven_results_df['Battery_Size_kWh'].apply(lambda x: int(x) if x.replace('.', '', 1).isdigit() else 0)
    breakeven_results_df.sort_values(by='sort_key', inplace=True)
    breakeven_results_df.drop('sort_key', axis=1, inplace=True)

    # Select and reorder desired columns for the output CSV
    desired_columns = [
        'Scenario', 'Battery_Size_kWh', 'Calculated_Annual_Energy_Cost_EUR', 'Installation_Cost_EUR',
        'Annual_Grid_Import_kWh', 'Annual_Grid_Export_kWh',
        'Returns_Per_Year_EUR', 'Breakeven_With_Setup_Years'
    ]
    
    results_df = breakeven_results_df[desired_columns].copy()

    # Save results to CSV
    results_df.to_csv(output_breakeven_csv_path, index=False, float_format='%.2f')
    print(f"\n--- Breakeven periods saved to: {os.path.abspath(output_breakeven_csv_path)} ---")
    print("\nBreakeven Results Overview:")
    print(results_df)

    # --- Plotting Bar Graphs ---
    print("\n--- Generating Breakeven Plots ---")
    
    plot_df = results_df.copy()
    plot_df['Returns_Per_Year_EUR'] = pd.to_numeric(plot_df['Returns_Per_Year_EUR'], errors='coerce')
    plot_df['Breakeven_With_Setup_Years'] = pd.to_numeric(plot_df['Breakeven_With_Setup_Years'], errors='coerce')

    # Sort plotting DataFrame by battery size
    plot_df['Battery_Size_Sort'] = plot_df['Scenario'].apply(lambda x: int(x.replace('kWh', '')) if 'kWh' in x else 0)
    plot_df = plot_df.sort_values(by='Battery_Size_Sort').reset_index(drop=True)

    def generate_bar_plot(df, y_col, title, filename, y_label):
        fig, ax = plt.subplots(figsize=(12, 7))
        sns.barplot(x='Scenario', y=y_col, data=df, hue='Scenario', palette='viridis', ax=ax, legend=False)
        ax.set_title(title)
        ax.set_xlabel('Battery Nominal Capacity')
        ax.set_ylabel(y_label)
        ax.grid(axis='y', linestyle='--', alpha=0.7)
        for p in ax.patches:
            if pd.notna(p.get_height()):
                ax.annotate(f"{p.get_height():.2f}",
                            (p.get_x() + p.get_width() / 2., p.get_height()),
                            ha='center', va='center', fontsize=9, color='black', xytext=(0, 5),
                            textcoords='offset points')
        plot_path = os.path.join(plots_output_directory, filename)
        fig.savefig(plot_path, dpi=300)
        plt.close(fig)
        print(f"Bar graph for {y_label} saved to: {os.path.abspath(plot_path)}")

    generate_bar_plot(plot_df, 'Returns_Per_Year_EUR', 'Annual Returns Per Battery Scenario', 'Annual_Returns_Per_Battery_Scenario2.png', 'Returns Per Year (EUR)')
    generate_bar_plot(plot_df, 'Breakeven_With_Setup_Years', 'Breakeven Period Per Battery Scenario (With Setup Cost)', 'Breakeven_Period_Per_Battery_Scenario2.png', 'Breakeven Period (Years)')

    # --- 3. Cumulative Savings (Worm) Graph ---
    print("\n--- Generating Cumulative Savings Plot ---")
    
    cumulative_data = []
    max_years = 40

    for scenario_name, row in breakeven_results_df.iterrows():
        installation_cost = row['Installation_Cost_EUR']
        annual_savings = row['Returns_Per_Year_EUR']
        cumulative_money = -installation_cost
        
        cumulative_data.append({'Year': 0, 'Cumulative_Money': cumulative_money, 'Scenario': scenario_name})
        
        years_to_plot = max(max_years, int(np.ceil(row['Breakeven_With_Setup_Years'])) + 5) if pd.notna(row['Breakeven_With_Setup_Years']) else max_years
        
        for year in range(1, int(years_to_plot) + 1):
            cumulative_money += annual_savings
            cumulative_data.append({'Year': year, 'Cumulative_Money': cumulative_money, 'Scenario': scenario_name})
            
    cumulative_df = pd.DataFrame(cumulative_data)

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

    cumulative_plot_path = os.path.join(plots_output_directory, "Cumulative_Savings_Breakeven_Plot2.png")
    fig3.savefig(cumulative_plot_path, dpi=300)
    plt.close(fig3)
    print(f"Cumulative savings (worm) plot saved to: {os.path.abspath(cumulative_plot_path)}")

except Exception as e:
    print(f"An error occurred: {e}")
    import traceback
    traceback.print_exc()

print(f"\nBreakeven period calculation and plotting completed. Please check the plots in: {os.path.abspath(plots_output_directory)}")