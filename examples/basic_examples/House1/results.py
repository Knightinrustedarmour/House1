import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_pdf import PdfPages

os.chdir(os.path.dirname(__file__))

results = pd.read_csv(os.path.join("flows", "flow_W_dec23.csv"), header=[0, 1], index_col=0)

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

df.index = pd.to_datetime(df.index, utc=True)

start_date = pd.to_datetime('2023-06-01', utc=True).date()
end_date = pd.to_datetime('2023-06-30', utc=True).date()
delta = pd.Timedelta(days=5)
pdf_path = os.path.join("pdf", "jun23.pdf")

with PdfPages(pdf_path) as pdf:
    current_date = start_date
    while current_date <= end_date:
        end_interval = current_date + pd.Timedelta(days=4)
        if end_interval > end_date:
            end_interval = end_date

        start_time_interval = pd.to_datetime(current_date.strftime('%Y-%m-%d'), utc=True)
        end_time_interval = pd.to_datetime(end_interval.strftime('%Y-%m-%d') + ' 23:59:59', utc=True)
        df_filtered = df[(df.index >= start_time_interval) & (df.index <= end_time_interval)].copy()

        if not df_filtered.empty:
            fig, axes = plt.subplots(nrows=3, ncols=1, figsize=(14, 20), sharex=True)
            plt.subplots_adjust(hspace=0.5)

            # Plot 1: PV Production and Distribution
            df_filtered["PV_production"].plot(ax=axes[0], label="PV Production (W)", color="green")
            df_filtered["PV_distribution"].plot(ax=axes[0], label="PV Distribution (W)", color="lightgreen")
            axes[0].set_ylabel("Power (W)")
            axes[0].legend(bbox_to_anchor=(1, 1), loc='upper right')
            axes[0].grid(True)

            # Plot 2: Demand and Grid Import
            df_filtered["Demand2"].plot(ax=axes[1], label="Demand (W)", color="red")
            df_filtered["Grid_import"].plot(ax=axes[1], label="Grid Import (W)", color="blue")
            df_filtered["Grid_export"].plot(ax=axes[1], label="Grid Export (W)", color="yellow")
            axes[1].set_ylabel("Power (W)")
            axes[1].legend(bbox_to_anchor=(1, 1), loc='upper right')
            axes[1].grid(True)


            # Plot 4: Battery Charge and Negative Battery Discharge
            df_filtered["Battery_charge"].plot(ax=axes[2], label="Battery Charge (Wh)", color="orange")
            (df_filtered["Battery_discharge"]).plot(ax=axes[2], label=" Battery Discharge (Wh)", color="purple", linestyle='--')
            axes[2].set_xlabel("Time")
            axes[2].set_ylabel("Energy (Wh)")
            axes[2].legend(bbox_to_anchor=(1, 1), loc='upper right')
            axes[2].grid(True)

            start_date_str = current_date.strftime('%Y-%m-%d')
            end_date_str = end_interval.strftime('%Y-%m-%d')
            fig.suptitle(f"Energy Flows ({start_date_str} to {end_date_str})", fontsize=16)
            plt.tight_layout(rect=[0, 0.03, 1, 0.95])
            pdf.savefig(fig)
            plt.close(fig)

        current_date += delta

print(f"PDF saved successfully at: {pdf_path}")