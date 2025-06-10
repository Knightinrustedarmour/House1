import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
from zipfile import ZipFile
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize
import argparse 

def generate_soc_density_scatter_plots(base_output_dir, scenarios_config):
    """
    Generates and saves 2D Kernel Density Estimate (KDE) plots
    showing the density of SOC levels across hours of the day for each battery scenario.
    The x-axis will be SOC (as whole numbers), y-axis will be Hour of Day,
    and color intensity will represent density of occurrences, with a numerical colorbar.

    Args:
        base_output_dir (str): The base directory where scenario output folders are located.
        scenarios_config (dict): A dictionary containing scenario configurations,
                                 including scenario names and their capacities.
    """
    print("\n--- Generating SOC Density Plots ---")
    # Debug print: Show what scenarios are actually being processed by the function
    print(f"DEBUG: Scenarios selected for processing: {list(scenarios_config.keys())}")

    if not scenarios_config:
        print("No scenarios were selected for plotting based on your input. Exiting.")
        return

    pdf_output_path = os.path.join(base_output_dir, "SOC_Density_Plots.pdf")
    all_png_files = []

    with PdfPages(pdf_output_path) as pdf:
        for scenario_name, config in scenarios_config.items():
            # Skip scenarios with no battery capacity or where SOC is not applicable
            if config["capacity"] <= 0:
                print(f"    Skipping {scenario_name}: No battery capacity.")
                continue

            scenario_output_dir = os.path.join(base_output_dir, scenario_name)
            # Ensure the specific scenario's output directory exists
            os.makedirs(scenario_output_dir, exist_ok=True)

            csv_path = os.path.join(scenario_output_dir, f"Combined_Battery_Data_{scenario_name}.csv")

            if not os.path.exists(csv_path):
                print(f"    Warning: CSV file not found for {scenario_name}: {csv_path}. Skipping plot.")
                continue

            try:
                df = pd.read_csv(csv_path, index_col=0, parse_dates=True)
                soc_col_name = f"SOC_{scenario_name}_%"

                if soc_col_name not in df.columns or df[soc_col_name].isnull().all():
                    print(f"    Warning: SOC data column '{soc_col_name}' not found or is empty for {scenario_name}. Skipping plot.")
                    continue

                # Prepare the data for plotting
                # Round SOC to nearest integer as requested
                soc_data_int = df[soc_col_name].dropna().astype(int).clip(0, 100) # Ensure SOC is within 0-100 after rounding
                
                # Get hours directly from the index of the cleaned SOC data
                hour_of_day = soc_data_int.index.hour 

                if soc_data_int.empty:
                    print(f"    Warning: No valid SOC data points after dropping NaNs for {scenario_name}. Skipping plot.")
                    continue

                print(f"    Generating density plot for {scenario_name}...")

                # Create a DataFrame for jointplot
                plot_df = pd.DataFrame({
                    'SOC_%': soc_data_int,
                    'Hour of Day': hour_of_day
                })

                # Use JointGrid with kind='kde' for a 2D density plot
                # Choose a colormap, e.g., 'viridis', 'plasma', 'magma', 'cividis'
                cmap = 'viridis' 
                g = sns.jointplot(x='SOC_%', y='Hour of Day', data=plot_df, kind='kde', fill=True,
                                  cmap=cmap, xlim=(0, 100), ylim=(0, 23),
                                  colorbar=True, # Explicitly enable colorbar
                                  cbar_kws={"label": "Density of Occurrences"}) # Add label to colorbar

                # Set titles and labels
                g.set_axis_labels("SOC (%)", "Hour of Day")
                g.fig.suptitle(f"SOC Density Plot - {scenario_name}\n(Capacity: {config['capacity'] / 1000:.1f} kWh)", y=0.98) 

                # Set specific ticks for hours and SOC
                g.ax_joint.set_xticks(range(0, 101, 10)) # SOC from 0 to 100, step 10
                g.ax_joint.set_yticks(range(0, 24, 2)) # Hours from 0 to 23, step 2
                g.ax_joint.grid(True, linestyle='--', alpha=0.6)

                # Adjust the top margin to make space for the suptitle
                g.fig.subplots_adjust(top=0.88) 

                # Removed manual ScalarMappable and cbar_ax creation as jointplot handles it now

                # Save to PDF
                pdf.savefig(g.fig)

                # Save to PNG
                png_path = os.path.join(scenario_output_dir, f"{scenario_name}_SOC_Density_Plot.png")
                g.fig.savefig(png_path, dpi=300)
                all_png_files.append(png_path)
                plt.close(g.fig) # Close the figure to free up memory

            except Exception as e:
                print(f"    An error occurred while processing {csv_path} for plotting: {e}")
                import traceback
                traceback.print_exc() # Print full traceback for debugging

    print(f"\nAll SOC density plots saved to: {pdf_output_path}")

    # Optionally, zip the individual PNGs into a combined zip
    zip_path = os.path.join(base_output_dir, "All_SOC_Density_Plots.zip")
    if all_png_files:
        with ZipFile(zip_path, 'w') as zipf:
            for file_path in all_png_files:
                if os.path.exists(file_path):
                    zipf.write(file_path, arcname=os.path.basename(file_path))
                else:
                    print(f"    Warning: PNG file not found for zipping: {file_path}")
        print(f"All individual SOC density plots zipped to: {zip_path}")
    else:
        print("No individual SOC density plots were generated to zip.")


