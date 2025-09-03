import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# --- Configuration ---
script_dir = os.path.dirname(os.path.abspath(__file__))

# Input and output directories
input_dir = os.path.join(script_dir, "output", "energy_flow_master_table")
output_dir = os.path.join(script_dir, "output", "cost_and_breakeven_plots")
os.makedirs(output_dir, exist_ok=True)

# Input CSV file path from the previous script's output
input_csv_path = os.path.join(input_dir, "annual_energy_flows_master_table.csv")

# Output CSV file for the new cost summary table
output_csv_path = os.path.join(output_dir, "annual_cost_summary.csv")

# New output CSV file for the requested scenario net costs format
output_scenario_net_costs_path = os.path.join(script_dir, "output", "scenario_net_costs.csv")
os.makedirs(os.path.dirname(output_scenario_net_costs_path), exist_ok=True)

# Energy cost/revenue rates
IMPORT_COST_PER_KWH = 0.35  # EUR/kWh
EXPORT_REVENUE_PER_KWH = 0.08 # EUR/kWh

# Scenarios with their installation costs
scenarios_config = {
    "PV_NoBattery": { "cost": 0 }, 
    "5kWh": { "cost": 6400 },
    "8kWh": { "cost": 9600 },
    "12kWh": { "cost": 12800 },
    "15kWh": { "cost": 16000 },
    "20kWh": { "cost": 22400 },
    "26kWh": { "cost": 28800 },
    "50kWh": { "cost": 51200 }
}

# --- Core Script Execution ---
print("--- Starting Annual Cost and Breakeven Analysis ---")

if not os.path.exists(input_csv_path):
    print(f"Error: Input file not found at {input_csv_path}.")
    print("Please run results_pv.py first to generate the annual energy flows master table.")
