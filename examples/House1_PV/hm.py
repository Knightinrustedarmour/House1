import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def generate_monthly_heatmaps(scenario_identifier, scenario_config):
    """
    Generates monthly heatmaps for key energy flows.
    """
    
    ALL_FLOWS = {
        "Demand_Consumption": [
            ("SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='distribution')", "SolphLabel(location='House1', mtress_component='demand', solph_node='input')"),
            ("('House1', 'ElectricityCarrier', 'distribution')", "('House1', 'demand', 'input')")
        ],
        "Battery_Charge": [
            ("SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='distribution')", "SolphLabel(location='House1', mtress_component='storage1', solph_node='Battery_Storage')"),
            ("('House1', 'ElectricityCarrier', 'distribution')", "('House1', 'storage1', 'Battery_Storage')")
        ],
        "Grid_Export_to_Grid": [
            ("SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='feed_in')", "SolphLabel(location='House1', mtress_component='ElectricityGridConnection', solph_node='grid_export')"),
            ("('House1', 'ElectricityCarrier', 'feed_in')", "('House1', 'ElectricityGridConnection', 'grid_export')")
        ],
        "Grid_Export_Sink": [
            ("SolphLabel(location='House1', mtress_component='ElectricityGridConnection', solph_node='grid_export')", "SolphLabel(location='House1', mtress_component='ElectricityGridConnection', solph_node='sink_export')"),
            ("('House1', 'ElectricityGridConnection', 'grid_export')", "('House1', 'ElectricityGridConnection', 'sink_export')")
        ],
        "Grid_Import": [
            ("SolphLabel(location='House1', mtress_component='ElectricityGridConnection', solph_node='grid_import')", "SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='distribution')"),
            ("('House1', 'ElectricityGridConnection', 'grid_import')", "('House1', 'ElectricityCarrier', 'distribution')")
        ],
        "Grid_Import_Source": [
            ("SolphLabel(location='House1', mtress_component='ElectricityGridConnection', solph_node='source_import')", "SolphLabel(location='House1', mtress_component='ElectricityGridConnection', solph_node='grid_import')"),
            ("('House1', 'ElectricityGridConnection', 'source_import')", "('House1', 'ElectricityGridConnection', 'grid_import')")
        ],
        "PV_Direct_Consumption": [
            ("SolphLabel(location='House1', mtress_component='PV', solph_node='connection')", "SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='distribution')"),
            ("('House1', 'PV', 'connection')", "('House1', 'ElectricityCarrier', 'distribution')")
        ],
        "PV_to_Grid_Feedin": [
            ("SolphLabel(location='House1', mtress_component='PV', solph_node='connection')", "SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='feed_in')"),
            ("('House1', 'PV', 'connection')", "('House1', 'ElectricityCarrier', 'feed_in')")
        ],
        "Total_PV_Production": [
            ("SolphLabel(location='House1', mtress_component='PV', solph_node='source')", "SolphLabel(location='House1', mtress_component='PV', solph_node='connection')"),
            ("('House1', 'PV', 'source')", "('House1', 'PV', 'connection')")
        ],
        "Demand_Sink": [
            ("SolphLabel(location='House1', mtress_component='demand', solph_node='input')", "SolphLabel(location='House1', mtress_component='demand', solph_node='sink')"),
            ("('House1', 'demand', 'input')", "('House1', 'demand', 'sink')")
        ],
        "Battery_Discharge": [
            ("SolphLabel(location='House1', mtress_component='storage1', solph_node='Battery_Storage')", "SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='distribution')"),
            ("('House1', 'storage1', 'Battery_Storage')", "('House1', 'ElectricityCarrier', 'distribution')")
        ],
        "PV2_Direct_Consumption": [
            ("SolphLabel(location='House1', mtress_component='PV2', solph_node='connection')", "SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='distribution')"),
            ("('House1', 'PV2', 'connection')", "('House1', 'ElectricityCarrier', 'distribution')")
        ],
        "PV2_to_Grid_Feedin": [
            ("SolphLabel(location='House1', mtress_component='PV2', solph_node='connection')", "SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='feed_in')"),
            ("('House1', 'PV2', 'connection')", "('House1', 'ElectricityCarrier', 'feed_in')")
        ],
        "Total_PV2_Production": [
            ("SolphLabel(location='House1', mtress_component='PV2', solph_node='source')", "SolphLabel(location='House1', mtress_component='PV2', solph_node='connection')"),
            ("('House1', 'PV2', 'source')", "('House1', 'PV2', 'connection')")
        ]
    }
    
    for month, filename in scenario_config["files"].items():
        filepath = os.path.join(scenario_config["flow_dir"], filename)
        if not os.path.exists(filepath):
            print(f"File not found: {filepath}. Skipping.")
            continue
        
        try:
            # Read the CSV without setting the index initially
            df = pd.read_csv(filepath, header=[0, 1])
            
            # Use iloc to select the first column, convert to datetime, and set it as the index
            df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0], errors='coerce')
            df.set_index(df.columns[0], inplace=True)
            
            plot_data = pd.DataFrame(index=df.index)
            plot_data['Time'] = df.index.hour + df.index.minute / 60
            plot_data['Day'] = df.index.day
            
            flows_to_plot = {
                "Grid_Import": ["Grid_Import"],
                "Total_Grid_Export": ["Grid_Export_to_Grid", "PV_to_Grid_Feedin", "PV2_to_Grid_Feedin"],
                "Battery_Discharge": ["Battery_Discharge"]
            }

            for flow_name, base_flows in flows_to_plot.items():
                flow_values = pd.Series(0.0, index=df.index)
                for base_flow in base_flows:
                    for solph_label_tuple in ALL_FLOWS.get(base_flow, []):
                        try:
                            flow_values += df[solph_label_tuple]
                            break
                        except KeyError:
                            continue

                if flow_values.sum() == 0 and flow_name != "Total_Grid_Export":
                    print(f"Skipping heatmap for {flow_name} in {month} as data is zero.")
                    continue
                
                plot_data[flow_name] = flow_values
                
                output_dir = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    "output", 
                    "heatmaps",
                    scenario_identifier,
                    month
                )
                os.makedirs(output_dir, exist_ok=True)

                heatmap_data = plot_data.pivot_table(
                    index='Time',
                    columns='Day',
                    values=flow_name,
                    aggfunc='sum'
                )
                
                plt.figure(figsize=(12, 8))
                ax = sns.heatmap(
                    heatmap_data, 
                    cmap="viridis",
                    cbar_kws={'label': f'{flow_name} (Wh)'}
                )
                ax.set_title(f'{flow_name} Heatmap for {month} ({scenario_identifier})')
                ax.set_xlabel('Day of Month')
                ax.set_ylabel('Time of Day (hr)')
                plt.savefig(os.path.join(output_dir, f'heatmap_{flow_name}_{month}.png'))
                plt.close()
                print(f"Generated heatmap for {flow_name} in {month}.")
        
        except Exception as e:
            print(f"Error processing {filepath}: {e}. Skipping plots for this file.")
            continue

