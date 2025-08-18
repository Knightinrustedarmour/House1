import os
import pandas as pd

def check_headers_for_5kwh_scenario():
    """Reads a 5kWh file and compares its headers to the hardcoded ones."""
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(script_dir, "flows_5k", "flow_5k_jan23.csv")
    
    # The hardcoded dictionary for comparison
    ALL_FLOWS = {
        "Demand_Consumption": (
            "SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='distribution')",
            "SolphLabel(location='House1', mtress_component='demand', solph_node='input')"
        ),
        "Battery_Charge": (
            "SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='distribution')",
            "SolphLabel(location='House1', mtress_component='storage1', solph_node='Battery_Storage')"
        ),
        "Grid_Export_to_Grid": (
            "SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='feed_in')",
            "SolphLabel(location='House1', mtress_component='ElectricityGridConnection', solph_node='grid_export')"
        ),
        "Grid_Export_Sink": (
            "SolphLabel(location='House1', mtress_component='ElectricityGridConnection', solph_node='grid_export')",
            "SolphLabel(location='House1', mtress_component='ElectricityGridConnection', solph_node='sink_export')"
        ),
        "Grid_Import": (
            "SolphLabel(location='House1', mtress_component='ElectricityGridConnection', solph_node='grid_import')",
            "SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='distribution')"
        ),
        "Grid_Import_Source": (
            "SolphLabel(location='House1', mtress_component='ElectricityGridConnection', solph_node='source_import')",
            "SolphLabel(location='House1', mtress_component='ElectricityGridConnection', solph_node='grid_import')"
        ),
        "PV_Direct_Consumption": (
            "SolphLabel(location='House1', mtress_component='PV', solph_node='connection')",
            "SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='distribution')"
        ),
        "PV_to_Grid_Feedin": (
            "SolphLabel(location='House1', mtress_component='PV', solph_node='connection')",
            "SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='feed_in')"
        ),
        "Total_PV_Production": (
            "SolphLabel(location='House1', mtress_component='PV', solph_node='source')",
            "SolphLabel(location='House1', mtress_component='PV', solph_node='connection')"
        ),
        "Demand_Sink": (
            "SolphLabel(location='House1', mtress_component='demand', solph_node='input')",
            "SolphLabel(location='House1', mtress_component='demand', solph_node='sink')"
        ),
        "Battery_Discharge": (
            "SolphLabel(location='House1', mtress_component='storage1', solph_node='Battery_Storage')",
            "SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='distribution')"
        )
    }

    if not os.path.exists(filepath):
        print(f"Error: File not found at {filepath}")
        return

    try:
        results = pd.read_csv(filepath, header=[0, 1], index_col=0)
        print("--- Headers found in your 'flow_5k_jan23.csv' file: ---")
        for col in results.columns:
            print(f"File Header: {col}")

        print("\n--- Headers currently hardcoded in the script: ---")
        for name, header_tuple in ALL_FLOWS.items():
            print(f"Script Header: {header_tuple} for '{name}'")
            
    except Exception as e:
        print(f"An error occurred while reading the file: {e}")

if __name__ == "__main__":
    check_headers_for_5kwh_scenario()