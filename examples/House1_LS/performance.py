import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

os.chdir(os.path.dirname(__file__))

months = [
    ('mar', '2023-03-01', '2023-03-31'),
    ('apr', '2023-04-01', '2023-04-30'),
    ('may', '2023-05-01', '2023-05-31'),
    ('jun', '2023-06-01', '2023-06-30'),
    ('jul', '2023-07-01', '2023-07-31'),
    ('aug', '2023-08-01', '2023-08-31'),
    ('sep', '2023-09-01', '2023-09-30'),
]

#scenarios = ['NB']
scenarios = ['NB','5k','8k','12k','15k','20k','26k','50k',]  # NB = no battery

for scenario in scenarios:
    for m, start, end in months:
        csv_path = os.path.join("flows", f"flow_{scenario}_{m}23.csv")
        pdf_path = os.path.join("output", "scenario_pdfs", f"{scenario}_{m}.pdf")
        os.makedirs(os.path.dirname(pdf_path), exist_ok=True)

        results = pd.read_csv(csv_path, header=[0, 1], index_col=0, parse_dates=True)
        df = pd.DataFrame(index=results.index)
        df.index = pd.to_datetime(df.index, utc=True)

        # Only add battery flows if not NB
        if scenario != 'NB':
            df["Battery_charge"] = results[[
                ("('House1', 'ElectricityCarrier', 'distribution')",
                 "('House1', 'storage1', 'Battery_Storage')")
            ]]
            df["Battery_discharge"] = results[[
                ("('House1', 'storage1', 'Battery_Storage')",
                 "('House1', 'ElectricityCarrier', 'distribution')")
            ]]
        else:
            df["Battery_charge"] = 0
            df["Battery_discharge"] = 0

        df["Grid_import"] = results[[
            ("('House1', 'ElectricityGridConnection', 'grid_import')",
             "('House1', 'ElectricityCarrier', 'distribution')")
        ]]
        df["Grid_export"] = results[[
            ("('House1', 'ElectricityCarrier', 'feed_in')",
             "('House1', 'ElectricityGridConnection', 'grid_export')")
        ]]
        df["PV_Distribution"] = results[[
            ("('House1', 'PV', 'connection')",
             "('House1', 'ElectricityCarrier', 'distribution')")
        ]]
        df["Demand"] = results[[
            ("('House1', 'demand', 'input')",
              "('House1', 'demand', 'sink')")]]

        # PV self-use (adjust for NB scenario)
        df["PV_self"] = df["PV_Distribution"] - df["Battery_charge"]
        df["PV_self"] = df["PV_self"].clip(lower=0)

        # Convert W·min → kWh
        df = df / 60000.0

        start_date = pd.Timestamp(start, tz='UTC')
        end_date   = pd.Timestamp(end, tz='UTC')
        step = pd.Timedelta(days=7)

        df = df[(df.index >= start_date) & (df.index <= end_date)]

        with PdfPages(pdf_path) as pdf:
            current_date = start_date

            while current_date <= end_date:
                end_interval = min(current_date + step - pd.Timedelta(days=1), end_date)
                df_filtered = df[(df.index >= current_date) & (df.index <= end_interval)]

                if not df_filtered.empty:
                    fig, axes = plt.subplots(nrows=2, ncols=1, figsize=(21, 9), sharex=True, dpi=150)
                    plt.subplots_adjust(hspace=0.5)

                    # Grid flows
                    df_filtered["Grid_import"].plot(ax=axes[0], label="Grid Import (kWh)", color="blue")
                    df_filtered["Grid_export"].plot(ax=axes[0], label="Grid Export (kWh)", color="yellow")
                    df_filtered["Demand"].plot(ax=axes[0], label="Demand (kWh)", color="red", linestyle="--")
                    axes[0].set_ylabel("Energy (kWh)")
                    axes[0].legend(bbox_to_anchor=(1, 1), loc='upper right')
                    axes[0].grid(True)

                    # Battery + PV
                    if scenario != 'NB':
                        df_filtered["Battery_charge"].plot(ax=axes[1], label="Battery Charge (kWh)", color="orange")
                        df_filtered["Battery_discharge"].plot(ax=axes[1], label="Battery Discharge (kWh)",
                                                              color="purple", linestyle='--')
                    df_filtered["PV_self"].plot(ax=axes[1], label="PV Self-Use (kWh)", color="green", linestyle=':')
                    axes[1].set_xlabel("Time")
                    axes[1].set_ylabel("Energy (kWh)")
                    axes[1].legend(bbox_to_anchor=(1, 1), loc='upper right')
                    axes[1].grid(True)

                    fig.suptitle(f"Energy Flows ({current_date.date()} to {end_interval.date()}) - {scenario}", fontsize=16)
                    plt.tight_layout(rect=[0, 0.03, 1, 0.95])

                    pdf.savefig(fig, dpi=300)
                    plt.close(fig)

                current_date += step

        print(f"Saved PDF for scenario {scenario.upper()}, month {m.upper()} at {pdf_path}")
