import pandas as pd
import os

# Base directory where your 'examples' folder is located
# IMPORTANT: Double-check this path is correct for your setup.
base_dir = r"c:\Users\eshwa\House1\examples\House1"

# Define the paths for the columns we are looking for,
# based on your last provided snippets.
EXPECTED_FLOW_COLUMNS = {
    "PV_production": (
        "SolphLabel(location='House1', mtress_component='PV', solph_node='connection')",
        "SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='distribution')"
    ),
    "Battery_discharge": (
        "SolphLabel(location='House1', mtress_component='storage1', solph_node='Battery_Storage')",
        "SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='distribution')"
    ),
    "Grid_import": (
        "SolphLabel(location='House1', mtress_component='ElectricityGridConnection', solph_node='grid_import')",
        "SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='distribution')"
    ),
}

# List of files to check from different scenarios
files_to_check = {
    "NoPV_January": os.path.join(base_dir, "flows_nopv", "flow_nopv_jan23.csv"),
    "PV_NoBattery_January": os.path.join(base_dir, "flows_nobattery", "flow_NB_jan23.csv"),
    "50kWh_January": os.path.join(base_dir, "flows_50k", "flow_50k_jan23.csv"),
    # Add more files if you suspect specific months or scenarios have different headers
    # e.g., "NoPV_March": os.path.join(base_dir, "flows_nopv", "flow_nopv_mar23.csv"),
}

print("--- Column Debugging Report ---")

for scenario_name, file_path in files_to_check.items():
    print(f"\n--- Checking file: {scenario_name} ({file_path}) ---")
    if not os.path.exists(file_path):
        print(f"ERROR: File not found at '{file_path}'. Please verify the path and file existence.")
        continue

    try:
        results = pd.read_csv(file_path, header=[0, 1], index_col=0)
        # Apply the utc=True fix for consistency here as well
        results.index = pd.to_datetime(results.index, utc=True)

        df_cols_list = results.columns.tolist()
        print("\nAll columns found in DataFrame (full MultiIndex tuples):")
        if not df_cols_list:
            print("  No columns found. Check CSV structure or header parameters.")
        else:
            for col_tuple in df_cols_list:
                print(f"  {col_tuple}")

        print("\nChecking for specific flow columns:")
        for flow_name, expected_col_path in EXPECTED_FLOW_COLUMNS.items():
            if expected_col_path in results.columns:
                print(f"  ✅ '{flow_name}' column FOUND: {expected_col_path}")
                # Print a small sample of the data if found, to confirm it's not all zeros
                print(f"    Sample data (first 5 rows) for '{flow_name}':")
                print(results[expected_col_path].head().to_string()) # .to_string() for better formatting
            else:
                print(f"  ❌ '{flow_name}' column NOT FOUND: {expected_col_path}")
                # Suggest potential alternative names if something similar is found (manual check for now)

    except pd.errors.EmptyDataError:
        print(f"ERROR: {file_path} is empty or contains no data.")
    except Exception as e:
        print(f"An error occurred while processing {file_path}: {e}")

print("\n--- Debugging Report Complete ---")
print("Please copy the ENTIRE output above and paste it back.")