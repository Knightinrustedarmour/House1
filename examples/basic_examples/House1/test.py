
import os
import matplotlib.pyplot as plt
import matplotlib
import csv
import pandas as pd
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
house_1.add(technologies.ElectricityGridConnection(working_rate=35e-6, revenue=8e-6))

house_1.add(
    demands.Electricity(
        name="electricity demand",
        time_series=[0, 0.5,15,3,0.2,7,3,6,0.8,10],
    )
)
house_1.add(
    technologies.RenewableElectricitySource(
        name="pv",
        nominal_power=1,
        specific_generation=[0, 0,25,30,41,0.1,0,0,0,0],
    )
)
house_1.add(technologies.BatteryStorage(name="storage1",
                                         nominal_capacity=5000, 
                                         charging_C_Rate=0.77, 
                                         discharging_C_Rate=0.77, 
                                         charging_efficiency=0.96,
                                         discharging_efficiency=0.96,
                                         loss_rate=0.0005,  
                                         initial_soc=0.5,
                                         min_soc=0.1))


solph_representation = SolphModel(
    meta_model,
    timeindex={
        "start": "2023-07-10 08:00:00",
        "end": "2023-07-10 18:00:00",
        "freq": "60T",
    },
)

solph_representation.build_solph_model()

plot = solph_representation.graph(detail=True)
plot.render(outfile="test.png")

solved_model = solph_representation.solve(solve_kwargs={"tee": True})


myresults = solph.processing.results(solved_model)
flows = get_flows(myresults)

output = pd.DataFrame(flows)
#saving flows in csv file

output.to_csv(os.path.join("flows", "test_results.csv"), index=True)

