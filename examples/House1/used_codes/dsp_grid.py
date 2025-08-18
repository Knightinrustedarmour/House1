import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
from zipfile import ZipFile
import argparse

# --- 1. Main Density Plot Generation Function ---
def generate_flow_density_plots(base_output_dir, scenarios_config):
    """
    Generates and saves 2D Kernel Density Estimate (KDE) plots
    showing the density of specified energy flow levels across hours of the day
    for each battery scenario.
    The x-axis will be the flow value, y-axis will be Hour of Day,
    and color intensity will represent density of occurrences, with a numerical colorbar.
    This version focuses only on the central 2D density plot, without marginal subplots.
    """
    print("\n--- Generating Energy Flow Density Plots ---")
    print(f"DEBUG: Scenarios selected for processing: {list(scenarios_config.keys())}")

    if not scenarios_config:
        print("No scenarios were selected for plotting based on your input. Exiting.")
        return

    # Define the specific flows for which to generate density plots
    flows_to_plot_density = {
        "PV_distribution": "PV Self-Consumption",
        "Demand2": "Electricity Demand",
        "Grid_import": "Grid Import",
        "Grid_export": "Grid Export"
    }

    # Define common column paths for extracting data
    # These are kept for extraction, but no SOC calculation happens here.
    common_column_paths = {
        "PV_distribution": ("SolphLabel(location='House1', mtress_component='PV', solph_node='connection')", "SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='distribution')"),
        "Demand2": ("SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='distribution')", "SolphLabel(location='House1', mtress_component='demand', solph_node='input')"),
        "Grid_import": ("SolphLabel(location='House1', mtress_component='ElectricityGridConnection', solph_node='grid_import')", "SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='distribution')"),
        "Grid_export": ("SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='feed_in')", "SolphLabel(location='House1', mtress_component='ElectricityGridConnection', solph_node='grid_export')")
    }

    global_pdf_output_path = os.path.join(base_output_dir, "Combined_Flow_Density_Plots.pdf")
    all_global_png_files = [] # Collect all PNGs for a combined zip

    with PdfPages(global_pdf_output_path) as pdf_all_flows:
        for scenario_name, config in scenarios_config.items():
            scenario_output_dir = os.path.join(base_output_dir, scenario_name)
            os.makedirs(scenario_output_dir, exist_ok=True) # Ensure directory exists

            # The CSV path assumes you've already run the main processing script
            # that generates 'Combined_All_Flow_Data_{scenario_name}.csv'
            csv_path = os.path.join(scenario_output_dir, f"Combined_All_Flow_Data_{scenario_name}.csv")

            if not os.path.exists(csv_path):
                print(f"    Warning: CSV file not found for {scenario_name}: {csv_path}. Skipping density plots for this scenario.")
                continue

            try:
                df = pd.read_csv(csv_path, index_col=0, parse_dates=True)

                for flow_key, plot_title_suffix in flows_to_plot_density.items():
                    flow_col_name = f"{flow_key}_W_{scenario_name}"

                    if flow_col_name not in df.columns or df[flow_col_name].isnull().all() or df[flow_col_name].sum() == 0:
                        print(f"        Warning: Flow data column '{flow_col_name}' not found, is empty, or has no activity for {scenario_name}. Skipping {plot_title_suffix} density plot.")
                        continue

                    # Prepare the data for plotting
                    flow_data_clipped = df[flow_col_name].dropna().clip(lower=0) # Ensure non-negative flows
                    hour_of_day = flow_data_clipped.index.hour

                    if flow_data_clipped.empty:
                        print(f"        Warning: No valid data points after cleaning for {flow_col_name} in {scenario_name}. Skipping density plot.")
                        continue

                    print(f"    Generating density plot for {plot_title_suffix} in {scenario_name}...")

                    fig, ax = plt.subplots(figsize=(10, 7))

                    # Determine y_label
                    y_label = "Power (W)"
                    if flow_key == "Demand2":
                        y_label = "Demand (W)"
                    elif "PV" in flow_key:
                        y_label = "PV Power (W)"
                    elif "Grid" in flow_key:
                        y_label = "Grid Power (W)"

                    # Choose colormap for density plots based on flow type
                    cmap_for_flow_density = 'viridis' # Default
                    if flow_key == "Demand2":
                        cmap_for_flow_density = 'plasma'
                    elif flow_key == "Grid_import":
                        cmap_for_flow_density = 'magma'
                    elif flow_key == "Grid_export":
                        cmap_for_flow_density = 'inferno_r' # Reversed inferno for export

                    # Use seaborn.kdeplot directly for the 2D density plot
                    # Removed 'y_range' as it causes an AttributeError in some matplotlib/seaborn versions
                    kde_plot = sns.kdeplot(x=flow_data_clipped, y=hour_of_day, fill=True,
                                           cmap=cmap_for_flow_density, cbar=True, # Enable colorbar directly
                                           cbar_kws={"label": "Density of Occurrences"}, # Label for the colorbar
                                           ax=ax, # Draw on the created axes
                                           clip=(0, None)) # Clip flow to non-negative. Note: clip takes x_range and y_range tuples.

                    # Set titles and labels
                    ax.set_xlabel(y_label) # Use dynamic y_label for x-axis
                    ax.set_ylabel("Hour of Day")
                    ax.set_title(f"{plot_title_suffix} Density Plot - {scenario_name}", y=1.02)

                    # Set specific ticks for hours and make x-ticks dynamic
                    ax.set_yticks(range(0, 24, 2)) # Hours from 0 to 23, step 2
                    ax.grid(True, linestyle='--', alpha=0.6)

                    # Ensure plot limits match desired ranges explicitly using set_ylim and set_xlim
                    ax.set_ylim(0, 23) # Set y-axis limits for hour of day
                    ax.set_xlim(left=0) # Ensure x-axis starts from 0 for power flows

                    plt.tight_layout(rect=[0, 0, 0.95, 0.98]) # Adjust rect for title and cbar

                    # Save to PDF (combined PDF for all plots)
                    pdf_all_flows.savefig(fig)

                    # Save to PNG (individual PNG for each plot)
                    png_path = os.path.join(scenario_output_dir, f"{scenario_name}_{flow_key}_Density_Plot.png")
                    fig.savefig(png_path, dpi=300)
                    all_global_png_files.append(png_path)
                    plt.close(fig) # Close the figure to free up memory

            except Exception as e:
                print(f"    An error occurred while processing {csv_path} for plotting: {e}")
                import traceback
                traceback.print_exc() # Print full traceback for debugging

    print(f"\nAll energy flow density plots saved to: {global_pdf_output_path}")

    # Optionally, zip all individual PNGs into a combined zip
    zip_path = os.path.join(base_output_dir, "All_Energy_Flow_Density_Plots.zip")
    if all_global_png_files:
        with ZipFile(zip_path, 'w') as zipf:
            for file_path in all_global_png_files:
                if os.path.exists(file_path):
                    zipf.write(file_path, arcname=os.path.basename(file_path))
                else:
                    print(f"    Warning: PNG file not found for zipping: {file_path}")
        print(f"All individual energy flow density plots zipped to: {zip_path}")
    else:
        print("No individual energy flow density plots were generated to zip.")


