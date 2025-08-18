import os
import pandas as pd

def calculate_annual_flows(scenario_identifier, scenario_config):
    """Calculates annual energy flows for a given scenario by checking for multiple header formats."""
    
    # Dictionary with both possible header formats for each flow
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
        ]
    }

    annual_flows_total = {name: 0.0 for name in ALL_FLOWS.keys()}
    
    # Loop through each monthly file for the scenario
    for filename in scenario_config["files"].values():
        filepath = os.path.join(scenario_config["flow_dir"], filename)
        if not os.path.exists(filepath):
            print(f"File not found: {filepath}. Skipping.")
            continue
        
        try:
            results = pd.read_csv(filepath, header=[0, 1], index_col=0)
            
            # Loop through all the specified flows and sum them up
            for flow_name, solph_label_tuples in ALL_FLOWS.items():
                for solph_label_tuple in solph_label_tuples:
                    try:
                        data_series = results[solph_label_tuple]
                        monthly_total_wh = data_series.sum()
                        annual_flows_total[flow_name] += monthly_total_wh
                        # Once a header is found, break to avoid summing multiple times
                        break 
                    except KeyError:
                        # Continue to the next possible header format if the current one is not found
                        continue
        except Exception as e:
            print(f"Error reading {filepath}: {e}. Skipping file.")
            continue
            
    # Convert total Wh to kWh
    annual_flows_kwh = {
        name: total_wh / 60000 for name, total_wh in annual_flows_total.items()
    }
    
    annual_flows_kwh["Scenario"] = scenario_identifier
    return annual_flows_kwh

