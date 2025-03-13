"""
Basic working 'electricity only' example.

Basic working 'electricity only' example which includes a location (house),
an electricity carrier which acts as a electricity source/supply from the 
official grid (working price of 35 ct/kWh) as well as a demand (consumer)
with a demand time series.

At first an energy system (here meta_model) is defined with a time series 
(index). Afterwards a location is defined and added to the energysystem. 
Then the electricity carrier and demand (time series) are added to the 
energysystem. Finally, the energy system is optimised/solved via 
meta_model.solve and the solver output is written to an .lp file.   
"""

import os
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

house_1 = Location(name="house_1")
meta_model.add_location(house_1)

house_1.add(carriers.ElectricityCarrier())
house_1.add(technologies.ElectricityGridConnection(working_rate=35))

house_1.add(
    demands.Electricity(
        name="electricity demand",
        time_series=[0, 0.5],
    )
)

solph_representation = SolphModel(
    meta_model,
    timeindex={
        "start": "2021-07-10 00:00:00",
        "end": "2021-07-10 02:00:00",
        "freq": "60T",
    },
)

solph_representation.build_solph_model()

plot = solph_representation.graph(detail=True)
plot.render(outfile="electricity_only_detail.png")

plot = solph_representation.graph(detail=False)
plot.render(outfile="electricity_only_simple.png")

solved_model = solph_representation.solve(solve_kwargs={"tee": True})

solved_model.write(
    "electricity_only.lp", io_options={"symbolic_solver_labels": True}
)

myresults = solph.processing.results(solved_model)
flows = get_flows(myresults)

print(
    flows[
        ("house_1", "electricity demand", "input"),
        ("house_1", "electricity demand", "sink"),
    ]
)

plot = solph_representation.graph(
    detail=True, flow_results=flows, flow_color=None
)
plot.render(outfile="electricity_only_results.png")
solph_representation.build_solph_model()

Carr_demand = flows[("house_1", "ElectricityCarrier", "distribution"), ("house_1", "electricity demand", "input")]
Time= Carr_demand.index
# T_35_to_b_35 = flows[("house_1", "HeatCarrier", "T_35"), ("house_1", "Hot Storage", "b_35")]
# T_40_to_b_40 = flows[("house_1", "HeatCarrier", "T_40"), ("house_1", "Hot Storage", "b_40")]
# T_45_to_b_45 = flows[("house_1", "HeatCarrier", "T_45"), ("house_1", "Hot Storage", "b_45")]
# #T_50_to_b_50 = flows[("house_1", "HeatCarrier", "T_50"), ("house_1", "Hot Storage", "b_50")]
# Total_storage_inflow =  T_30_to_b_30 + T_35_to_b_35 + T_40_to_b_40 + T_45_to_b_45 #+ T_50_to_b_50 T_25_to_b_25 +

# #b_25_to_T_25 = flows[("house_1", "Hot Storage", "b_25"), ("house_1", "HeatCarrier", "T_25")]
# b_30_to_T_30 = flows[("house_1", "Hot Storage", "b_30"), ("house_1", "HeatCarrier", "T_30")]
# b_35_to_T_35 = flows[("house_1", "Hot Storage", "b_35"), ("house_1", "HeatCarrier", "T_35")]
# b_40_to_T_40 = flows[("house_1", "Hot Storage", "b_40"), ("house_1", "HeatCarrier", "T_40")]
# b_45_to_T_45 = flows[("house_1", "Hot Storage", "b_45"), ("house_1", "HeatCarrier", "T_45")]
# #b_50_to_T_50 = flows[("house_1", "Hot Storage", "b_50"), ("house_1", "HeatCarrier", "T_50")]
# Total_storage_outflow =  b_30_to_T_30 + b_35_to_T_35 + b_40_to_T_40 + b_45_to_T_45 #+ b_50_to_T_50 b_25_to_T_25 +

# Total_storage_Usage = Total_storage_inflow - Total_storage_outflow

plt.figure(figsize=(7, 4))
#plt.plot(air_temp_ahe.index, air_temp_ahe, label="T_ambient")
plt.plot(Carr_demand.index, Carr_demand, label="Carr_demand", color="purple")


plt.legend()
plt.title("Hot Storage supplying temperature Base case")
plt.xlabel("Time (HH:MM)")
plt.ylabel("Watts")
plt.gca().xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%H:%M"))
#plt.savefig("HP_performance.png")
plt.show()


data = [Time,Carr_demand]
headers= ["Time","Carr_demand"]
with open("Scenario_1.csv", "w", newline="") as f:
     writer = csv.writer(f)
     writer.writerow(headers)  # Write headers
     for row in zip(*data):  # Combine rows from different data sources
         writer.writerow(row)