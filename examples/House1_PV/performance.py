import os
import pandas as pd
import matplotlib.pyplot as plt

os.chdir(os.path.dirname(__file__))

months = [
    ('jan', '2023-01-01', '2023-01-31'),
    ('apr', '2023-04-01', '2023-04-30'),
    ('jul', '2023-07-01', '2023-07-31'),
    ('sep', '2023-09-01', '2023-09-30'),
    ('dec', '2023-12-01', '2023-12-31'),
]

scenarios = ['5k', '8k', '12k', '15k', '20k', '26k', '50k', 'nobattery']

for scenario in scenarios:
    for m, start, end in months:

        csv_path = os.path.join("flows", f"flow_{scenario}_{m}23.csv")

        out_dir = os.path.join("output", "scenario_pngs", scenario)
        os.makedirs(out_dir, exist_ok=True)

        results = pd.read_csv(csv_path, header=[0, 1], index_col=0, parse_dates=True)
        df = pd.DataFrame(index=results.index)
        df.index = pd.to_datetime(df.index, utc=True)

        # Battery flows
        if scenario != 'nobattery':
            df["Battery_charge"] = results[
                ("('House1', 'ElectricityCarrier', 'distribution')",
                 "('House1', 'storage1', 'Battery_Storage')")
            ]
            df["Battery_discharge"] = results[
                ("('House1', 'storage1', 'Battery_Storage')",
                 "('House1', 'ElectricityCarrier', 'distribution')")
            ]
        else:
            df["Battery_charge"] = 0
            df["Battery_discharge"] = 0

        df["Grid_import"] = results[
            ("('House1', 'ElectricityGridConnection', 'grid_import')",
             "('House1', 'ElectricityCarrier', 'distribution')")
        ]
        df["Grid_export"] = results[
            ("('House1', 'ElectricityCarrier', 'feed_in')",
             "('House1', 'ElectricityGridConnection', 'grid_export')")
        ]
        df["PV_Distribution"] = results[
            ("('House1', 'PV', 'connection')",
             "('House1', 'ElectricityCarrier', 'distribution')")
        ]
        df["PV_Distribution2"] = results[
            ("('House1', 'PV2', 'connection')",
             "('House1', 'ElectricityCarrier', 'distribution')")
        ]

        # PV self-consumption
        df["PV_self"] = df["PV_Distribution"] + df["PV_Distribution2"] - df["Battery_charge"]
        df["PV_self"] = df["PV_self"].clip(lower=0)

        # Convert W·min → kWh
        df = df / 60000.0

        start_date = pd.Timestamp(start, tz='UTC')
        end_date = pd.Timestamp(end, tz='UTC')
        step = pd.Timedelta(days=7)

        df = df[(df.index >= start_date) & (df.index <= end_date)]

        current_date = start_date
        week_idx = 1

        while current_date <= end_date:
            end_interval = min(current_date + step - pd.Timedelta(days=1), end_date)
            df_filtered = df[(df.index >= current_date) & (df.index <= end_interval)]

            if not df_filtered.empty:
                fig, axes = plt.subplots(
                    nrows=2, ncols=1, figsize=(21, 9), sharex=True, dpi=150
                )
                plt.subplots_adjust(hspace=0.5)

                # Grid flows
                df_filtered["Grid_import"].plot(ax=axes[0], label="Grid Import (kWh)")
                df_filtered["Grid_export"].plot(ax=axes[0], label="Grid Export (kWh)")
                axes[0].set_ylabel("Energy (kWh)")
                axes[0].legend(loc="upper right")
                axes[0].grid(True)

                # Battery + PV
                if scenario != 'nobattery':
                    df_filtered["Battery_charge"].plot(
                        ax=axes[1], label="Battery Charge (kWh)"
                    )
                    df_filtered["Battery_discharge"].plot(
                        ax=axes[1], label="Battery Discharge (kWh)", linestyle="--"
                    )

                df_filtered["PV_self"].plot(
                    ax=axes[1], label="PV Self-Use (kWh)", linestyle=":"
                )

                axes[1].set_xlabel("Time")
                axes[1].set_ylabel("Energy (kWh)")
                axes[1].legend(loc="upper right")
                axes[1].grid(True)

                fig.suptitle(
                    f"Energy Flows ({current_date.date()} to {end_interval.date()}) – {scenario}",
                    fontsize=16
                )
                plt.tight_layout(rect=[0, 0.03, 1, 0.95])

                # ---- Save PNG ----
                png_name = f"pv_{scenario}_{m}_week{week_idx}.png"
                png_path = os.path.join(out_dir, png_name)

                plt.savefig(png_path, dpi=300, bbox_inches="tight")
                plt.close(fig)

                print(f"Saved PNG: {png_path}")

                week_idx += 1

            current_date += step
