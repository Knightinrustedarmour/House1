

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

Alhambra = Location(name="Alhambra")
meta_model.add_location(Alhambra)

Alhambra.add(carriers.ElectricityCarrier())
Alhambra.add(technologies.ElectricityGridConnection(working_rate=0.1, revenue=0.35))
op_data = pd.read_csv("C:/Users/eshwa/mt/mtress/examples/op_data2.csv")
time_index = {
    "start": "2023-08-10 00:00:00",
    "end": "2023-08-17 23:59:00",
    "freq": "1T",
    "tz": "Europe/Berlin",
}

start_date_str = time_index["start"][:10]  # Extract date from timestamp
end_date_str = time_index["end"][:10]


full_date_range = pd.date_range(start="2022-08-08 00:00:00", periods=len(op_data), freq="min", tz=time_index["tz"])

# Find matching rows
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


Alhambra.add(demands.Electricity(name="demand", time_series=op_data["Load_Watts"]))

#Alhambra.add(carriers.AbstractCarrier(AbstractComponent))
Alhambra.add(technologies.RenewableElectricitySource
            (name= "PV",
             nominal_power= 1,
             specific_generation=op_data["Modelled_Energy"], fixed=True))

Alhambra.add(technologies.BatteryStorage(name="storage1",
                                        nominal_capacity=1,
                                        charging_C_Rate=1,
                                        discharging_C_Rate=1,
                                        charging_efficiency=0.98,
                                        discharging_efficiency=0.95,
                                        loss_rate=0.0,
                                        initial_soc=0.5,
                                        min_soc=0.1))


solph_representation = SolphModel(
    meta_model,
    timeindex= time_index,
    #     "start": "2022-08-10 00:00:00",
    #     "end":   "2022-08-11 00:00:00",
    #     "freq": "1T",
    #     "tz": "Europe/Berlin",
    )

solph_representation.build_solph_model()

plot = solph_representation.graph(detail=True)
plot.render(outfile="test.png")
solved_model = solph_representation.solve(solve_kwargs={"tee": True})
myresults = solph.processing.results(solved_model)
flows = get_flows(myresults)

pv_generation_series = flows[
    ("Alhambra", "PV", "source"), ("Alhambra", "PV", "connection")
].fillna(0)
total_pv_generation = sum(pv_generation_series) / 1000  # Convert to kW
#print("PV Generation Series:", pv_generation_series)


grid_import = flows[
    ("Alhambra", "ElectricityGridConnection", "source_import"), ("Alhambra", "ElectricityGridConnection", "grid_import")
].fillna(0)
total_grid_import = sum(grid_import) /  1000
battery =flows[("Alhambra","storage1","Battery_Storage"),("Alhambra","ElectricityCarrier","distribution")].fillna(0)
total_battery = sum(battery) / 1000

print("Total PV Generation in kW:", total_pv_generation)
print("Total Import from grid in Kw:",total_grid_import)
print("Total Battery Storage in Kw:",total_battery)

print("Import from CSV",op_data["Load_Watts"].sum() /1000)
print("PV from CSV",op_data["Modelled_Energy"].sum()/1000)
plt.plot(battery.index, battery, label="Battery Storage",color="red")
plt.legend()
plt.xlabel("Time")
plt.ylabel("Power (kW)")
plt.show()