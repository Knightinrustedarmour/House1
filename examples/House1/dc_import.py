import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from zipfile import ZipFile
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
import argparse # Import argparse for command-line argument parsing

# --- 1. Helper function to plot GENERIC FLOW duration curves ---
def export_generic_duration_curves(df, output_dir, scenario_name, flow_col_name, plot_title_prefix, y_label):
    """
    Generates and saves yearly and monthly duration curves for a specified power flow column.
    """
    pdf_path = os.path.join(output_dir, f"{flow_col_name}_Duration_Curves_{scenario_name}.pdf")
    png_files_for_zip = []

    if flow_col_name not in df.columns or df[flow_col_name].isnull().all():
        print(f"    Skipping {plot_title_prefix} duration curves for {scenario_name}: Data column '{flow_col_name}' not found or is empty.")
        return []

    with PdfPages(pdf_path) as pdf_duration_curves:
        # Yearly Duration Curve
        print(f"    Generating Yearly {plot_title_prefix} Duration Curve for {scenario_name}...")
        yearly_flow_data = df.sort_values(flow_col_name, ascending=False).reset_index(drop=True)
        duration_hours_yearly = np.arange(1, len(yearly_flow_data) + 1) / 60.0 # Data is in Wmin per minute, so divide by 60 for hours

        fig_yearly, ax_yearly = plt.subplots(figsize=(10, 10 * 13 / 21))
        ax_yearly.plot(duration_hours_yearly, yearly_flow_data[flow_col_name], label=scenario_name) # Added label for potential future use
        ax_yearly.set_xlabel("Duration (Hours)")
        ax_yearly.set_ylabel(y_label)
        ax_yearly.set_title(f"Yearly {plot_title_prefix} Duration Curve - {scenario_name}")
        ax_yearly.grid(True)
        plt.tight_layout()
        pdf_duration_curves.savefig(fig_yearly)
        png_path_yearly = os.path.join(output_dir, f"{scenario_name}_Yearly_{flow_col_name}_Duration_Curve.png")
        fig_yearly.savefig(png_path_yearly, dpi=300)
        png_files_for_zip.append(png_path_yearly)
        plt.close(fig_yearly)

        # Monthly Duration Curves
        for month_name in df["Month"].unique():
            print(f"    Generating Monthly {plot_title_prefix} Duration Curve for {scenario_name} - {month_name}...")
            month_df = df[df["Month"] == month_name].copy()
            month_df = month_df.sort_values(flow_col_name, ascending=False).reset_index(drop=True)

            duration_hours_monthly = np.arange(1, len(month_df) + 1) / 60.0

            fig_monthly, ax_monthly = plt.subplots(figsize=(10, 10 * 13 / 21))
            ax_monthly.plot(duration_hours_monthly, month_df[flow_col_name])
            ax_monthly.set_xlabel("Duration (Hours of the month)")
            ax_monthly.set_ylabel(y_label)
            ax_monthly.set_title(f"{plot_title_prefix} Duration Curve - {scenario_name} - {month_name}")
            ax_monthly.grid(True)
            plt.tight_layout()
            pdf_duration_curves.savefig(fig_monthly)
            png_path_monthly = os.path.join(output_dir, f"{scenario_name}_{month_name}_{flow_col_name}_Duration_Curve.png")
            fig_monthly.savefig(png_path_monthly, dpi=300)
            png_files_for_zip.append(png_path_monthly)
            plt.close(fig_monthly)

    return png_files_for_zip


