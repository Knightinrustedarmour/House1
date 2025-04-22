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

house_1 = Location(name="house_1")
meta_model.add_location(house_1)

house_1.add(carriers.ElectricityCarrier())
house_1.add(technologies.ElectricityGridConnection(working_rate=0.1, revenue=0.35))
op_data = pd.read_csv("C:/Users/eshwa/mt/mtress/examples/op_data2.csv")
op_data = op_data.iloc[:1440]
print(op_data["Load_Watts"].sum())
print(op_data["Modelled_Energy"].sum())
house_1.add(demands.Electricity(name="demand0", time_series=op_data["Load_Watts"]))
house_1.add(technologies.RenewableElectricitySource
            (name= "source2",
             nominal_power= 1,
             specific_generation=op_data["Modelled_Energy"], fixed=True))


solph_representation = SolphModel(
    meta_model,
    timeindex={
        "start": "2022-08-08 00:00:00",
        "end":   "2022-08-09 00:00:00",
        "freq": "1T",
        "tz": "Europe/Berlin",
    },
)

solph_representation.build_solph_model()

plot = solph_representation.graph(detail=True)
plot.render(outfile="Alh2_detail.png")

plot = solph_representation.graph(detail=False)
plot.render(outfile="Alh2_only_simple.png")

solved_model = solph_representation.solve(solve_kwargs={"tee": True})

solved_model.write(
    "Alh2_only.lp", io_options={"symbolic_solver_labels": True}
)

myresults = solph.processing.results(solved_model)
flows = get_flows(myresults)

plot = solph_representation.graph(
    detail=True, flow_results=flows, flow_color=None
)
plot.render(outfile="electricity_only_results.png")
solph_representation.build_solph_model()

pv_generation_series = flows[
    ("house_1", "source2", "source"), ("house_1", "source2", "connection")
].fillna(0)
total_pv_generation = sum(pv_generation_series) / 1000  # Convert to kW
#print("PV Generation Series:", pv_generation_series)
print("Total PV Generation in kW:", total_pv_generation)

grid_import = flows[
    ("house_1", "ElectricityGridConnection", "source_import"), ("house_1", "ElectricityGridConnection", "grid_import")
].fillna(0)
total_grid_import = sum(grid_import) /  1000
print("Total Import from grid in Kw:",total_grid_import)