# --- Core Script Execution ---
if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "output", "energy_flow_master_table")
    os.makedirs(output_dir, exist_ok=True)

    scenarios_config = {
        "NoPV": {
            "flow_dir": os.path.join(script_dir, "flows_nopv"),
            "files": {
                'jan': 'flow_nopv_jan23.csv', 'feb': 'flow_nopv_feb23.csv',
                'mar': 'flow_nopv_mar23.csv', 'apr': 'flow_nopv_apr23.csv', 'may': 'flow_nopv_may23.csv',
                'jun': 'flow_nopv_jun23.csv', 'jul': 'flow_nopv_jul23.csv', 'aug': 'flow_nopv_aug23.csv',
                'sep': 'flow_nopv_sep23.csv', 'oct': 'flow_nopv_oct23.csv', 'nov': 'flow_nopv_nov23.csv',
                'dec': 'flow_nopv_dec23.csv'
            }
        },
        "PV_NoBattery": {
            "flow_dir": os.path.join(script_dir, "flows_nobattery"),
            "files": {
                'jan': 'flow_NB_jan23.csv', 'feb': 'flow_NB_feb23.csv',
                'mar': 'flow_NB_mar23.csv', 'apr': 'flow_NB_apr23.csv', 'may': 'flow_NB_may23.csv',
                'jun': 'flow_NB_jun23.csv', 'jul': 'flow_NB_jul23.csv', 'aug': 'flow_NB_aug23.csv',
                'sep': 'flow_NB_sep23.csv', 'oct': 'flow_NB_oct23.csv', 'nov': 'flow_NB_nov23.csv',
                'dec': 'flow_NB_dec23.csv'
            }
        },
        "5kWh": {
            "flow_dir": os.path.join(script_dir, "flows_5k"),
            "files": {
                'jan': 'flow_5k_jan23.csv', 'feb': 'flow_5k_feb23.csv',
                'mar': 'flow_5k_mar23.csv', 'apr': 'flow_5k_apr23.csv', 'may': 'flow_5k_may23.csv',
                'jun': 'flow_5k_jun23.csv', 'jul': 'flow_5k_jul23.csv', 'aug': 'flow_5k_aug23.csv',
                'sep': 'flow_5k_sep23.csv', 'oct': 'flow_5k_oct23.csv', 'nov': 'flow_5k_nov23.csv',
                'dec': 'flow_5k_dec23.csv'
            }
        },
        "8kWh": {
            "flow_dir": os.path.join(script_dir, "flows_8k"),
            "files": {
                'jan': 'flow_8k_jan23.csv', 'feb': 'flow_8k_feb23.csv',
                'mar': 'flow_8k_mar23.csv', 'apr': 'flow_8k_apr23.csv', 'may': 'flow_8k_may23.csv',
                'jun': 'flow_8k_jun23.csv', 'jul': 'flow_8k_jul23.csv', 'aug': 'flow_8k_aug23.csv',
                'sep': 'flow_8k_sep23.csv', 'oct': 'flow_8k_oct23.csv', 'nov': 'flow_8k_nov23.csv',
                'dec': 'flow_8k_dec23.csv'
            }
        },
        "12kWh": {
            "flow_dir": os.path.join(script_dir, "flows_12k"),
            "files": {
                'jan': 'flow_12k_jan23.csv', 'feb': 'flow_12k_feb23.csv',
                'mar': 'flow_12k_mar23.csv', 'apr': 'flow_12k_apr23.csv', 'may': 'flow_12k_may23.csv',
                'jun': 'flow_12k_jun23.csv', 'jul': 'flow_12k_jul23.csv', 'aug': 'flow_12k_aug23.csv',
                'sep': 'flow_12k_sep23.csv', 'oct': 'flow_12k_oct23.csv', 'nov': 'flow_12k_nov23.csv',
                'dec': 'flow_12k_dec23.csv'
            }
        },
        "15kWh": {
            "flow_dir": os.path.join(script_dir, "flows_15k"),
            "files": {
                'jan': 'flow_15k_jan23.csv', 'feb': 'flow_15k_feb23.csv',
                'mar': 'flow_15k_mar23.csv', 'apr': 'flow_15k_apr23.csv', 'may': 'flow_15k_may23.csv',
                'jun': 'flow_15k_jun23.csv', 'jul': 'flow_15k_jul23.csv', 'aug': 'flow_15k_aug23.csv',
                'sep': 'flow_15k_sep23.csv', 'oct': 'flow_15k_oct23.csv', 'nov': 'flow_15k_nov23.csv',
                'dec': 'flow_15k_dec23.csv'
            }
        },
        "20kWh": {
            "flow_dir": os.path.join(script_dir, "flows_20k"),
            "files": {
                'jan': 'flow_20k_jan23.csv', 'feb': 'flow_20k_feb23.csv',
                'mar': 'flow_20k_mar23.csv', 'apr': 'flow_20k_apr23.csv', 'may': 'flow_20k_may23.csv',
                'jun': 'flow_20k_jun23.csv', 'jul': 'flow_20k_jul23.csv', 'aug': 'flow_20k_aug23.csv',
                'sep': 'flow_20k_sep23.csv', 'oct': 'flow_20k_oct23.csv', 'nov': 'flow_20k_nov23.csv',
                'dec': 'flow_20k_dec23.csv'
            }
        },
        "26kWh": {
            "flow_dir": os.path.join(script_dir, "flows_26k"),
            "files": {
                'jan': 'flow_26k_jan23.csv', 'feb': 'flow_26k_feb23.csv',
                'mar': 'flow_26k_mar23.csv', 'apr': 'flow_26k_apr23.csv', 'may': 'flow_26k_may23.csv',
                'jun': 'flow_26k_jun23.csv', 'jul': 'flow_26k_jul23.csv', 'aug': 'flow_26k_aug23.csv',
                'sep': 'flow_26k_sep23.csv', 'oct': 'flow_26k_oct23.csv', 'nov': 'flow_26k_nov23.csv',
                'dec': 'flow_26k_dec23.csv'
            }
        },
        "50kWh": {
            "flow_dir": os.path.join(script_dir, "flows_50k"),
            "files": {
                'jan': 'flow_50k_jan23.csv', 'feb': 'flow_50k_feb23.csv',
                'mar': 'flow_50k_mar23.csv', 'apr': 'flow_50k_apr23.csv', 'may': 'flow_50k_may23.csv',
                'jun': 'flow_50k_jun23.csv', 'jul': 'flow_50k_jul23.csv', 'aug': 'flow_50k_aug23.csv',
                'sep': 'flow_50k_sep23.csv', 'oct': 'flow_50k_oct23.csv', 'nov': 'flow_50k_nov23.csv',
                'dec': 'flow_50k_dec23.csv'
            }
        }
    }
    
    all_annual_flows_data = []

    for scenario_identifier, config in scenarios_config.items():
        print(f"\n--- Processing scenario: {scenario_identifier} ---")
        annual_flows_dict = calculate_annual_flows(scenario_identifier, config)
        if annual_flows_dict:
            all_annual_flows_data.append(annual_flows_dict)
    
    if all_annual_flows_data:
        df_annual_flows_master = pd.DataFrame(all_annual_flows_data)
        df_annual_flows_master = df_annual_flows_master.set_index("Scenario")
        
        output_filepath = os.path.join(output_dir, "annual_energy_flows_master_table.csv")
        df_annual_flows_master.to_csv(output_filepath, float_format="%.2f")
        print(f"\nSuccessfully created annual energy flows master table at: {output_filepath}")