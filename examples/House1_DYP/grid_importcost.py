import os
import pandas as pd

# Define base directory (assuming the script is run from the directory containing 'flows' and 'op_dyprice.csv')
script_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else os.getcwd()
FLOWS_DIR = os.path.join(script_dir, "flows")
PRICE_FILE = os.path.join(script_dir, "op_dyprice.csv")
TIMEZONE = "Europe/Berlin"

# --- 1. Scenarios Configuration ---
# All file names use 'k' for kWh, e.g., 'flow_5k_jan23.csv'
scenarios_config = {
    "PV_NoBattery": {
        "files": {
            'jan': 'flow_NB_jan23.csv', 'feb': 'flow_NB_feb23.csv',
            'mar': 'flow_NB_mar23.csv', 'apr': 'flow_NB_apr23.csv', 'may': 'flow_NB_may23.csv',
            'jun': 'flow_NB_jun23.csv', 'jul': 'flow_NB_jul23.csv', 'aug': 'flow_NB_aug23.csv',
            'sep': 'flow_NB_sep23.csv', 'oct': 'flow_NB_oct23.csv', 'nov': 'flow_NB_nov23.csv',
            'dec': 'flow_NB_dec23.csv'
        }
    },
    "5kWh": {
        "files": {
            'jan': 'flow_5k_jan23.csv', 'feb': 'flow_5k_feb23.csv',
            'mar': 'flow_5k_mar23.csv', 'apr': 'flow_5k_apr23.csv', 'may': 'flow_5k_may23.csv',
            'jun': 'flow_5k_jun23.csv', 'jul': 'flow_5k_jul23.csv', 'aug': 'flow_5k_aug23.csv',
            'sep': 'flow_5k_sep23.csv', 'oct': 'flow_5k_oct23.csv', 'nov': 'flow_5k_nov23.csv',
            'dec': 'flow_5k_dec23.csv'
        }
    },
    "8kWh": {
        "files": {
            'jan': 'flow_8k_jan23.csv', 'feb': 'flow_8k_feb23.csv',
            'mar': 'flow_8k_mar23.csv', 'apr': 'flow_8k_apr23.csv', 'may': 'flow_8k_may23.csv',
            'jun': 'flow_8k_jun23.csv', 'jul': 'flow_8k_jul23.csv', 'aug': 'flow_8k_aug23.csv',
            'sep': 'flow_8k_sep23.csv', 'oct': 'flow_8k_oct23.csv', 'nov': 'flow_8k_nov23.csv',
            'dec': 'flow_8k_dec23.csv'
        }
    },
    "12kWh": {
        "files": {
            'jan': 'flow_12k_jan23.csv', 'feb': 'flow_12k_feb23.csv',
            'mar': 'flow_12k_mar23.csv', 'apr': 'flow_12k_apr23.csv', 'may': 'flow_12k_may23.csv',
            'jun': 'flow_12k_jun23.csv', 'jul': 'flow_12k_jul23.csv', 'aug': 'flow_12k_aug23.csv',
            'sep': 'flow_12k_sep23.csv', 'oct': 'flow_12k_oct23.csv', 'nov': 'flow_12k_nov23.csv',
            'dec': 'flow_12k_dec23.csv'
        }
    },
    "15kWh": {
        "files": {
            'jan': 'flow_15k_jan23.csv', 'feb': 'flow_15k_feb23.csv',
            'mar': 'flow_15k_mar23.csv', 'apr': 'flow_15k_apr23.csv', 'may': 'flow_15k_may23.csv',
            'jun': 'flow_15k_jun23.csv', 'jul': 'flow_15k_jul23.csv', 'aug': 'flow_15k_aug23.csv',
            'sep': 'flow_15k_sep23.csv', 'oct': 'flow_15k_oct23.csv', 'nov': 'flow_15k_nov23.csv',
            'dec': 'flow_15k_dec23.csv'
        }
    },
    "20kWh": {
        "files": {
            'jan': 'flow_20k_jan23.csv', 'feb': 'flow_20k_feb23.csv',
            'mar': 'flow_20k_mar23.csv', 'apr': 'flow_20k_apr23.csv', 'may': 'flow_20k_may23.csv',
            'jun': 'flow_20k_jun23.csv', 'jul': 'flow_20k_jul23.csv', 'aug': 'flow_20k_aug23.csv',
            'sep': 'flow_20k_sep23.csv', 'oct': 'flow_20k_oct23.csv', 'nov': 'flow_20k_nov23.csv',
            'dec': 'flow_20k_dec23.csv'
        }
    },
    "26kWh": {
        "files": {
            'jan': 'flow_26k_jan23.csv', 'feb': 'flow_26k_feb23.csv',
            'mar': 'flow_26k_mar23.csv', 'apr': 'flow_26k_apr23.csv', 'may': 'flow_26k_may23.csv',
            'jun': 'flow_26k_jun23.csv', 'jul': 'flow_26k_jul23.csv', 'aug': 'flow_26k_aug23.csv',
            'sep': 'flow_26k_sep23.csv', 'oct': 'flow_26k_oct23.csv', 'nov': 'flow_26k_nov23.csv',
            'dec': 'flow_26k_dec23.csv'
        }
    },
    "50kWh": {
        "files": {
            'jan': 'flow_50k_jan23.csv', 'feb': 'flow_50k_feb23.csv',
            'mar': 'flow_50k_mar23.csv', 'apr': 'flow_50k_apr23.csv', 'may': 'flow_50k_may23.csv',
            'jun': 'flow_50k_jun23.csv', 'jul': 'flow_50k_jul23.csv', 'aug': 'flow_50k_aug23.csv',
            'sep': 'flow_50k_sep23.csv', 'oct': 'flow_50k_oct23.csv', 'nov': 'flow_50k_nov23.csv',
            'dec': 'flow_50k_dec23.csv'
        }
    }
}