# --- Global Configuration ---
script_dir = os.path.dirname(os.path.abspath(__file__))
base_output_directory = os.path.join(script_dir, "output") 

# This dictionary holds ALL available scenarios.
full_scenarios_config = {
    "5kWh": { "capacity": 5000 },
    "NoBattery": { "capacity": 0 },
    "8kWh": { "capacity": 8000 },
    "12kWh": { "capacity": 12000 },
    "15kWh": { "capacity": 15000 },
    "20kWh": { "capacity": 20000 },
    "26kWh": { "capacity": 26000 },
    "50kWh": { "capacity": 50000 } # The new 50kWh scenario is here!
}


if __name__ == "__main__":
    # 1. Set up argument parser
    parser = argparse.ArgumentParser(description="Generate SOC density plots for specified battery scenarios.")
    parser.add_argument(
        "--scenarios", 
        nargs='*', # Allows 0 or more arguments (list of strings)
        help="Specify battery scenarios to plot (e.g., 5kWh 50kWh). If not provided, all scenarios will be processed."
    )
    args = parser.parse_args()

    # Debug print: Shows what argparse parsed from your command line
    print(f"DEBUG: Parsed arguments object: {args}")
    print(f"DEBUG: Value of 'scenarios' argument: {args.scenarios}")

    # 2. Determine which scenarios to process based on arguments
    if args.scenarios: # This condition is True if --scenarios was provided with any value
        # Filter the full_scenarios_config to include only requested scenarios
        selected_scenarios_config = {}
        for s_name in args.scenarios:
            if s_name in full_scenarios_config:
                selected_scenarios_config[s_name] = full_scenarios_config[s_name]
            else:
                print(f"Warning: Scenario '{s_name}' not recognized or not found in configuration. Skipping.")
        
        if not selected_scenarios_config:
            print(f"Error: No valid scenarios found to plot from your input: {args.scenarios}.")
            print(f"Available scenarios are: {list(full_scenarios_config.keys())}")
            exit() # Exit if no valid scenarios could be picked based on user input
        
        print(f"Processing only the following specified scenarios: {list(selected_scenarios_config.keys())}")
    else: # This block runs if --scenarios was NOT provided
        selected_scenarios_config = full_scenarios_config
        print("No specific scenarios requested. Processing all available scenarios.")

    # 3. Proceed with plot generation using the selected scenarios
    if not os.path.exists(base_output_directory):
        print(f"Error: Base output directory '{base_output_directory}' not found.")
        print("Please ensure your 'output' directory exists and contains scenario subfolders with CSVs.")
    else:
        generate_soc_density_scatter_plots(base_output_directory, selected_scenarios_config)

