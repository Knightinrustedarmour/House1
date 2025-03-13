import os
import pandas as pd
import matplotlib.pyplot as plt
#from oemof.solph import results
from oemof.solph.processing import results
from mtress import (
    Location,
    MetaModel,
    SolphModel,
    carriers,
    demands,
    technologies,
)
from mtress._helpers import get_flows
from mtress._helpers._visualization import render_series

os.chdir(os.path.dirname(__file__))
energy_system = MetaModel()
house_1 = Location(name="Alhambra")
energy_system.add_location(house_1)

house_1.add(carriers.ElectricityCarrier())
house_1.add(technologies.ElectricityGridConnection(working_rate=35))
op_data = pd.read_csv("C:/Users/eshwa/mt/mtress/examples/op_data2.csv")
op_data["time"] = pd.date_range(start="2022-08-08 00:00:00", periods=len(op_data), freq="1T")
op_data = op_data.iloc[:10080]
#op_data = op_data.set_index("time")
#op_data = op_data.loc["2022-08-08 00:00:00":"2022-08-15 00:00:00"]



house_1.add(demands.Electricity(name="demand0",
                                 time_series=op_data["Load_Watts"]))
house_1.add(technologies.RenewableElectricitySource
            (name= "source2",
             nominal_power=1,
             specific_generation=op_data["Modelled_Energy"], fixed=True))


house_1.add(technologies.BatteryStorage(name="storage1",
                                        nominal_capacity=1,
                                        charging_C_Rate=1,
                                        discharging_C_Rate=1,
                                        charging_efficiency=0.98,
                                        discharging_efficiency=0.95,
                                        loss_rate=0.0,
                                        initial_soc=0.5,
                                        min_soc=0.1))   

solph_representation = SolphModel(
    energy_system,
    timeindex={
        "start": "2022-08-08 00:00:00+01:00",
        "freq": "1T",
        #"end": "2022-08-15 00:00:00",
        "periods": len(op_data) + 1,
        #"periods": 993601, 
        "tz": "Europe/Berlin",
    }
)

solph_representation.build_solph_model()

plot = solph_representation.graph(detail=True)
plot.render(outfile="alhambra_detail.png")

plot = solph_representation.graph(detail=False)
plot.render(outfile="alhambra_simple.png")

#run.solph.model()

solved_model = solph_representation.solve(solve_kwargs={"tee": True})
myresults = results(solved_model)
flows = get_flows(myresults)

plot.render(outfile="alhambra_results.png")
solved_model.write(
    "alhambra.lp", io_options={"symbolic_solver_labels": True}
)
pv = flows[("Alhambra","source2","source"),("Alhambra","source2","connection")]
load = flows[("Alhambra","ElecticityGridConnection","source_import"),("Alhambra","ElecticityGridConnection","grid_import")]
time =pv.index
plt.figure(figsize=(7, 4))
plt.plot(time, pv, label="PV")
plt.legend()
plt.title("PV production")
plt.xlabel("Time (HH:MM)")
plt.ylabel("Watts")
plt.show()