# --- 2. Helper function to plot GENERIC FLOW heatmaps ---
def export_generic_flow_heatmaps(df, output_dir, scenario_name, flow_col_name, plot_title_suffix, cmap='viridis'):
    """
    Generates and saves monthly heatmaps for a specified power flow column.
    """
    heatmap_pdf_path = os.path.join(output_dir, f"{flow_col_name}_Heatmaps_{scenario_name}.pdf")
    png_files_for_zip = []

    if flow_col_name not in df.columns or df[flow_col_name].isnull().all():
        print(f"    Skipping {plot_title_suffix} heatmaps for {scenario_name}: Data column '{flow_col_name}' not found or is empty.")
        return []

    with PdfPages(heatmap_pdf_path) as pdf_heatmaps:
        for month_name in df["Month"].unique():
            print(f"    Generating {plot_title_suffix} Heatmap for {scenario_name} - {month_name}...")
            month_df = df[df["Month"] == month_name].copy()

            # Resample from Wmin (per minute) to Wh (per hour) for heatmaps
            # Sum Wmin over an hour (60 minutes) and then convert to Wh by dividing by 60.
            flow_hourly_wh = month_df[flow_col_name].resample('H').sum() / 60.0

            hourly_data = pd.DataFrame({
                'Value': flow_hourly_wh.values
            }, index=flow_hourly_wh.index)
            hourly_data['hour'] = hourly_data.index.hour
            hourly_data['day'] = hourly_data.index.day

            pivot_table = hourly_data.pivot_table(index='hour', columns='day', values='Value').fillna(0)

            fig, ax = plt.subplots(figsize=(12, 12 * 13 / 21))

            max_val = pivot_table.max().max()
            min_val = pivot_table.min().min()

            if max_val == 0 and min_val == 0: # Check if all values are zero
                print(f"        No {plot_title_suffix} data for {scenario_name} - {month_name}. Heatmap will be empty.")
                sns.heatmap(pivot_table, cmap="Greys", annot=False, fmt=".0f",
                            linewidths=.5, ax=ax, cbar=False)
            else:
                # For single-directional flows (like PV production, Demand, Grid Import/Export),
                # use a sequential colormap. Set vmin to 0 for flows that are typically non-negative.
                sns.heatmap(pivot_table, cmap=cmap, annot=False, fmt=".0f",
                            linewidths=.5, ax=ax, vmin=0, vmax=max_val) # Set vmin=0 for positive flows

            ax.set_title(f"{plot_title_suffix} Heatmap (Wh/Hour) - {scenario_name} - {month_name}")
            ax.set_xlabel("Day of Month")
            ax.set_ylabel("Hour of Day")
            plt.tight_layout()
            pdf_heatmaps.savefig(fig)
            png_path = os.path.join(output_dir, f"{scenario_name}_{month_name}_{flow_col_name}_Heatmap.png")
            fig.savefig(png_path, dpi=300)
            png_files_for_zip.append(png_path)
            plt.close(fig)

    return png_files_for_zip


# --- 3. Helper function to plot combined yearly GENERIC FLOW duration curve ---
def export_combined_yearly_flow_duration_curve(all_scenarios_yearly_dfs, output_dir, flow_key, plot_title_prefix, y_label):
    """
    Generates and saves a single plot with yearly duration curves for a specific flow type
    across all specified scenarios.
    """
    combined_pdf_path = os.path.join(output_dir, f"Combined_Yearly_{flow_key}_Duration_Curves.pdf")
    combined_png_path = os.path.join(output_dir, f"Combined_Yearly_{flow_key}_Duration_Curves.png")

    print(f"\n--- Generating Combined Yearly {plot_title_prefix} Duration Curve for all scenarios ---")

    fig, ax = plt.subplots(figsize=(12, 12 * 13 / 21))
    plotted_any_data = False

    for scenario_name, yearly_df in all_scenarios_yearly_dfs.items():
        flow_col_name_in_df = f"{flow_key}_W_{scenario_name}"
        
        # Ensure the DataFrame has the flow column and it's not all NaNs, and there's activity
        if flow_col_name_in_df in yearly_df.columns and \
           not yearly_df[flow_col_name_in_df].isnull().all() and \
           yearly_df[flow_col_name_in_df].sum() > 0:
            
            sorted_flow_data = yearly_df.sort_values(flow_col_name_in_df, ascending=False).reset_index(drop=True)
            duration_hours = np.arange(1, len(sorted_flow_data) + 1) / 60.0
            ax.plot(duration_hours, sorted_flow_data[flow_col_name_in_df], label=scenario_name)
            plotted_any_data = True
        else:
            print(f"    Skipping {scenario_name} for combined {plot_title_prefix} plot: No valid data found or no activity.")

    if plotted_any_data:
        ax.set_xlabel("Duration (Hours)")
        ax.set_ylabel(y_label)
        ax.set_title(f"Combined Yearly {plot_title_prefix} Duration Curves for All Scenarios")
        ax.grid(True)
        # Use reasonable limits for power flows, e.g., starting at 0
        ax.set_ylim(bottom=0)
        ax.legend(title="Scenario")
        plt.tight_layout()

        # Save to PDF
        with PdfPages(combined_pdf_path) as pdf:
            pdf.savefig(fig)
        print(f"Combined yearly {plot_title_prefix} duration curve saved to: {combined_pdf_path}")

        # Save to PNG
        fig.savefig(combined_png_path, dpi=300)
        print(f"Combined yearly {plot_title_prefix} duration curve saved to: {combined_png_path}")
    else:
        print(f"No scenarios found with valid {plot_title_prefix} data for combined yearly duration curve. Skipping combined plot.")

    plt.close(fig)


