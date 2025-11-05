# import os
# import pandas as pd
# import matplotlib.pyplot as plt
# import matplotlib
# import csv
# from oemof import solph

# from mtress import (
#     Location,
#     MetaModel,
#     SolphModel,
#     carriers,
#     demands,
#     technologies,
# )
# from mtress._helpers import get_flows

# os.chdir(os.path.dirname(__file__))

# # Load full data once outside the loop for efficiency
# op_data_full = pd.read_csv(os.path.join("op_dyprice.csv"))

# # Define the full date range for op_data_full (based on the original CSV's start)
# full_date_range = pd.date_range(start="2022-08-08 00:00:00", periods=len(op_data_full), freq="min", tz="Europe/Berlin")

# # Define all months for the year 2023
# months_to_simulate = [
#     {"year": 2023, "month": 1},  # January
#     {"year": 2023, "month": 2},  # February
#     {"year": 2023, "month": 3},  # March
#     {"year": 2023, "month": 4},  # April
#     {"year": 2023, "month": 5},  # May
#     {"year": 2023, "month": 6},  # June
#     {"year": 2023, "month": 7},  # July
#     {"year": 2023, "month": 8},  # August
#     {"year": 2023, "month": 9},  # September
#     {"year": 2023, "month": 10}, # October
#      {"year": 2023, "month": 11}, # November
#     {"year": 2023, "month": 12}, # December
# ]


# output_dir = "flows"
# os.makedirs(output_dir, exist_ok=True)

# for month_info in months_to_simulate:
#     year = month_info["year"]
#     month = month_info["month"]

  
#     start_date = pd.Timestamp(year=year, month=month, day=1, hour=0, minute=0, tz="Europe/Berlin")

#     end_date = start_date + pd.offsets.MonthEnd(0) + pd.Timedelta(hours=23, minutes=59)

#     time_index = {
#         "start": start_date.strftime("%Y-%m-%d %H:%M:%S"),
#         "end": end_date.strftime("%Y-%m-%d %H:%M:%S"),
#         "freq": "min",
#         "tz": "Europe/Berlin",
#      }
#     # "start": "2023-11-01 00:00:00",
#     # "end": "2023-11-30 23:59:00",
#     # "freq": "min",


#     print(f"Simulating for {start_date.strftime('%B %Y')}...")

  
#     start_row = full_date_range.get_indexer([start_date], method='nearest')[0]
#     end_row = full_date_range.get_indexer([end_date], method='nearest')[0] + 1
    
#     op_data = op_data_full.iloc[start_row:end_row].copy()
#     op_data.index = pd.date_range(start=full_date_range[start_row], end=full_date_range[end_row-1], freq=time_index["freq"], tz=time_index["tz"])

    
#     monthly_meta_model = MetaModel()
#     monthly_House1 = Location(name="House1")
#     monthly_meta_model.add_location(monthly_House1)

#     monthly_House1.add(carriers.ElectricityCarrier())
#     monthly_House1.add(technologies.ElectricityGridConnection(working_rate=op_data["Price"], revenue=0.08))
#     monthly_House1.add(demands.Electricity(name="demand", time_series=op_data["Load_W"]))
#     monthly_House1.add(technologies.RenewableElectricitySource(
#         name="PV",
#         nominal_power=1,
#         specific_generation=op_data["Modelled_Energy"],
#         fixed=True 
#     ))
   

#     monthly_House1.add(technologies.BatteryStorage(
#         name="storage1",
#         nominal_capacity=50000, 
#         charging_C_Rate=0.77,
#         discharging_C_Rate=0.77,
#         charging_efficiency=0.96,
#         discharging_efficiency=0.96,
#         loss_rate=0.0005,
#         initial_soc=0.5,
#         min_soc=0.1
#     ))

#     solph_representation = SolphModel(
#         monthly_meta_model,
#         timeindex=time_index,
#     )

#     solph_representation.build_solph_model()
#     # Set tee to False to suppress detailed solver output for each month
#     solved_model = solph_representation.solve(solve_kwargs={"tee": False})
#     myresults = solph.processing.results(solved_model)
#     flows = get_flows(myresults) 
#     plot = solph_representation.graph(
#     detail=True, flow_results=flows, flow_color=None
# )
#     plot.render(outfile="House1_dy.png")