# --- 2. Global Configuration for Scenarios ---
script_dir = os.path.dirname(os.path.abspath(__file__))
base_output_directory = os.path.join(script_dir, "output") 

# This dictionary holds ALL available scenarios and their flow directories/files.
# 'capacity' is no longer needed as SOC calculations are excluded.
scenarios_config_flows_only = {
    "5kWh": {
        "flow_dir": os.path.join(script_dir, "flows"),
        "files": {
            'jan': 'flow_W_jan23.csv', 'feb': 'flow_W_feb23.csv', 'mar': 'flow_W_mar23.csv', 'apr': 'flow_W_apr23.csv',
            'may': 'flow_W_may23.csv', 'jun': 'flow_W_jun23.csv', 'jul': 'flow_W_jul23.csv', 'aug': 'flow_W_aug23.csv',
            'sep': 'flow_W_sep23.csv', 'oct': 'flow_W_oct23.csv', 'nov': 'flow_W_nov23.csv', 'dec': 'flow_W_dec23.csv'
        },
    },
    "NoBattery": {
        "flow_dir": os.path.join(script_dir, "flows_nobattery"),
        "files": {
            'jan': 'flow_NB_jan23.csv', 'feb': 'flow_NB_feb23.csv', 'mar': 'flow_NB_mar23.csv', 'apr': 'flow_NB_apr23.csv',
            'may': 'flow_NB_may23.csv', 'jun': 'flow_NB_jun23.csv', 'jul': 'flow_NB_jul23.csv', 'aug': 'flow_NB_aug23.csv',
            'sep': 'flow_NB_sep23.csv', 'oct': 'flow_NB_oct23.csv', 'nov': 'flow_NB_nov23.csv', 'dec': 'flow_NB_dec23.csv'
        },
    },
    "8kWh": {
        "flow_dir": os.path.join(script_dir, "flows_8k"),
        "files": {
            'jan': 'flow_8k_jan23.csv', 'feb': 'flow_8k_feb23.csv', 'mar': 'flow_8k_mar23.csv', 'apr': 'flow_8k_apr23.csv',
            'may': 'flow_8k_may23.csv', 'jun': 'flow_8k_jun23.csv', 'jul': 'flow_8k_jul23.csv', 'aug': 'flow_8k_aug23.csv',
            'sep': 'flow_8k_sep23.csv', 'oct': 'flow_8k_oct23.csv', 'nov': 'flow_8k_nov23.csv', 'dec': 'flow_8k_dec23.csv'
        },
    },
    "12kWh": {
        "flow_dir": os.path.join(script_dir, "flows_12k"),
        "files": {
            'jan': 'flow_12k_jan23.csv', 'feb': 'flow_12k_feb23.csv', 'mar': 'flow_12k_mar23.csv', 'apr': 'flow_12k_apr23.csv',
            'may': 'flow_12k_may23.csv', 'jun': 'flow_12k_jun23.csv', 'jul': 'flow_12k_jul23.csv', 'aug': 'flow_12k_aug23.csv',
            'sep': 'flow_12k_sep23.csv', 'oct': 'flow_12k_oct23.csv', 'nov': 'flow_12k_nov23.csv', 'dec': 'flow_12k_dec23.csv'
        },
    },
    "15kWh": {
        "flow_dir": os.path.join(script_dir, "flows_15k"),
        "files": {
            'jan': 'flow_15k_jan23.csv', 'feb': 'flow_15k_feb23.csv', 'mar': 'flow_15k_mar23.csv', 'apr': 'flow_15k_apr23.csv',
            'may': 'flow_15k_may23.csv', 'jun': 'flow_15k_jun23.csv', 'jul': 'flow_15k_jul23.csv', 'aug': 'flow_15k_aug23.csv',
            'sep': 'flow_15k_sep23.csv', 'oct': 'flow_15k_oct23.csv', 'nov': 'flow_15k_nov23.csv', 'dec': 'flow_15k_dec23.csv'
        },
    },
    "20kWh": {
        "flow_dir": os.path.join(script_dir, "flows_20k"),
        "files": {
            'jan': 'flow_20k_jan23.csv', 'feb': 'flow_20k_feb23.csv', 'mar': 'flow_20k_mar23.csv', 'apr': 'flow_20k_apr23.csv',
            'may': 'flow_20k_may23.csv', 'jun': 'flow_20k_jun23.csv', 'jul': 'flow_20k_jul23.csv', 'aug': 'flow_20k_aug23.csv',
            'sep': 'flow_20k_sep23.csv', 'oct': 'flow_20k_oct23.csv', 'nov': 'flow_20k_nov23.csv', 'dec': 'flow_20k_dec23.csv'
        },
    },
    "26kWh": {
        "flow_dir": os.path.join(script_dir, "flows_26k"),
        "files": {
            'jan': 'flow_26k_jan23.csv', 'feb': 'flow_26k_feb23.csv', 'mar': 'flow_26k_mar23.csv', 'apr': 'flow_26k_apr23.csv',
            'may': 'flow_26k_may23.csv', 'jun': 'flow_26k_jun23.csv', 'jul': 'flow_26k_jul23.csv', 'aug': 'flow_26k_aug23.csv',
            'sep': 'flow_26k_sep23.csv', 'oct': 'flow_26k_oct23.csv', 'nov': 'flow_26k_nov23.csv', 'dec': 'flow_26k_dec23.csv'
        },
    },
    "50kWh": {
        "flow_dir": os.path.join(script_dir, "flows_50k"),
        "files": {
            'jan': 'flow_50k_jan23.csv', 'feb': 'flow_50k_feb23.csv', 'mar': 'flow_50k_mar23.csv', 'apr': 'flow_50k_apr23.csv',
            'may': 'flow_50k_may23.csv', 'jun': 'flow_50k_jun23.csv', 'jul': 'flow_50k_jul23.csv', 'aug': 'flow_50k_aug23.csv',
            'sep': 'flow_50k_sep23.csv', 'oct': 'flow_50k_oct23.csv', 'nov': 'flow_50k_nov23.csv', 'dec': 'flow_50k_dec23.csv'
        },
    }
}