# --- 4. Main Processing Function (No SOC Calculation) ---
def process_scenario_data(scenario_name, flow_dir, file_dict):
    """
    Processes data for a single scenario, extracts energy flows,
    generates heatmaps and duration curves for various energy flows,
    and saves combined data and plots.
    """
    print(f"\n--- Processing {scenario_name} Scenario ---")

    scenario_output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", scenario_name)
    os.makedirs(scenario_output_dir, exist_ok=True)

    all_monthly_dfs = []

    for month_abbr, filename in file_dict.items():
        filepath = os.path.join(flow_dir, filename)

        if not os.path.exists(filepath):
            print(f"    Warning: File not found: {filepath}. Skipping {month_abbr} for {scenario_name}.")
            continue

        try:
            # Read the CSV with multi-level headers
            results = pd.read_csv(filepath, header=[0, 1], index_col=0)
            results.index = pd.to_datetime(results.index, utc=True)

            monthly_data = pd.DataFrame(index=results.index)

            # --- Extract all specified flow columns ---
            for flow_key, col_path in column_paths.items():
                if col_path in results.columns:
                    monthly_data[f"{flow_key}_W_{scenario_name}"] = results[col_path].squeeze()
                    # Ensure non-negative values for flows that are typically positive
                    if flow_key in ["Battery_charge", "Battery_discharge", "PV_production", "PV_distribution",
                                    "Demand2", "Grid_import", "Grid_export"]:
                        monthly_data[f"{flow_key}_W_{scenario_name}"] = monthly_data[f"{flow_key}_W_{scenario_name}"].clip(lower=0)
                else:
                    print(f"    Note: Flow column '{flow_key}' with path '{col_path}' not found in {filename} for {scenario_name}. Filling with zeros.")
                    monthly_data[f"{flow_key}_W_{scenario_name}"] = 0.0 # Assign 0.0 to indicate no flow

            monthly_data['Month'] = month_abbr.capitalize()
            all_monthly_dfs.append(monthly_data)

            print(f"    Processed {filename} for {scenario_name}")

        except KeyError as e:
            print(f"    Error: Missing expected column in {filename} for {scenario_name}. Error: {e}")
        except Exception as e:
            print(f"    An unexpected error occurred while processing {filepath}: {e}")

    if not all_monthly_dfs:
        print(f"No data was processed for {scenario_name}. Skipping plotting and CSV export.")
        return None

    yearly_df = pd.concat(all_monthly_dfs)

    output_csv_path = os.path.join(scenario_output_dir, f"Combined_All_Flow_Data_{scenario_name}.csv")
    yearly_df.to_csv(output_csv_path)
    print(f"Combined all flow data for {scenario_name} exported to: {output_csv_path}")

    # Generate plots for this scenario
    print(f"\n--- Generating plots for {scenario_name} ---")
    all_png_files_scenario = []

    # --- Generate plots for selected flows (PV_distribution, Demand2, Grid_import, Grid_export, and Battery flows) ---
    # Include Battery_charge and Battery_discharge for individual plots too if needed
    flows_to_plot_individual = {
        "Battery_charge": "Battery Charging Power",
        "Battery_discharge": "Battery Discharging Power",
        "PV_production": "PV Production", # Added PV_production to individual plots
        "PV_distribution": "PV Self-Consumption",
        "Demand2": "Electricity Demand",
        "Grid_import": "Grid Import",
        "Grid_export": "Grid Export"
    }

    for flow_key, plot_title_suffix in flows_to_plot_individual.items():
        flow_col_name_in_df = f"{flow_key}_W_{scenario_name}"
        
        y_label = "Power (W)"
        if flow_key == "Demand2":
            y_label = "Demand (W)"
        elif "PV" in flow_key:
            y_label = "PV Power (W)"
        elif "Grid" in flow_key:
            y_label = "Grid Power (W)"
        
        # Duration Curves (individual scenario)
        if flow_col_name_in_df in yearly_df.columns and \
           not yearly_df[flow_col_name_in_df].isnull().all() and \
           yearly_df[flow_col_name_in_df].sum() > 0: # Only plot if there's actual activity
            duration_df = yearly_df[[flow_col_name_in_df, 'Month']].copy()
            all_png_files_scenario.extend(
                export_generic_duration_curves(
                    duration_df, scenario_output_dir, scenario_name,
                    flow_col_name_in_df, plot_title_suffix, y_label
                )
            )
        else:
            print(f"    Skipping {plot_title_suffix} duration curves for {scenario_name}: Data not available, all NaNs, or no activity.")

        # Heatmaps (individual scenario)
        if flow_col_name_in_df in yearly_df.columns and \
           not yearly_df[flow_col_name_in_df].isnull().all() and \
           yearly_df[flow_col_name_in_df].sum() > 0: # Only plot if there's actual activity
            cmap_for_flow = 'viridis' # Default
            if flow_key == "Demand2":
                cmap_for_flow = 'plasma'
            elif flow_key == "Grid_import":
                cmap_for_flow = 'magma'
            elif flow_key == "Grid_export":
                cmap_for_flow = 'inferno_r'
            elif flow_key in ["Battery_charge", "Battery_discharge"]: # Use a distinct cmap for battery flows
                cmap_for_flow = 'Blues' if flow_key == "Battery_charge" else 'Reds_r' # Example: Blues for charge, reversed Reds for discharge

            all_png_files_scenario.extend(
                export_generic_flow_heatmaps(
                    yearly_df, scenario_output_dir, scenario_name,
                    flow_col_name_in_df, plot_title_suffix, cmap=cmap_for_flow
                )
            )
        else:
            print(f"    Skipping {plot_title_suffix} heatmaps for {scenario_name}: Data not available, all NaNs, or no activity.")


    # Create a zip archive of all generated PNGs for the scenario
    if all_png_files_scenario:
        zip_path = os.path.join(scenario_output_dir, f"{scenario_name}_All_Plots.zip")
        with ZipFile(zip_path, 'w') as zipf:
            for file_path in all_png_files_scenario:
                if os.path.exists(file_path):
                    zipf.write(file_path, arcname=os.path.basename(file_path))
                else:
                    print(f"    Warning: PNG file not found for zipping: {file_path}")
        print(f"All plots for {scenario_name} zipped to: {zip_path}")
    else:
        print(f"No plots generated for {scenario_name} to zip.")
    
    return yearly_df # Return the full yearly_df for main execution to use


