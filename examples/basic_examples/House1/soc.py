# plot_battery_soc.py

import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

os.chdir(os.path.dirname(__file__))
results = pd.read_csv(os.path.join("flows", "flow_W_aug23.csv"), header=[0, 1], index_col=0)

nominal_capacity_wh = 5000  #  Wh
charge_eff = 0.96
discharge_eff = 0.96
initial_soc_wh = 0.5 * nominal_capacity_wh
discharge_c_rate = 0.77
nominal_voltage_dc = 76.8  
nominal_capacity_ah = nominal_capacity_wh / nominal_voltage_dc
max_discharge_current = discharge_c_rate * nominal_capacity_ah
max_discharge_power = max_discharge_current * nominal_voltage_dc

df = pd.DataFrame()
df["Battery_charge"] = results[ [
        ("SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='distribution')",
         "SolphLabel(location='House1', mtress_component='storage1', solph_node='Battery_Storage')")
    ]]

df["Battery_discharge"] = results[[
        ("SolphLabel(location='House1', mtress_component='storage1', solph_node='Battery_Storage')",
         "SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='distribution')")
    ]]

df["PV_distribution"] = results[[("SolphLabel(location='House1', mtress_component='PV', solph_node='connection')",
                                  "SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='distribution')")]]

df["Demand2"] = results[[("SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='distribution')",
                          "SolphLabel(location='House1', mtress_component='demand', solph_node='input')")]]


df.index = pd.to_datetime(df.index, utc=True)

start_date = pd.to_datetime('2023-08-05', utc=True).date()
end_date = pd.to_datetime('2023-08-10', utc=True).date()
delta = pd.Timedelta(days=5)

current_date = start_date
while current_date <= end_date:
    end_interval = current_date + pd.Timedelta(days=4)
    if end_interval > end_date:
        end_interval = end_date

    start_time_interval = pd.to_datetime(current_date.strftime('%Y-%m-%d'), utc=True)
    end_time_interval = pd.to_datetime(end_interval.strftime('%Y-%m-%d') + ' 23:59:59', utc=True)
    df_filtered = df[(df.index >= start_time_interval) & (df.index <= end_time_interval)].copy()

    if not df_filtered.empty:
        time_delta_seconds = (df_filtered.index[1] - df_filtered.index[0]).total_seconds() if len(df_filtered) > 1 else 60
        soc_wh = [initial_soc_wh]

        for charge_power, discharge_power in zip(df_filtered["Battery_charge"].fillna(0), df_filtered["Battery_discharge"].fillna(0)):
            prev_soc_wh = soc_wh[-1]
            net_change_wh = 0

            # Charging
            if charge_power > 0:
                net_change_wh += charge_power * (charge_eff * time_delta_seconds / 3600)

            # Discharging with rate limit
            if discharge_power > 0:
                limited_discharge_power = min(discharge_power, max_discharge_power)
                net_change_wh -= limited_discharge_power * (time_delta_seconds / 3600) / discharge_eff

            new_soc_wh = prev_soc_wh + net_change_wh
            new_soc_wh = max(0, min(nominal_capacity_wh, new_soc_wh))
            soc_wh.append(new_soc_wh)

        df_filtered["SOC (Wh)"] = soc_wh[1:]
        df_filtered["SOC (%)"] = [s / nominal_capacity_wh * 100 for s in df_filtered["SOC (Wh)"]]

        fig, axes = plt.subplots(nrows=3, ncols=1, figsize=(12, 10), sharex=True) 
        plt.subplots_adjust(hspace=0.5)

        axes[0].plot(df_filtered.index, df_filtered["Demand2"].fillna(0), label="Demand (W)", color="red")
        axes[0].plot(df_filtered.index, df_filtered["PV_distribution"].fillna(0), label="PV Distribution (W)", color="green")
        axes[0].set_ylabel("Power (W)")
        axes[0].legend(loc="upper right")
        axes[0].grid(True)

        # Battery Charge and Negative Battery Discharge
        axes[1].plot(df_filtered.index, df_filtered["Battery_charge"].fillna(0), label="Battery Charge (W)", color="orange")
        axes[1].plot(df_filtered.index, -df_filtered["Battery_discharge"].fillna(0), label=" Battery Discharge (W)", color="purple", linestyle='--')
        axes[1].set_ylabel("Power (W)")
        axes[1].legend(loc="upper right")
        axes[1].grid(True)

        # State of Charge
        axes[2].plot(df_filtered.index, df_filtered["SOC (%)"], color="black", label="State of Charge (%)")
        axes[2].set_ylabel("SOC (%)")
        axes[2].set_xlabel("Time")
        axes[2].set_title("Battery State of Charge")
        axes[2].grid(True)
        axes[2].legend(loc="upper right")

        start_date_str = current_date.strftime('%Y-%m-%d')
        end_date_str = end_interval.strftime('%Y-%m-%d')
        fig.suptitle(f"Energy Activity and SOC ({start_date_str} to {end_date_str})", fontsize=16)
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        plt.show()

    current_date += delta