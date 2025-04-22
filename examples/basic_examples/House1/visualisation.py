import pandas as pd
import matplotlib.pyplot as plt

# Load the energy flows CSV file, specifying the index column and parsing dates
energy_flows_df = pd.read_csv("C:/Users/eshwa/mt/mtress/examples/basic_examples/alhambra/energy_flows.csv", index_col=0, parse_dates=True)

#plt.figure(figsize=(12, 6))
#plt.plot(energy_flows_df.index,energy_flows_df['PV_Input_Watts'], label='PV Input (W)', color='green')
#plt.plot(energy_flows_df.index,energy_flows_df['Battery_In_Watts'], label='Battery Charge (W)', color='cyan')
#plt.plot(energy_flows_df.index,energy_flows_df['Self_consumption'], label='PV Self Consumption (W)', color='blue')
#plt.plot(energy_flows_df.index, energy_flows_df['Battery_Out_Watts'], label='Battery Discharge (W)', color='purple')
#plt.plot(energy_flows_df.index, energy_flows_df['Grid_Import_Watts'], label='Grid Import (W)', color='blue')
#plt.plot(energy_flows_df.index,energy_flows_df['Demand'],label ='Demand',color = 'red')
#plt.plot(energy_flows_df.index, energy_flows_df['Demand2'], label='Demand2', color='orange')
#plt.plot(energy_flows_df.index, energy_flows_df['Distrubution'], label='Distribution (W)', color='red')
#plt.plot(energy_flows_df.index, energy_flows_df['Grid_export_watts'], label='Exported to grid (W)', color='yellow')
# plt.xlabel('Time')
# plt.ylabel('Power (W)')
# plt.title('Energy Flows Throughout the Week')
# plt.legend()
# plt.grid(True)
# plt.tight_layout()
# plt.show()




demand2 = energy_flows_df['Demand2'].sum()
demand1 =  energy_flows_df['Demand'].sum()
diff = demand2 - demand1 
print("Difference between demand2 and demand:", diff)