# --- Global Configuration ---
script_dir = os.path.dirname(os.path.abspath(__file__))

column_paths = {
    # All flow paths are kept for data extraction
    "Battery_charge": ("SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='distribution')", "SolphLabel(location='House1', mtress_component='storage1', solph_node='Battery_Storage')"),
    "Battery_discharge": ("SolphLabel(location='House1', mtress_component='storage1', solph_node='Battery_Storage')", "SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='distribution')"),
    "PV_production": ("SolphLabel(location='House1', mtress_component='PV', solph_node='source')", "SolphLabel(location='House1', mtress_component='PV', solph_node='connection')"),
    "PV_distribution": ("SolphLabel(location='House1', mtress_component='PV', solph_node='connection')", "SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='distribution')"),
    "Demand2": ("SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='distribution')", "SolphLabel(location='House1', mtress_component='demand', solph_node='input')"),
    "Grid_import": ("SolphLabel(location='House1', mtress_component='ElectricityGridConnection', solph_node='grid_import')", "SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='distribution')"),
    "Grid_export": ("SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='feed_in')", "SolphLabel(location='House1', mtress_component='ElectricityGridConnection', solph_node='grid_export')")
}

# Scenarios configuration - capacity is removed as SOC calculation is not in this script.
scenarios_config = {
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


# --- 5. Main Execution ---
if __name__ == "__main__":
    base_output_directory = os.path.join(script_dir, "output")
    os.makedirs(base_output_directory, exist_ok=True)

    # --- Argument Parsing for Scenario Selection ---
    parser = argparse.ArgumentParser(description="Generate plots for energy flows across specified battery scenarios.")
    # Add a new argument for 'only_combined_plots'
    parser.add_argument(
        "--only-combined-plots",
        action="store_true", # This makes it a boolean flag
        help="If set, only generates the combined yearly duration curves by loading existing CSVs. Skips individual scenario processing."
    )
    parser.add_argument(
        "--scenarios",
        nargs='*', # 0 or more arguments
        help="Specify battery scenarios to process (e.g., 5kWh 50kWh). If not provided, all scenarios will be processed."
    )
    args = parser.parse_args()

    print(f"DEBUG: Parsed arguments object: {args}")
    print(f"DEBUG: Value of 'scenarios' argument: {args.scenarios}")
    print(f"DEBUG: Value of 'only_combined_plots' argument: {args.only_combined_plots}")

    # Determine which scenarios to process based on arguments
    selected_scenarios_config = {}
    if args.scenarios:
        for s_name in args.scenarios:
            if s_name in scenarios_config:
                selected_scenarios_config[s_name] = scenarios_config[s_name]
            else:
                print(f"Warning: Scenario '{s_name}' not recognized or not found in configuration. Skipping.")
        
        if not selected_scenarios_config:
            print(f"Error: No valid scenarios found to process from your input: {args.scenarios}.")
            print(f"Available scenarios are: {list(scenarios_config.keys())}")
            exit()
        
        print(f"Processing only the following specified scenarios: {list(selected_scenarios_config.keys())}")
    else:
        selected_scenarios_config = scenarios_config
        print("No specific scenarios requested. Processing all available scenarios.")

    # Dictionary to store yearly DataFrames for combined plots
    all_scenarios_yearly_dfs = {}

    if args.only_combined_plots:
        print("\n--- Running in 'Only Combined Plots' mode ---")
        print("Attempting to load data from existing 'Combined_All_Flow_Data_*.csv' files in output directories.")
        # Load data from existing CSVs if running in 'only-combined-plots' mode
        for name in selected_scenarios_config.keys():
            scenario_output_dir = os.path.join(base_output_directory, name)
            output_csv_path = os.path.join(scenario_output_dir, f"Combined_All_Flow_Data_{name}.csv")
            if os.path.exists(output_csv_path):
                try:
                    df_loaded = pd.read_csv(output_csv_path, index_col=0, parse_dates=True)
                    all_scenarios_yearly_dfs[name] = df_loaded
                    print(f"    Successfully loaded data for scenario: {name}")
                except Exception as e:
                    print(f"    Error loading data for scenario {name} from {output_csv_path}: {e}")
            else:
                print(f"    Warning: CSV file not found for scenario {name} at {output_csv_path}. Skipping this scenario for combined plots.")
        
        if not all_scenarios_yearly_dfs:
            print("No data could be loaded for any selected scenarios. Please ensure CSVs exist or run without '--only-combined-plots'.")
            exit()

    else: # Normal processing mode: process data and generate all plots (individual and combined)
        # --- Loop through selected scenarios and process data/generate individual plots ---
        for name, config in selected_scenarios_config.items():
            # process_scenario_data now returns the full yearly_df
            yearly_df_for_scenario = process_scenario_data(name, config["flow_dir"], config["files"])
            
            if yearly_df_for_scenario is not None:
                all_scenarios_yearly_dfs[name] = yearly_df_for_scenario
            
    # --- Generate Combined Yearly Duration Curves for specified flows ---
    # This block runs regardless of `only_combined_plots` as long as data is available
    combined_flows_to_plot = {
        "PV_distribution": "PV Self-Consumption",
        "Demand2": "Electricity Demand",
        "Grid_import": "Grid Import",
        "Grid_export": "Grid Export",
        
    }

    if not all_scenarios_yearly_dfs:
        print("No scenario data available for generating combined yearly duration curves. Skipping combined plots.")
    else:
        for flow_key, plot_title_prefix in combined_flows_to_plot.items():
            y_label = "Power (W)"
            if flow_key == "Demand2":
                y_label = "Demand (W)"
            elif "PV" in flow_key:
                y_label = "PV Power (W)"
            elif "Grid" in flow_key:
                y_label = "Grid Power (W)"
            

            export_combined_yearly_flow_duration_curve(
                all_scenarios_yearly_dfs, base_output_directory,
                flow_key, plot_title_prefix, y_label
            )

    print("\nAll energy flow data processing, CSV export, and plot generation completed.")