# --- 3. Main Execution Block ---
if __name__ == "__main__":
    os.makedirs(base_output_directory, exist_ok=True)

    # --- Argument Parsing for Scenario Selection ---
    parser = argparse.ArgumentParser(description="Generate energy flow density plots for specified scenarios.")
    parser.add_argument(
        "--scenarios",
        nargs='*', # 0 or more arguments
        help="Specify battery scenarios to plot (e.g., 5kWh 50kWh). If not provided, all scenarios will be plotted."
    )
    args = parser.parse_args()

    print(f"DEBUG: Parsed arguments object: {args}")
    print(f"DEBUG: Value of 'scenarios' argument: {args.scenarios}")

    # Determine which scenarios to plot based on arguments
    selected_scenarios_config = {}
    if args.scenarios:
        for s_name in args.scenarios:
            if s_name in scenarios_config_flows_only:
                selected_scenarios_config[s_name] = scenarios_config_flows_only[s_name]
            else:
                print(f"Warning: Scenario '{s_name}' not recognized or not found in configuration. Skipping.")
        
        if not selected_scenarios_config:
            print(f"Error: No valid scenarios found to plot from your input: {args.scenarios}.")
            print(f"Available scenarios are: {list(scenarios_config_flows_only.keys())}")
            exit()
        
        print(f"Plotting only the following specified scenarios: {list(selected_scenarios_config.keys())}")
    else:
        selected_scenarios_config = scenarios_config_flows_only
        print("No specific scenarios requested. Plotting density for all available scenarios.")

    # Call the main density plot generation function
    generate_flow_density_plots(base_output_directory, selected_scenarios_config)

    print("\nAll energy flow density plot generation completed.")
