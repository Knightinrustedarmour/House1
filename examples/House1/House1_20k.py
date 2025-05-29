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
meta_model = MetaModel()

House1 = Location(name="House1")
meta_model.add_location(House1)

House1.add(carriers.ElectricityCarrier())

House1.add(technologies.ElectricityGridConnection(working_rate=35e-6, revenue=8e-6))
op_data = pd.read_csv(os.path.join("..", "op_data_power.csv"))
time_index = {
    "start": "2023-10-01 00:00:00",
    "end": "2023-10-31 23:59:00",
    "freq": "min",
    "tz": "Europe/Berlin",
}

start_date_str = time_index["start"][:10]  # Extract date from timestamp
end_date_str = time_index["end"][:10]


full_date_range = pd.date_range(start="2022-08-08 00:00:00", periods=len(op_data), freq="min", tz=time_index["tz"])


start_row = None
end_row = None

for i, ts in enumerate(full_date_range):
    if ts.strftime("%Y-%m-%d") == start_date_str and start_row is None: 
        start_row = i
    if ts.strftime("%Y-%m-%d") == end_date_str:
        end_row = i + 1  

op_data = op_data.iloc[start_row:end_row]

date_range = pd.date_range(start=full_date_range[start_row], end=full_date_range[end_row-1], freq=time_index["freq"], tz=time_index["tz"])

op_data.index = date_range

House1.add(demands.Electricity(name="demand", time_series=op_data["Load_W"]))


House1.add(technologies.RenewableElectricitySource
            (name= "PV",
             nominal_power= 1,
             specific_generation=op_data["Modelled_Energy"], fixed=True))

House1.add(technologies.BatteryStorage(name="storage1",
                                         nominal_capacity=15000, 
                                         charging_C_Rate=0.77, 
                                         discharging_C_Rate=0.77, 
                                         charging_efficiency=0.96,
                                         discharging_efficiency=0.96,
                                         loss_rate=0.0005,  
                                         initial_soc=0.5,
                                         min_soc=0.1))

# # Enphase IQ Battery 5P
# # Type: AC-coupled, modular LiFePO₄

solph_representation = SolphModel(
    meta_model,
    timeindex= time_index,
    )

solph_representation.build_solph_model()

# plot = solph_representation.graph(detail=True)
# plot.render(outfile="house_detail.png")

solved_model = solph_representation.solve(solve_kwargs={"tee": True})


myresults = solph.processing.results(solved_model)
flows = get_flows(myresults)

plot = solph_representation.graph(
    detail=True, flow_results=flows, flow_color=None
)
plot.render(outfile="House1_20k_results.png")
solph_representation.build_solph_model()

output = pd.DataFrame(flows)
#saving flows in csv file
output.to_csv(os.path.join("flows_15k", "flow_15K_oct23.csv"), index=True)