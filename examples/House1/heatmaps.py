import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# -----------------------------------------------------------------------------
# Set working directory
# -----------------------------------------------------------------------------
os.chdir(os.path.dirname(__file__))

# -----------------------------------------------------------------------------
# Month definitions (full)
# -----------------------------------------------------------------------------
months = [
    ("jan", "2023-01-01", "2023-01-31"),
    ("feb", "2023-02-01", "2023-02-28"),
    ("mar", "2023-03-01", "2023-03-31"),
    ("apr", "2023-04-01", "2023-04-30"),
    ("may", "2023-05-01", "2023-05-31"),
    ("jun", "2023-06-01", "2023-06-30"),
    ("jul", "2023-07-01", "2023-07-31"),
    ("aug", "2023-08-01", "2023-08-31"),
    ("sep", "2023-09-01", "2023-09-30"),
    ("oct", "2023-10-01", "2023-10-31"),
    ("nov", "2023-11-01", "2023-11-30"),
    ("dec", "2023-12-01", "2023-12-31"),
]

# -----------------------------------------------------------------------------
# Scenarios (NoPV ignored)
# -----------------------------------------------------------------------------
scenarios = ["5k", "8k", "12k", "15k", "20k", "26k", "50k", "NB"]

# -----------------------------------------------------------------------------
# Color scale boundaries (fixed across all plots)
# -----------------------------------------------------------------------------
V_MIN = -0.5
V_MAX = 0.5

# -----------------------------------------------------------------------------
# Helper: convert to heatmap matrix
# -----------------------------------------------------------------------------
def df_to_heatmap_matrix(df, value_column):
    """
    Converts a datetime-indexed df into a heatmap matrix:
    rows: time of day
    columns: day of month
    """
    temp = df.copy()
    temp["day"] = temp.index.day
    temp["time"] = temp.index.time

    hm = temp.pivot_table(index="time", columns="day", values=value_column)
    hm = hm.sort_index()
    return hm

# -----------------------------------------------------------------------------
# Main loop over scenarios and months
# -----------------------------------------------------------------------------
for scenario in scenarios:

    # Output dir for scenario
    scenario_dir = os.path.join("output", "scenario_heatmaps", scenario)
    os.makedirs(scenario_dir, exist_ok=True)

    for month_name, start_date, end_date in months:

        # ---------------------------------------------------------------------
        # Read input CSV
        # ---------------------------------------------------------------------
        csv_path = os.path.join("flows", f"flow_{scenario}_{month_name}23.csv")

        if not os.path.exists(csv_path):
            print(f"Missing CSV: {csv_path}")
            continue

        # Load CSV with MultiIndex header
        results = pd.read_csv(csv_path, header=[0, 1], index_col=0, parse_dates=True)
        df = pd.DataFrame(index=pd.to_datetime(results.index, utc=True))

        # ---------------------------------------------------------------------
        # Extract flows using EXACT KEYS
        # ---------------------------------------------------------------------
        df["Grid_import"] = results[
            ("('House1', 'ElectricityGridConnection', 'grid_import')",
             "('House1', 'ElectricityCarrier', 'distribution')")
        ]

        df["Grid_export"] = results[
            ("('House1', 'ElectricityCarrier', 'feed_in')",
             "('House1', 'ElectricityGridConnection', 'grid_export')")
        ]

        df["Demand"] = results[
            ("('House1', 'ElectricityCarrier', 'distribution')",
             "('House1', 'demand', 'input')")
        ]

        # Battery flows
        if scenario != "NB":
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

        # ---------------------------------------------------------------------
        # Convert Wmin → kWh
        # ---------------------------------------------------------------------
        df = df / 60000.0

        # ---------------------------------------------------------------------
        # Filter month
        # ---------------------------------------------------------------------
        df = df[(df.index >= pd.Timestamp(start_date, tz="UTC")) &
                (df.index <= pd.Timestamp(end_date, tz="UTC"))]

        if df.empty:
            print(f"No data for {scenario} {month_name}.")
            continue

        # ---------------------------------------------------------------------
        # Compute derived metrics
        # ---------------------------------------------------------------------
        df["Net_energy"] = df["Grid_import"] - df["Grid_export"]
        df["Net_battery"] = df["Battery_charge"] - df["Battery_discharge"]

        # ---------------------------------------------------------------------
        # Select which metrics to plot
        # ---------------------------------------------------------------------
        metrics_to_plot = [("Net_energy", "Net Energy Flow")]

        if scenario != "NB":
            metrics_to_plot.append(("Net_battery", "Net Battery Flow"))

        # ---------------------------------------------------------------------
        # Plot each metric
        # ---------------------------------------------------------------------
        for col, title in metrics_to_plot:

            heatmap_data = df_to_heatmap_matrix(df, col)

            if heatmap_data.empty:
                continue

            # -------------------------------------------------------------
            # Create large figure
            # -------------------------------------------------------------
            plt.figure(figsize=(24, 10))

            plt.title(f"{title} – {month_name.capitalize()} – {scenario}", fontsize=20)

            # -------------------------------------------------------------
            # Heatmap with fixed vmin/vmax and saturated colormap
            # -------------------------------------------------------------
            plt.imshow(
                heatmap_data,
                aspect="auto",
                origin="lower",
                cmap="RdBu_r",     # deep color, no white
                vmin=V_MIN,
                vmax=V_MAX,
                interpolation="nearest"
            )

            # -------------------------------------------------------------
            # Colorbar (aligned across all months)
            # -------------------------------------------------------------
            cbar = plt.colorbar()
            cbar.set_label(f"{title} (kWh)", fontsize=14)

            # -------------------------------------------------------------
            # Axis formatting
            # -------------------------------------------------------------
            plt.xlabel("Day of Month", fontsize=14)
            plt.ylabel("Time of Day", fontsize=14)

            # X axis ticks (days)
            plt.xticks(
                ticks=np.arange(len(heatmap_data.columns)),
                labels=heatmap_data.columns,
                rotation=45
            )

            # Y axis ticks (roughly hourly)
            time_labels = [t.strftime("%H:%M") for t in heatmap_data.index]
            step = max(len(time_labels) // 24, 1)
            plt.yticks(
                ticks=np.arange(0, len(time_labels), step),
                labels=time_labels[::step]
            )

            # -------------------------------------------------------------
            # File name (no underscores in title)
            # -------------------------------------------------------------
            safe_title = title.replace("_", " ")
            png_name = f"{scenario}_{month_name}_{safe_title.replace(' ', '')}.png"
            png_path = os.path.join(scenario_dir, png_name)

            # -------------------------------------------------------------
            # Save figure
            # -------------------------------------------------------------
            plt.savefig(png_path, dpi=450, bbox_inches="tight")
            plt.close()

            print(f"Saved: {png_path}")
