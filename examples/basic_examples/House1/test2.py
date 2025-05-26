import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_pdf import PdfPages

def calculate_soc_from_flows(charge_series, discharge_series, index,
                              nominal_capacity_wh=5000, initial_soc_percent=50):
    """
    Calculates the State of Charge (SOC) of a battery based on charge and discharge power flows.

    Assumes that the charge and discharge values in the input series already account for
    efficiency and internal losses. The SOC is tracked based on the net energy change
    from the initial SOC.

    Args:
        charge_series (pd.Series): A pandas Series of charge power (in Watts) over time.
        discharge_series (pd.Series): A pandas Series of discharge power (in Watts) over time.
        index (pd.Index): The pandas Index representing the timestamps of the data.
        nominal_capacity_wh (float): The nominal energy capacity of the battery in Watt-hours.
        initial_soc_percent (float): The initial State of Charge as a percentage (0-100).

    Returns:
        list: A list of SOC values (in percentage) at each time point.
    """
    soc_values_percent = [initial_soc_percent]
    current_soc_wh = (initial_soc_percent / 100) * nominal_capacity_wh

    for i in range(1, len(index)):
        dt_seconds = (index[i] - index[i - 1]).total_seconds()
        dt_hours = dt_seconds / 3600

        charge_energy_wh = charge_series.iloc[i] * dt_hours
        discharge_energy_wh = discharge_series.iloc[i] * dt_hours

        net_energy_change_wh = charge_energy_wh - discharge_energy_wh
        current_soc_wh += net_energy_change_wh

        soc_percentage = (current_soc_wh / nominal_capacity_wh) * 100
        soc_values_percent.append(soc_percentage)

    return soc_values_percent


os.chdir(os.path.dirname(__file__))

results = pd.read_csv(os.path.join("flows", "flow_W_dec23.csv"), header=[0, 1], index_col=0)

df = pd.DataFrame()
df["Battery_charge"] = results[[
    ("SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='distribution')",
     "SolphLabel(location='House1', mtress_component='storage1', solph_node='Battery_Storage')")
]]

df["Battery_discharge"] = results[[
    ("SolphLabel(location='House1', mtress_component='storage1', solph_node='Battery_Storage')",
     "SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='distribution')")
]]

df["PV_distribution"] = results[[
    ("SolphLabel(location='House1', mtress_component='PV', solph_node='connection')",
     "SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='distribution')")
]]

df["Demand2"] = results[[
    ("SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='distribution')",
     "SolphLabel(location='House1', mtress_component='demand', solph_node='input')")
]]

df.index = pd.to_datetime(df.index, utc=True)

# ---- Calculate SOC ----
df["SOC_%"] = calculate_soc_from_flows(df["Battery_charge"].squeeze(), df["Battery_discharge"].squeeze(), df.index)

# ---- Plotting ----
start_date = pd.to_datetime('2023-12-01', utc=True).date()
end_date = pd.to_datetime('2023-12-31', utc=True).date()
delta = pd.Timedelta(days=5)
pdf_path = os.path.join("pdf", "soc_dec323.pdf")

with PdfPages(pdf_path) as pdf:
    current_date = start_date
    while current_date <= end_date:
        end_interval = current_date + pd.Timedelta(days=4)
        if end_interval > end_date:
            end_interval = end_date

        start_time_interval = pd.to_datetime(str(current_date), utc=True)
        end_time_interval = pd.to_datetime(str(end_interval) + ' 23:59:59', utc=True)

        df_filtered = df[(df.index >= start_time_interval) & (df.index <= end_time_interval)].copy()

        if not df_filtered.empty:
            fig, axes = plt.subplots(nrows=3, ncols=1, figsize=(14, 18), sharex=True)
            plt.subplots_adjust(hspace=0.4)

            # Plot 1: PV vs Demand
            df_filtered["PV_distribution"].plot(ax=axes[0], label="PV Distribution (W)", color="green")
            df_filtered["Demand2"].plot(ax=axes[0], label="Demand (W)", color="red")
            axes[0].set_ylabel("Power (W)")
            axes[0].legend()
            axes[0].grid(True)

            # Plot 2: Battery flows
            df_filtered["Battery_charge"].plot(ax=axes[1], label="Battery Charge (W)", color="orange")
            df_filtered["Battery_discharge"].plot(ax=axes[1], label="Battery Discharge (W)", color="purple", linestyle='--')
            axes[1].set_ylabel("Power (W)")
            axes[1].legend()
            axes[1].grid(True)

            # Plot 3: SOC %
            df_filtered["SOC_%"].plot(ax=axes[2], label="State of Charge (%)", color="blue")
            axes[2].set_ylabel("SOC (%)")
            axes[2].set_xlabel("Time")
            axes[2].legend()
            axes[2].grid(True)

            start_str = current_date.strftime('%Y-%m-%d')
            end_str = end_interval.strftime('%Y-%m-%d')
            fig.suptitle(f"Battery and PV Analysis ({start_str} to {end_str})", fontsize=16)
            plt.tight_layout(rect=[0, 0.03, 1, 0.95])
            pdf.savefig(fig)
            plt.close(fig)

        current_date += delta

print(f"PDF saved at: {pdf_path}")