# --- 2. Load and Prepare Price Data ---

try:
    op_data_full = pd.read_csv(PRICE_FILE)
    
    # Recreate the index logic from the simulation code for alignment
    FULL_START_DATE = "2022-08-08 00:00:00"
    full_date_range = pd.date_range(
        start=FULL_START_DATE,
        periods=len(op_data_full),
        freq="min",
        tz=TIMEZONE # Should be Europe/Berlin, as used in your simulation
    )

    price_data_annual = op_data_full[["Price"]].copy()
    price_data_annual.index = full_date_range
    price_data_annual.rename(columns={'Price': 'price_eur_per_kwh'}, inplace=True)
    
except FileNotFoundError:
    print(f"Error: Price file not found at '{PRICE_FILE}'. Please ensure 'op_dyprice.csv' is in the working directory.")
    exit()

# --- 3. Infer Grid Import Column Name ---
# This is the most likely column name based on oemof.solph's naming conventions for flows.
# The flow is from the 'grid_import' bus of 'ElectricityGridConnection' to the 'distribution' bus of 'ElectricityCarrier'
GRID_IMPORT_COL =   ("('House1', 'ElectricityGridConnection', 'grid_import')",
             "('House1', 'ElectricityCarrier', 'distribution')")

output_filename = "grid_import_cost.csv"
summary_filename = "grid_import_cost_summary.csv"
annual_results = {}

# ✅ Add this block here
OUTPUT_DIR = os.path.join(script_dir, "output","import_cost")
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("Starting annual grid import cost analysis...")
print(f"Time-series results will be saved to '{OUTPUT_DIR}'.")
print(f"Summary results will be saved to '{summary_filename}'.\n")

# Use ExcelWriter for creating multiple sheets in a single file
for scenario_name, config in scenarios_config.items():
    print(f"Processing scenario: {scenario_name}")
    all_months_df = []

    for file_name in config["files"].values():
        file_path = os.path.join(FLOWS_DIR, file_name)
        try:
            monthly_df = pd.read_csv(file_path, header=[0, 1], index_col=0, parse_dates=True)
            monthly_df.index = pd.to_datetime(monthly_df.index, utc=True).tz_convert(TIMEZONE)
            grid_import_wmin = monthly_df[GRID_IMPORT_COL]
            all_months_df.append(grid_import_wmin)
        except FileNotFoundError:
            print(f"  Warning: File not found: {file_path}. Skipping.")
        except KeyError:
            print(f"  Warning: Column '{GRID_IMPORT_COL}' not found in {file_name}. Skipping.")

    if not all_months_df:
        print(f"  No valid data for scenario {scenario_name}. Skipping.")
        continue

    annual_flows_wmin = pd.concat(all_months_df).rename('grid_import_wmin')
    grid_import_kwh = annual_flows_wmin / 60000.0
    grid_import_kwh.name = 'grid_import_kwh'

    df_scenario = pd.DataFrame(grid_import_kwh)
    df_scenario = df_scenario.join(price_data_annual, how='inner')
    df_scenario['grid_import_cost_eur'] = df_scenario['grid_import_kwh'] * df_scenario['price_eur_per_kwh']

    total_annual_cost = df_scenario['grid_import_cost_eur'].sum()
    annual_results[scenario_name] = total_annual_cost

    output_df = df_scenario[['grid_import_kwh', 'price_eur_per_kwh', 'grid_import_cost_eur']].rename_axis('time').reset_index()

    csv_filename = os.path.join(OUTPUT_DIR, f"grid_import_cost_{scenario_name}.csv")
    output_df.to_csv(csv_filename, index=False)

    print(f"  Annual Cost: {total_annual_cost:,.2f} € (Saved to '{csv_filename}')")

    # --- Write Summary File ---
summary_df = pd.DataFrame.from_dict(
    annual_results, orient='index', columns=['total_annual_cost_eur']
).sort_index()

summary_path = os.path.join(OUTPUT_DIR, summary_filename)
summary_df.to_csv(summary_path)

print(f"\nSummary of all scenarios saved to '{summary_path}'.")