# --- Core Script Execution ---
if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    scenarios_config = {
        "PV_NoBattery": { "flow_dir": os.path.join(script_dir, "flows"), "files": { 'jan': 'flow_nobattery_jan23.csv', 'feb': 'flow_nobattery_feb23.csv', 'mar': 'flow_nobattery_mar23.csv', 'apr': 'flow_nobattery_apr23.csv', 'may': 'flow_nobattery_may23.csv', 'jun': 'flow_nobattery_jun23.csv', 'jul': 'flow_nobattery_jul23.csv', 'aug': 'flow_nobattery_aug23.csv', 'sep': 'flow_nobattery_sep23.csv', 'oct': 'flow_nobattery_oct23.csv', 'nov': 'flow_nobattery_nov23.csv', 'dec': 'flow_nobattery_dec23.csv' } },
        "5kWh": { "flow_dir": os.path.join(script_dir, "flows"), "files": { 'jan': 'flow_5k_jan23.csv', 'feb': 'flow_5k_feb23.csv', 'mar': 'flow_5k_mar23.csv', 'apr': 'flow_5k_apr23.csv', 'may': 'flow_5k_may23.csv', 'jun': 'flow_5k_jun23.csv', 'jul': 'flow_5k_jul23.csv', 'aug': 'flow_5k_aug23.csv', 'sep': 'flow_5k_sep23.csv', 'oct': 'flow_5k_oct23.csv', 'nov': 'flow_5k_nov23.csv', 'dec': 'flow_5k_dec23.csv' } },
        "8kWh": { "flow_dir": os.path.join(script_dir, "flows"), "files": { 'jan': 'flow_8k_jan23.csv', 'feb': 'flow_8k_feb23.csv', 'mar': 'flow_8k_mar23.csv', 'apr': 'flow_8k_apr23.csv', 'may': 'flow_8k_may23.csv', 'jun': 'flow_8k_jun23.csv', 'jul': 'flow_8k_jul23.csv', 'aug': 'flow_8k_aug23.csv', 'sep': 'flow_8k_sep23.csv', 'oct': 'flow_8k_oct23.csv', 'nov': 'flow_8k_nov23.csv', 'dec': 'flow_8k_dec23.csv' } },
        "12kWh": { "flow_dir": os.path.join(script_dir, "flows"), "files": { 'jan': 'flow_12k_jan23.csv', 'feb': 'flow_12k_feb23.csv', 'mar': 'flow_12k_mar23.csv', 'apr': 'flow_12k_apr23.csv', 'may': 'flow_12k_may23.csv', 'jun': 'flow_12k_jun23.csv', 'jul': 'flow_12k_jul23.csv', 'aug': 'flow_12k_aug23.csv', 'sep': 'flow_12k_sep23.csv', 'oct': 'flow_12k_oct23.csv', 'nov': 'flow_12k_nov23.csv', 'dec': 'flow_12k_dec23.csv' } },
        "15kWh": { "flow_dir": os.path.join(script_dir, "flows"), "files": { 'jan': 'flow_15k_jan23.csv', 'feb': 'flow_15k_feb23.csv', 'mar': 'flow_15k_mar23.csv', 'apr': 'flow_15k_apr23.csv', 'may': 'flow_15k_may23.csv', 'jun': 'flow_15k_jun23.csv', 'jul': 'flow_15k_jul23.csv', 'aug': 'flow_15k_aug23.csv', 'sep': 'flow_15k_sep23.csv', 'oct': 'flow_15k_oct23.csv', 'nov': 'flow_15k_nov23.csv', 'dec': 'flow_15k_dec23.csv' } },
        "20kWh": { "flow_dir": os.path.join(script_dir, "flows"), "files": { 'jan': 'flow_20k_jan23.csv', 'feb': 'flow_20k_feb23.csv', 'mar': 'flow_20k_mar23.csv', 'apr': 'flow_20k_apr23.csv', 'may': 'flow_20k_may23.csv', 'jun': 'flow_20k_jun23.csv', 'jul': 'flow_20k_jul23.csv', 'aug': 'flow_20k_aug23.csv', 'sep': 'flow_20k_sep23.csv', 'oct': 'flow_20k_oct23.csv', 'nov': 'flow_20k_nov23.csv', 'dec': 'flow_20k_dec23.csv' } },
        "26kWh": { "flow_dir": os.path.join(script_dir, "flows"), "files": { 'jan': 'flow_26k_jan23.csv', 'feb': 'flow_26k_feb23.csv', 'mar': 'flow_26k_mar23.csv', 'apr': 'flow_26k_apr23.csv', 'may': 'flow_26k_may23.csv', 'jun': 'flow_26k_jun23.csv', 'jul': 'flow_26k_jul23.csv', 'aug': 'flow_26k_aug23.csv', 'sep': 'flow_26k_sep23.csv', 'oct': 'flow_26k_oct23.csv', 'nov': 'flow_26k_nov23.csv', 'dec': 'flow_26k_dec23.csv' } },
        "50kWh": { "flow_dir": os.path.join(script_dir, "flows"), "files": { 'jan': 'flow_50k_jan23.csv', 'feb': 'flow_50k_feb23.csv', 'mar': 'flow_50k_mar23.csv', 'apr': 'flow_50k_apr23.csv', 'may': 'flow_50k_may23.csv', 'jun': 'flow_50k_jun23.csv', 'jul': 'flow_50k_jul23.csv', 'aug': 'flow_50k_aug23.csv', 'sep': 'flow_50k_sep23.csv', 'oct': 'flow_50k_oct23.csv', 'nov': 'flow_50k_nov23.csv', 'dec': 'flow_50k_dec23.csv' } }
    }

    scenarios_to_plot = list(scenarios_config.keys())

    for scenario_identifier in scenarios_to_plot:
        print(f"\n--- Generating heatmaps for scenario: {scenario_identifier} ---")
        generate_monthly_heatmaps(scenario_identifier, scenarios_config[scenario_identifier])
    
    print("\nHeatmap generation complete. Check the 'output/heatmaps' directory.")