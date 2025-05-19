import os
import pandas as pd

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the path to the 'flows' directory
flows_dir = os.path.join(script_dir, "flows")

# Define the target CSV files
target_files = {
    'mar': 'flow_W_mar23.csv',
    'apr': 'flow_W_apr23.csv',
    'may': 'flow_W_may23.csv',
    'jun': 'flow_W_jun23.csv',
    'jul': 'flow_W_jul23.csv',
    'aug': 'flow_W_aug23.csv',
}

# Create empty DataFrames for each month
mar = pd.DataFrame()
apr = pd.DataFrame()
may = pd.DataFrame()
jun = pd.DataFrame()
jul = pd.DataFrame()
aug = pd.DataFrame()

# Load data into individual DataFrames
for month, filename in target_files.items():
    filepath = os.path.join(flows_dir, filename)
    try:
        results = pd.read_csv(filepath, header=[0, 1], index_col=0)

        # Populate the DataFrame based on the month
        if month == 'mar':
            df = mar
        elif month == 'apr':
            df = apr
        elif month == 'may':
            df = may
        elif month == 'jun':
            df = jun
        elif month == 'jul':
            df = jul
        elif month == 'aug':
            df = aug

        df["Battery_charge"] = results[[
            ("SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='distribution')",
             "SolphLabel(location='House1', mtress_component='storage1', solph_node='Battery_Storage')")
        ]]

        df["Battery_discharge"] = results[[
            ("SolphLabel(location='House1', mtress_component='storage1', solph_node='Battery_Storage')",
             "SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='distribution')")
        ]]

        df["PV_production"] = results[[
            ("SolphLabel(location='House1', mtress_component='PV', solph_node='source')",
             "SolphLabel(location='House1', mtress_component='PV', solph_node='connection')")
        ]]
        pv_dist_col = ("SolphLabel(location='House1', mtress_component='PV', solph_node='connection')",
                       "SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='distribution')")
        if pv_dist_col in results.columns:
            df["PV_distribution"] = results[[pv_dist_col]]
        else:
            print(f"Warning: 'PV_distribution' column not found in {filename}")
            df["PV_distribution"] = pd.Series(index=results.index)

        df["Demand2"] = results[[
            ("SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='distribution')",
             "SolphLabel(location='House1', mtress_component='demand', solph_node='input')")
        ]]

        df["Grid_import"] = results[[
            ("SolphLabel(location='House1', mtress_component='ElectricityGridConnection', solph_node='grid_import')",
             "SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='distribution')")
        ]]

        df["Grid_export"] = results[[
            ("SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='feed_in')",
             "SolphLabel(location='House1', mtress_component='ElectricityGridConnection', solph_node='grid_export')")
        ]]
        df.index = pd.to_datetime(df.index, utc=True)


    except FileNotFoundError:
        print(f"Warning: File not found: {filename}")

print("\n--- March DataFrame ---")
print(mar.head())
print("\n--- April DataFrame ---")
print(apr.head())

print("\nSum of PV Distribution for each month:")
print(f"March: {mar['PV_distribution'].sum() /1000 :.2f} Kwh")
print(f"April: {apr['PV_distribution'].sum()/1000:.2f} Kwh")
print(f"May: {may['PV_distribution'].sum()/1000:.2f} Kwh")
print(f"June: {jun['PV_distribution'].sum()/1000:.2f} Kwh")
print(f"July: {jul['PV_distribution'].sum()/1000:.2f} Kwh")
print(f"August: {aug['PV_distribution'].sum()/1000:.2f} Kwh")

total_pv_distribution = mar['PV_distribution'].sum() + apr['PV_distribution'].sum() + may['PV_distribution'].sum() + jun['PV_distribution'].sum() + jul['PV_distribution'].sum() + aug['PV_distribution'].sum()
total_grid_export = mar['Grid_export'].sum() + apr['Grid_export'].sum() + may['Grid_export'].sum() + jun['Grid_export'].sum() + jul['Grid_export'].sum() + aug['Grid_export'].sum()
total_grid_import = mar['Grid_import'].sum() + apr['Grid_import'].sum() + may['Grid_import'].sum() + jun['Grid_import'].sum() + jul['Grid_import'].sum() + aug['Grid_import'].sum()
total_demand = mar['Demand2'].sum() + apr['Demand2'].sum() + may['Demand2'].sum() + jun['Demand2'].sum() + jul['Demand2'].sum() + aug['Demand2'].sum()
print(f"\nTotal Demand (Mar-Aug): {total_demand / 1000 :.2f} Kw")
print(f"\nTotal PV Distribution (Mar-Aug): {total_pv_distribution / 1000 :.2f} Kw")
print(f"Total Grid Export (Mar-Aug): {total_grid_export / 1000 :.2f} Kw")
print(f"Total Grid Import (Mar-Aug): {total_grid_import / 1000 :.2f} Kw")

