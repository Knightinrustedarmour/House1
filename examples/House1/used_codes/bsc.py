import os
import pandas as pd
import matplotlib.pyplot as plt

def create_annual_dataframe(scenario_config, flow_name):
    """
    Reads monthly flow data and concatenates it into a single annual DataFrame.
    """
    ALL_FLOWS = {
        "Grid_Import": [
            ("SolphLabel(location='House1', mtress_component='ElectricityGridConnection', solph_node='grid_import')", "SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='distribution')"),
            ("('House1', 'ElectricityGridConnection', 'grid_import')", "('House1', 'ElectricityCarrier', 'distribution')")
        ],
        "PV_Direct_Consumption": [
            ("SolphLabel(location='House1', mtress_component='PV', solph_node='connection')", "SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='distribution')"),
            ("('House1', 'PV', 'connection')", "('House1', 'ElectricityCarrier', 'distribution')")
        ],
        "PV_to_Grid_Feedin": [
            ("SolphLabel(location='House1', mtress_component='PV', solph_node='connection')", "SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='feed_in')"),
            ("('House1', 'PV', 'connection')", "('House1', 'ElectricityCarrier', 'feed_in')")
        ]
    }
    
    if flow_name not in ALL_FLOWS:
        print(f"Error: Requested flow '{flow_name}' is not defined. Skipping.")
        return pd.DataFrame()

    monthly_series_list = []
    
    for filename in scenario_config["files"].values():
        filepath = os.path.join(scenario_config["flow_dir"], filename)
        if not os.path.exists(filepath):
            print(f"File not found: {filepath}. Skipping.")
            continue
        try:
            monthly_data = pd.read_csv(filepath, header=[0, 1], index_col=0)
            flow_data_found = False
            for header_tuple in ALL_FLOWS[flow_name]:
                if header_tuple in monthly_data.columns:
                    series = monthly_data[header_tuple].copy()
                    series.index = pd.to_datetime(series.index, utc=True)
                    series.name = flow_name
                    monthly_series_list.append(series)
                    flow_data_found = True
                    break
            if not flow_data_found:
                print(f"Flow path for '{flow_name}' not found in file: {filepath}. Skipping.")
        except Exception as e:
            print(f"Error reading {filepath}: {e}. Skipping file.")
    
    if monthly_series_list:
        annual_data = pd.concat(monthly_series_list).sort_index()
        return annual_data
    else:
        print(f"No data was processed for flow: {flow_name} in scenario: {scenario_config.get('display_name', 'Unknown')}.")
        return pd.DataFrame()

# --- Core Script Execution ---
if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "output", "plots")
    os.makedirs(output_dir, exist_ok=True)
    
    scenarios_config = {
        "NoPV": {
            "flow_dir": os.path.join(script_dir, "flows_nopv"),
            "files": {
                'jan': 'flow_nopv_jan23.csv', 'feb': 'flow_nopv_feb23.csv', 'mar': 'flow_nopv_mar23.csv',
                'apr': 'flow_nopv_apr23.csv', 'may': 'flow_nopv_may23.csv', 'jun': 'flow_nopv_jun23.csv',
                'jul': 'flow_nopv_jul23.csv', 'aug': 'flow_nopv_aug23.csv', 'sep': 'flow_nopv_sep23.csv',
                'oct': 'flow_nopv_oct23.csv', 'nov': 'flow_nopv_nov23.csv', 'dec': 'flow_nopv_dec23.csv'
            },
            "display_name": "No PV"
        },
        "12kWh": {
            "flow_dir": os.path.join(script_dir, "flows_12k"),
            "files": {
                'jan': 'flow_12k_jan23.csv', 'feb': 'flow_12k_feb23.csv', 'mar': 'flow_12k_mar23.csv',
                'apr': 'flow_12k_apr23.csv', 'may': 'flow_12k_may23.csv', 'jun': 'flow_12k_jun23.csv',
                'jul': 'flow_12k_jul23.csv', 'aug': 'flow_12k_aug23.csv', 'sep': 'flow_12k_sep23.csv',
                'oct': 'flow_12k_oct23.csv', 'nov': 'flow_12k_nov23.csv', 'dec': 'flow_12k_dec23.csv'
            },
            "display_name": "Battery (12kWh)"
        },
        "15kWh": {
            "flow_dir": os.path.join(script_dir, "flows_15k"),
            "files": {
                'jan': 'flow_15k_jan23.csv', 'feb': 'flow_15k_feb23.csv', 'mar': 'flow_15k_mar23.csv',
                'apr': 'flow_15k_apr23.csv', 'may': 'flow_15k_may23.csv', 'jun': 'flow_15k_jun23.csv',
                'jul': 'flow_15k_jul23.csv', 'aug': 'flow_15k_aug23.csv', 'sep': 'flow_15k_sep23.csv',
                'oct': 'flow_15k_oct23.csv', 'nov': 'flow_15k_nov23.csv', 'dec': 'flow_15k_dec23.csv'
            },
            "display_name": "Battery (15kWh)"
        }
    }
    
    flows_to_plot = {
        "Grid_Import": ["NoPV", "12kWh", "15kWh"],
        "PV_Direct_Consumption": ["12kWh", "15kWh"],
        "PV_to_Grid_Feedin": ["12kWh", "15kWh"]
    }

    for flow, scenarios_to_include in flows_to_plot.items():
        annual_data = {}
        for scenario in scenarios_to_include:
            config = scenarios_config[scenario]
            print(f"Processing scenario: {scenario} for flow: {flow}")
            df = create_annual_dataframe(config, flow)
            
            if not df.empty and isinstance(df.index, pd.DatetimeIndex):
                if flow == "Grid_Import":
                    resampled_data = df.sort_index().resample('D').sum() / 60000.0
                else:
                    resampled_data = df.sort_index().resample('W').sum() / 60000.0
                
                annual_data[scenario] = resampled_data
                print(f"Data for {scenario} aggregated.")
            else:
                print(f"Skipping plot for {scenario} - no valid data found.")
                continue

        if annual_data:
            plt.figure(figsize=(12, 8))
            for scenario, data in annual_data.items():
                plt.plot(data.index, data.values, label=f'{scenarios_config[scenario]["display_name"]}', linewidth=2)
            
            plt.title(f'{flow.replace("_", " ")} Comparison (kWh)')
            plt.xlabel('Date')
            plt.ylabel(f'Energy (kWh)')
            plt.legend(title='Scenario')
            plt.grid(True, linestyle='--', alpha=0.6)
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, f'time_series_{flow.lower()}_comparison.png'))
            print(f"\nSuccessfully created time series plot for {flow} at: {os.path.join(output_dir, f'time_series_{flow.lower()}_comparison.png')}")

            plt.figure(figsize=(12, 8))
            for scenario, data in annual_data.items():
                sorted_data = data.sort_values(ascending=False).values
                x_axis = range(1, len(sorted_data) + 1)
                plt.plot(x_axis, sorted_data, label=f'{scenarios_config[scenario]["display_name"]}', linewidth=2)
            
            plt.title(f'{flow.replace("_", " ")} Duration Curve')
            plt.xlabel('Sorted Duration')
            plt.ylabel(f'Energy (kWh)')
            plt.legend(title='Scenario')
            plt.grid(True, linestyle='--', alpha=0.6)
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, f'{flow.lower()}_duration_curve.png'))
            print(f"\nSuccessfully created duration curve for {flow} at: {os.path.join(output_dir, f'{flow.lower()}_duration_curve.png')}")
        else:
            print(f"\nNo data was processed for flow: {flow}. No plots were generated.")