#     output = pd.DataFrame(flows)
    
#     # Save flows to a unique CSV file for each month
#     file_name = f"flow_50k_{start_date.strftime('%b%y').lower()}.csv"
#     output.to_csv(os.path.join(output_dir, file_name), index=True)
#     print(f"Saved {file_name}")

# print("All 2023 monthly simulations complete!") 




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

# Set the working directory to the script's directory
# This ensures op_dyprice.csv is loaded correctly.
os.chdir(os.path.dirname(__file__))

# Load full data once
try:
    op_data_full = pd.read_csv(os.path.join("op_dyprice.csv"))
except FileNotFoundError:
    print("Error: op_dyprice.csv not found. Please ensure the file is in the same directory.")
    exit()

# Define the full date range for op_data_full (based on the original CSV's start)
# Assuming the full data starts on 2022-08-08 00:00:00 and has a 1-minute frequency
full_date_range = pd.date_range(
    start="2022-08-08 00:00:00", 
    periods=len(op_data_full), 
    freq="min", 
    tz="Europe/Berlin"
)

# --- Annual Simulation Configuration (Full Year 2023) ---
print("Configuring simulation for the entire year 2023...")

# Define the start and end dates for the full 2023 year
start_date = pd.Timestamp(year=2023, month=1, day=1, hour=0, minute=0, tz="Europe/Berlin")
end_date = pd.Timestamp(year=2023, month=12, day=31, hour=23, minute=59, tz="Europe/Berlin")

time_index = {
    "start": start_date.strftime("%Y-%m-%d %H:%M:%S"),
    "end": end_date.strftime("%Y-%m-%d %H:%M:%S"),
    "freq": "min",
    "tz": "Europe/Berlin",
}

# Slice op_data for the entire 2023 simulation period
start_row = full_date_range.get_indexer([start_date], method='nearest')[0]
end_row = full_date_range.get_indexer([end_date], method='nearest')[0] + 1
op_data = op_data_full.iloc[start_row:end_row].copy()
op_data.index = pd.date_range(
    start=full_date_range[start_row], 
    end=full_date_range[end_row-1], 
    freq=time_index["freq"], 
    tz=time_index["tz"]
)

# --- Model Setup ---
meta_model = MetaModel()
House1 = Location(name="House1")
meta_model.add_location(House1)

# Add Energy Carriers and Components
House1.add(carriers.ElectricityCarrier())
House1.add(technologies.ElectricityGridConnection(
    working_rate=op_data["Price"], 
    revenue=0.08
))
House1.add(demands.Electricity(
    name="demand", 
    time_series=op_data["Load_W"]
))
House1.add(technologies.RenewableElectricitySource(
    name="PV",
    nominal_power=1,
    specific_generation=op_data["Modelled_Energy"],
    fixed=True 
))

House1.add(technologies.BatteryStorage(
    name="storage1",
    nominal_capacity=50000, # Wh
    charging_C_Rate=0.77,
    discharging_C_Rate=0.77,
    charging_efficiency=0.96,
    discharging_efficiency=0.96,
    loss_rate=0.0005,
    initial_soc=0.5,
    min_soc=0.1
))

# --- Solph Model and Optimization ---
solph_representation = SolphModel(
    meta_model,
    timeindex=time_index,
)

solph_representation.build_solph_model()

# Set tee to False to suppress detailed solver output
print("Starting annual optimization...")
solved_model = solph_representation.solve(solve_kwargs={"tee": False})

# --- Results Processing and Saving ---
myresults = solph.processing.results(solved_model)
flows = get_flows(myresults) 

# Save graph (will overwrite the previous one)
plot = solph_representation.graph(
    detail=True, 
    flow_results=flows, 
    flow_color=None
)
plot.render(outfile="House1_dy_annual.png")

output_dir = "flows"
os.makedirs(output_dir, exist_ok=True)
output = pd.DataFrame(flows)

# Save flows to a single CSV file for the full year
file_name = f"flow_50k_2023.csv"
output.to_csv(os.path.join(output_dir, file_name), index=True)
print(f"Saved annual flows to {os.path.join(output_dir, file_name)}")

print("Annual simulation for 2023 complete!")
