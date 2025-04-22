import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

#results = pd.read_csv("C:/Users/eshwa/mt/mtress/examples/basic_examples/alhambra/flows2.csv", header=[0, 1], index_col=0)
results = pd.read_csv("C:/Users/eshwa/mt/mtress/examples/basic_examples/alhambra/flows/flow_dec23.csv", header=[0, 1], index_col=0)

df = pd.DataFrame()

df["Battery_charge"] = results[ [
        ("SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='distribution')", 
         "SolphLabel(location='House1', mtress_component='storage1', solph_node='Battery_Storage')")
    ]]

df["Battery_discharge"] = results[[
        ("SolphLabel(location='House1', mtress_component='storage1', solph_node='Battery_Storage')", 
         "SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='distribution')")
    ]]

df["PV_production"] =results[[("SolphLabel(location='House1', mtress_component='PV', solph_node='source')",
                           "SolphLabel(location='House1', mtress_component='PV', solph_node='connection')")]]

df["PV_distribution"] = results[[("SolphLabel(location='House1', mtress_component='PV', solph_node='connection')",
                              "SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='distribution')")]]

df["Demand2"] = results[[("SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='distribution')",
                      "SolphLabel(location='House1', mtress_component='demand', solph_node='input')")]]

df["Grid_import"] = results[[("SolphLabel(location='House1', mtress_component='ElectricityGridConnection', solph_node='grid_import')",
                          "SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='distribution')")]]

df["Grid_export"] = results[[("SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='feed_in')",
                          "SolphLabel(location='House1', mtress_component='ElectricityGridConnection', solph_node='grid_export')")]]

start_time = '2023-12-01 00:00:00'
end_time = '2023-12-05 23:59:00'

df = df[(df.index >= start_time) & (df.index <= end_time)]

nominal_capacity = 5000  # in Wh
charge_eff = 0.77
discharge_eff = 0.77
soc = [0.5 * nominal_capacity]  # initial SOC in Wh

for ch, dis in zip(df["Battery_charge"].fillna(0), df["Battery_discharge"].fillna(0)):
    prev = soc[-1]
    new = prev + ch * charge_eff - dis / discharge_eff
    new = max(0, min(nominal_capacity, new))
    soc.append(new)

df["SOC (%)"] = [s / nominal_capacity * 100 for s in soc[1:]]

# Plot
fig_soc, ax_soc = plt.subplots(figsize=(12, 3))
df["SOC (%)"].plot(ax=ax_soc, color="black", label="State of Charge (%)")
ax_soc.set_ylabel("SOC (%)")
ax_soc.set_xlabel("Time")
ax_soc.set_title("Battery State of Charge")
ax_soc.grid(True)
ax_soc.legend(loc="upper right")
plt.tight_layout()
plt.show()

# total_pv_production = df["PV_production"].sum() / 1000
# total_pv_use = df["PV_distribution"].sum() / 1000
# total_demand2 = df["Demand2"].sum()/ 1000
# total_gridimport = df["Grid_import"].sum()/ 1000
# total_gridexport = df["Grid_export"].sum()/ 1000
# total_battery_discharge = df["Battery_discharge"].sum()/ 1000
# total_battery_charge = df["Battery_charge"].sum()/ 1000

# print("Total PV Production (Sum of 'PV_production' column): {:.2f} kW".format(total_pv_production))
# print("Total PV Used (Sum of 'PV_distribution' column): {:.2f} kW".format(total_pv_use))
# print("Total Demand (Sum of 'Demand2' column): {:.2f} kW".format(total_demand2))
# print("Total Grid Import (Sum of 'Grid_import' column): {:.2f} kW".format(total_gridimport))
# print("Total Grid Export (Sum of 'Grid_export' column): {:.2f} kW".format(total_gridexport))
# print("Total Battery Discharge (Sum of 'Battery_discharge' column): {:.2f} kW".format(total_battery_discharge))
# print("Total Battery Charge (Sum of 'Battery_charge' column): {:.2f} kW".format(total_battery_charge))

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