else:
    try:
        # Read the annual results file
        annual_flows_df = pd.read_csv(input_csv_path, index_col='Scenario')

        # --- Data Preparation ---
        # Create a new DataFrame for analysis and plotting
        analysis_df = annual_flows_df.copy()

        # Calculate annual import cost and export revenue
        analysis_df['Annual Import Cost (EUR)'] = analysis_df['Grid_Import'] * IMPORT_COST_PER_KWH
        analysis_df['Annual Export Revenue (EUR)'] = analysis_df['Grid_Export_to_Grid'] * EXPORT_REVENUE_PER_KWH
        
        # Calculate annual net energy cost
        analysis_df['Annual Net Energy Cost (EUR)'] = analysis_df['Annual Import Cost (EUR)'] - analysis_df['Annual Export Revenue (EUR)']
        
        # Add installation costs
        analysis_df['Installation Cost (EUR)'] = [scenarios_config[idx]['cost'] for idx in analysis_df.index]

        # Calculate annual savings vs. baseline (NoBattery)
        no_battery_annual_net_cost = analysis_df.loc['PV_NoBattery', 'Annual Net Energy Cost (EUR)']
        analysis_df['Annual Savings (EUR)'] = no_battery_annual_net_cost - analysis_df['Annual Net Energy Cost (EUR)']
        
        # Calculate breakeven period
        # Avoid division by zero for non-saving scenarios
        analysis_df['Breakeven Period (Years)'] = analysis_df.apply(
            lambda row: row['Installation Cost (EUR)'] / row['Annual Savings (EUR)'] 
            if row['Annual Savings (EUR)'] > 0 else np.inf, axis=1
        )
        
        print("\n--- Summary of Calculated Data ---")
        print(analysis_df[['Annual Import Cost (EUR)', 'Annual Export Revenue (EUR)', 'Annual Net Energy Cost (EUR)', 'Installation Cost (EUR)', 'Annual Savings (EUR)', 'Breakeven Period (Years)']])

        # --- Create and Save the New Summary CSV ---
        summary_df = analysis_df[[
            'Annual Import Cost (EUR)', 
            'Annual Export Revenue (EUR)', 
            'Annual Net Energy Cost (EUR)', 
            'Installation Cost (EUR)', 
            'Annual Savings (EUR)', 
            'Breakeven Period (Years)'
        ]].copy()
        
        # Format for readability
        for col in summary_df.columns:
            summary_df[col] = summary_df[col].apply(lambda x: f"{x:.2f}" if pd.notna(x) and x != np.inf else ('' if x == np.inf else ''))

        summary_df.to_csv(output_csv_path)
        print(f"\n--- Annual cost summary table saved to: {output_csv_path} ---")
        print("\nAnnual Summary Overview:")
        print(summary_df)

        # --- Create and Save the new `scenario_net_costs.csv` ---
        print("\n--- Creating and saving scenario_net_costs.csv ---")
        # Extract the annual net cost and installation cost from the analysis DataFrame
        # The .T transposes the DataFrame, making scenarios the columns
        scenario_net_costs_df = analysis_df[['Annual Net Energy Cost (EUR)', 'Installation Cost (EUR)']].T
        
        # Rename the index to match the requested format
        scenario_net_costs_df.rename(index={
            'Annual Net Energy Cost (EUR)': 'Total',
            'Installation Cost (EUR)': 'Installation Cost'
        }, inplace=True)
        
        # Reset the index to make the new row names a column
        scenario_net_costs_df.reset_index(inplace=True)
        scenario_net_costs_df.rename(columns={'index': 'Month'}, inplace=True)
        
        # Format the numbers to 2 decimal places
        for col in scenario_net_costs_df.columns:
            if col != 'Month':
                scenario_net_costs_df[col] = scenario_net_costs_df[col].round(2)
                scenario_net_costs_df[col] = scenario_net_costs_df[col].apply(
                    lambda x: f"{x:.2f}" if pd.notna(x) else ''
                )

        # Save to the new CSV file
        scenario_net_costs_df.to_csv(output_scenario_net_costs_path, index=False)
        print(f"\n--- Scenario net costs table saved to: {output_scenario_net_costs_path} ---")
        print("\nScenario Net Costs Overview:")
        print(scenario_net_costs_df)

        # --- Plotting Functions ---
        def generate_bar_plot(df, y_col, title, filename, y_label):
            """Generates and saves a bar plot."""
            plt.figure(figsize=(12, 7))
            
            # Sort data for plotting
            plot_df = df.copy()
            plot_df['sort_key'] = plot_df.index.to_series().apply(
                lambda x: int(x.replace('kWh', '')) if 'kWh' in x else 0)
            plot_df = plot_df.sort_values('sort_key').drop('sort_key', axis=1)

            sns.barplot(x=plot_df.index, y=y_col, data=plot_df, hue=plot_df.index, palette='viridis', legend=False)
            
            plt.title(title)
            plt.xlabel('Battery Nominal Capacity')
            plt.ylabel(y_label)
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # Add value labels
            ax = plt.gca()
            for p in ax.patches:
                if p.get_height() > 0:
                    ax.annotate(f"{p.get_height():.2f}", 
                                (p.get_x() + p.get_width() / 2., p.get_height()), 
                                ha='center', va='center', fontsize=9, color='black', xytext=(0, 5), 
                                textcoords='offset points')
            
            plot_path = os.path.join(output_dir, filename)
            plt.savefig(plot_path, dpi=300)
            print(f"Plot saved to: {plot_path}")
            plt.close()

        # Generate the requested plots
        generate_bar_plot(analysis_df, 'Annual Import Cost (EUR)', 'Annual Grid Import Cost Per Scenario', 'annual_import_costs.png', 'Annual Import Cost (EUR)')
        generate_bar_plot(analysis_df, 'Annual Export Revenue (EUR)', 'Annual Grid Export Revenue Per Scenario', 'annual_export_revenue.png', 'Annual Export Revenue (EUR)')
        generate_bar_plot(analysis_df, 'Annual Savings (EUR)', 'Annual Savings Per Scenario (vs. No Battery)', 'annual_savings.png', 'Annual Savings (EUR)')
        generate_bar_plot(analysis_df, 'Breakeven Period (Years)', 'Breakeven Period Per Scenario', 'breakeven_period.png', 'Breakeven Period (Years)')

        # --- Cumulative Savings (Worm) Plot ---
        print("\n--- Generating Cumulative Savings Plot ---")
        cumulative_data = []
        max_years = 40  # Initial max years for plotting

        # First, collect all data and determine the required plot length
        for scenario_name, row in analysis_df.iterrows():
            installation_cost = row['Installation Cost (EUR)']
            annual_savings = row['Annual Savings (EUR)']

            current_money = -installation_cost
            cumulative_data.append({'Year': 0, 'Cumulative_Money': current_money, 'Scenario': scenario_name})
            
            for year in range(1, max_years + 1):
                current_money += annual_savings
                cumulative_data.append({'Year': year, 'Cumulative_Money': current_money, 'Scenario': scenario_name})

        cumulative_df = pd.DataFrame(cumulative_data)

        # Plot the cumulative savings
        plt.figure(figsize=(14, 8))
        sns.lineplot(x='Year', y='Cumulative_Money', hue='Scenario', data=cumulative_df, marker='o', markersize=4)

        plt.title('Cumulative Financial Position Over Time (Towards Breakeven)')
        plt.xlabel('Time (Years)')
        plt.ylabel('Cumulative Money (EUR)')
        plt.axhline(0, color='red', linestyle='--', linewidth=1, label='Breakeven Point')
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend(title='Battery Scenario')
        plt.tight_layout()

        cumulative_plot_path = os.path.join(output_dir, "cumulative_savings_plot.png")
        plt.savefig(cumulative_plot_path, dpi=300)
        print(f"Cumulative savings plot saved to: {cumulative_plot_path}")
        plt.close()

    except Exception as e:
        print(f"\nAn error occurred during analysis or plotting: {e}")
        import traceback
        traceback.print_exc()

print("\nAnalysis and plotting completed.")
