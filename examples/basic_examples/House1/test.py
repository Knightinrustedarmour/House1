
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
output.to_csv("test_results.csv", index=True)

results = pd.read_csv("test_results.csv", header=[0, 1], index_col=0)

df = pd.DataFrame()

df["Battery_charge"] = results[ [
        ("SolphLabel(location='house_1', mtress_component='ElectricityCarrier', solph_node='distribution')", 
         "SolphLabel(location='house_1', mtress_component='storage1', solph_node='Battery_Storage')")
    ]]

df["Battery_discharge"] = results[[
        ("SolphLabel(location='house_1', mtress_component='storage1', solph_node='Battery_Storage')", 
         "SolphLabel(location='house_1', mtress_component='ElectricityCarrier', solph_node='distribution')")
    ]]

df["PV_production"] =results[[("SolphLabel(location='house_1', mtress_component='pv', solph_node='source')",
                           "SolphLabel(location='house_1', mtress_component='pv', solph_node='connection')")]]

df["PV_distribution"] = results[[("SolphLabel(location='house_1', mtress_component='pv', solph_node='connection')",
                              "SolphLabel(location='house_1', mtress_component='ElectricityCarrier', solph_node='distribution')")]]

df["Demand2"] = results[[("SolphLabel(location='house_1', mtress_component='ElectricityCarrier', solph_node='distribution')",
                      "SolphLabel(location='house_1', mtress_component='electricity demand', solph_node='input')")]]

df["Grid_import"] = results[[("SolphLabel(location='house_1', mtress_component='ElectricityGridConnection', solph_node='grid_import')",
                          "SolphLabel(location='house_1', mtress_component='ElectricityCarrier', solph_node='distribution')")]]

df["Grid_export"] = results[[("SolphLabel(location='house_1', mtress_component='ElectricityCarrier', solph_node='feed_in')",
                          "SolphLabel(location='house_1', mtress_component='ElectricityGridConnection', solph_node='grid_export')")]]

start_time = '2023-07-10 08:00:00'
end_time = '2023-07-10 18:00:00'

df = df[(df.index >= start_time) & (df.index <= end_time)]

fig, axes = plt.subplots(nrows=7, ncols=1, figsize=(12, 18), sharex=True)
plt.subplots_adjust(hspace=0.5) # Adjust vertical spacing between subplots
# Plot each energy flow in a separate subplot
df["PV_production"].plot(ax=axes[0], label="PV Production (W)", color="green")
axes[0].set_ylabel("Power (W)")
axes[0].legend(bbox_to_anchor=(1, 1), loc='upper right')
axes[0].grid(True)

df["PV_distribution"].plot(ax=axes[1], label="PV Distribution (Wh)", color="lightgreen")
axes[1].set_ylabel("Energy (Wh)")
axes[1].legend(bbox_to_anchor=(1, 1), loc='upper right')
axes[1].grid(True)

df["Demand2"].plot(ax=axes[2], label="Demand (Wh)", color="red")
axes[2].set_ylabel("Energy (Wh)")
axes[2].legend(bbox_to_anchor=(1, 1), loc='upper right')
axes[2].grid(True)

df["Grid_import"].plot(ax=axes[3], label="Grid Import (W)", color="blue")
axes[3].set_ylabel("Energy (Wh)")
axes[3].legend(bbox_to_anchor=(1, 1), loc='upper right')
axes[3].grid(True)

df["Grid_export"].plot(ax=axes[4], label="Grid Export (Wh)", color="yellow")
axes[4].set_ylabel("Energy (Wh)")
axes[4].legend(bbox_to_anchor=(1, 1), loc='upper right')
axes[4].grid(True)

df["Battery_charge"].plot(ax=axes[5], label="Battery Charge (Wh)", color="orange")
axes[5].set_ylabel("Energy (Wh)")
axes[5].legend(bbox_to_anchor=(1, 1), loc='upper right')
axes[5].grid(True)

df["Battery_discharge"].plot(ax=axes[6], label="Battery Discharge (Wh)", color="purple")
axes[6].set_xlabel("Time") # Only label the x-axis of the bottom subplot
axes[6].set_ylabel("Energy (Wh)")
axes[6].legend(bbox_to_anchor=(1,1), loc='upper right')
axes[6].grid(True)

fig.suptitle(f"Energy Flows ({start_time} to {end_time})", fontsize=16)
plt.tight_layout(rect=[0, 0.03, 1, 0.95])
plt.show()