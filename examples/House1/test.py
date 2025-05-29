import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import csv
from oemof import solph

from mtress import (
    Location,
    MetaModel,
    SolphModel,
    carriers,
    demands,
    technologies,
)
from mtress._helpers import get_flows

os.chdir(os.path.dirname(__file__))

# Load full data once outside the loop for efficiency
op_data_full = pd.read_csv(os.path.join("..", "op_data_power.csv"))

# Define the full date range for op_data_full (based on the original CSV's start)
full_date_range = pd.date_range(start="2022-08-08 00:00:00", periods=len(op_data_full), freq="min", tz="Europe/Berlin")

# Define all months for the year 2023
months_to_simulate = [
    {"year": 2023, "month": 1},  # January
    {"year": 2023, "month": 2},  # February
    {"year": 2023, "month": 3},  # March
    {"year": 2023, "month": 4},  # April
    {"year": 2023, "month": 5},  # May
    {"year": 2023, "month": 6},  # June
    {"year": 2023, "month": 7},  # July
    {"year": 2023, "month": 8},  # August
    {"year": 2023, "month": 9},  # September
    {"year": 2023, "month": 10}, # October
     {"year": 2023, "month": 11}, # November
    {"year": 2023, "month": 12}, # December
]

# Create a directory to save the monthly flow data if it doesn't exist
output_dir = "flows_26k"
os.makedirs(output_dir, exist_ok=True)

for month_info in months_to_simulate:
    year = month_info["year"]
    month = month_info["month"]

    # Construct the start and end dates for the current month
    start_date = pd.Timestamp(year=year, month=month, day=1, hour=0, minute=0, tz="Europe/Berlin")
    # Using pd.offsets.MonthEnd(0) ensures we get the last day of the current month
    end_date = start_date + pd.offsets.MonthEnd(0) + pd.Timedelta(hours=23, minutes=59)

    time_index = {
        "start": start_date.strftime("%Y-%m-%d %H:%M:%S"),
        "end": end_date.strftime("%Y-%m-%d %H:%M:%S"),
        "freq": "min",
        "tz": "Europe/Berlin",
    }

    print(f"Simulating for {start_date.strftime('%B %Y')}...")

    # Determine the rows for the current month from the full dataset
    # Using get_indexer with 'nearest' method to find the closest index
    start_row = full_date_range.get_indexer([start_date], method='nearest')[0]
    end_row = full_date_range.get_indexer([end_date], method='nearest')[0] + 1
    
    op_data = op_data_full.iloc[start_row:end_row].copy()
    op_data.index = pd.date_range(start=full_date_range[start_row], end=full_date_range[end_row-1], freq=time_index["freq"], tz=time_index["tz"])

    # Re-instantiate MetaModel and Location for each monthly simulation
    # This is crucial to ensure that each simulation run is independent
    # and uses the correct time series data for the current month.
    monthly_meta_model = MetaModel()
    monthly_House1 = Location(name="House1")
    monthly_meta_model.add_location(monthly_House1)

    monthly_House1.add(carriers.ElectricityCarrier())
    monthly_House1.add(technologies.ElectricityGridConnection(working_rate=35e-6, revenue=8e-6))
    monthly_House1.add(demands.Electricity(name="demand", time_series=op_data["Load_W"]))
    monthly_House1.add(technologies.RenewableElectricitySource(
        name="PV",
        nominal_power=1,
        specific_generation=op_data["Modelled_Energy"],
        fixed=True
    ))
    monthly_House1.add(technologies.BatteryStorage(
        name="storage1",
        nominal_capacity=26000,
        charging_C_Rate=0.77,
        discharging_C_Rate=0.77,
        charging_efficiency=0.96,
        discharging_efficiency=0.96,
        loss_rate=0.0005,
        initial_soc=0.5,
        min_soc=0.1
    ))

    solph_representation = SolphModel(
        monthly_meta_model,
        timeindex=time_index,
    )

    solph_representation.build_solph_model()
    # Set tee to False to suppress detailed solver output for each month
    solved_model = solph_representation.solve(solve_kwargs={"tee": False}) 

    myresults = solph.processing.results(solved_model)
    flows = get_flows(myresults)

    output = pd.DataFrame(flows)
    
    # Save flows to a unique CSV file for each month
    file_name = f"flow_26K_{start_date.strftime('%b%y').lower()}.csv"
    output.to_csv(os.path.join(output_dir, file_name), index=True)
    print(f"Saved {file_name}")

print("All 2023 monthly simulations complete!")