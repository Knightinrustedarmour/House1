import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
# Removed: from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
from zipfile import ZipFile
import argparse
import traceback # Added for better debugging

def generate_soc_density_plots(base_output_dir, scenarios_config):
    """
    Generates and saves 2D Kernel Density Estimate (KDE) plots
    showing the density of SOC levels across hours of the day for each battery scenario.
    This version produces only PNG files and skips the combined PDF file.

    Args:
        base_output_dir (str): The base directory where scenario output folders are located.
        scenarios_config (dict): A dictionary containing scenario configurations,
                                 including scenario names and their capacities.
    """
    print("\n--- Generating SOC Density Plots (PNG only) ---")
    print(f"DEBUG: Scenarios selected for processing: {list(scenarios_config.keys())}")

    if not scenarios_config:
        print("No scenarios were selected for plotting based on your input. Exiting.")
        return

    all_png_files = []

    # Removed: with PdfPages(pdf_output_path) as pdf:
    for scenario_name, config in scenarios_config.items():
        # Skip NoBattery scenario, or any scenario with 0 capacity
        if config["capacity"] <= 0:
            print(f"    Skipping {scenario_name}: No battery capacity.")
            continue

        scenario_output_dir = os.path.join(base_output_dir, scenario_name)
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

            # Prepare data
            soc_data_int = df[soc_col_name].dropna().astype(int).clip(0, 100)
            hour_of_day = soc_data_int.index.hour 

            if soc_data_int.empty:
                print(f"    Warning: No valid SOC data points after dropping NaNs for {scenario_name}. Skipping plot.")
                continue

            print(f"    Generating density plot for {scenario_name}...")

            # Create a figure and an axes for the plot
            fig, ax = plt.subplots(figsize=(10, 7))

            # Use seaborn.kdeplot directly for the 2D density plot
            kde_plot = sns.kdeplot(x=soc_data_int, y=hour_of_day, fill=True,
                                    cmap='viridis', cbar=True, # Note: Corrected 'viriddis' to 'viridis'
                                    cbar_kws={"label": "Density of Occurrences"}, 
                                    ax=ax,
                                    clip=((0, 100), (0, 23))) 

            # Set titles and labels
            ax.set_xlabel("SOC (%)")
            ax.set_ylabel("Hour of Day")
            ax.set_title(f"SOC Density Plot - {scenario_name}\n(Capacity: {config['capacity'] / 1000:.1f} kWh)", y=1.02)

            # Set specific ticks for hours and SOC
            ax.set_xticks(range(0, 101, 10))
            ax.set_yticks(range(0, 24, 2))
            ax.grid(True, linestyle='--', alpha=0.6)

            # Ensure plot limits match desired ranges
            ax.set_xlim(0, 100)
            ax.set_ylim(0, 23)

            plt.tight_layout() # Removed rect argument since no suptitle/pdf

            # Removed: pdf.savefig(fig)

            # Save to PNG
            png_path = os.path.join(scenario_output_dir, f"{scenario_name}_SOC_Density_Plot.png")
            fig.savefig(png_path, dpi=300)
            all_png_files.append(png_path)
            print(f"    PNG saved to: {png_path}")
            plt.close(fig)

        except Exception as e:
            print(f"    An error occurred while processing {csv_path} for plotting: {e}")
            traceback.print_exc()

    print("\n✅ Individual SOC density plots saved as PNGs.")

    # Optionally, zip the individual PNGs into a combined zip
    zip_path = os.path.join(base_output_dir, "All_SOC_Density_Plots.zip")
    if all_png_files:
        with ZipFile(zip_path, 'w') as zipf:
            for file_path in all_png_files:
                if os.path.exists(file_path):
                    # Save the file with only its name in the zip
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
    "50kWh": { "capacity": 50000 }
}


if __name__ == "__main__":
    # 1. Set up argument parser
    parser = argparse.ArgumentParser(description="Generate SOC density plots for specified battery scenarios.")
    parser.add_argument(
        "--scenarios", 
        nargs='*',
        help="Specify battery scenarios to plot (e.g., 5kWh 50kWh). If not provided, all scenarios will be processed."
    )
    args = parser.parse_args()

    # 2. Determine which scenarios to process based on arguments
    if args.scenarios:
        selected_scenarios_config = {}
        for s_name in args.scenarios:
            if s_name in full_scenarios_config:
                selected_scenarios_config[s_name] = full_scenarios_config[s_name]
            else:
                print(f"Warning: Scenario '{s_name}' not recognized or not found in configuration. Skipping.")
        
        if not selected_scenarios_config:
            print(f"Error: No valid scenarios found to plot from your input: {args.scenarios}.")
            print(f"Available scenarios are: {list(full_scenarios_config.keys())}")
            exit()
        
        print(f"Processing only the following specified scenarios: {list(selected_scenarios_config.keys())}")
    else:
        selected_scenarios_config = full_scenarios_config
        print("No specific scenarios requested. Processing all available scenarios.")

    # 3. Proceed with plot generation using the selected scenarios
    if not os.path.exists(base_output_directory):
        print(f"Error: Base output directory '{base_output_directory}' not found.")
        print("Please ensure your 'output' directory exists and contains scenario subfolders with CSVs.")
    else:
        generate_soc_density_plots(base_output_directory, selected_scenarios_config)