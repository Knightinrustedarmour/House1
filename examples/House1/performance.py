import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

# --- Helper: Try both tuple and SolphLabel headers ---
def get_flow(results, tuple_key):
    # Build SolphLabel form of the key
    solph_key = tuple(
        f"SolphLabel(location='{a}', mtress_component='{b}', solph_node='{c}')"
        for (a, b, c) in tuple_key
    )

    # Try tuple version
    try:
        return results[tuple_key]
    except KeyError:
        pass

    # Try SolphLabel version
    try:
        return results[solph_key]
    except KeyError:
        pass

    raise KeyError(f"❌ Could not find flow for: {tuple_key}\nPresent columns:\n{list(results.columns)[:10]}...")


# --- Set working directory to script folder ---
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)
print("WORKING DIRECTORY SET TO:", os.getcwd())

flows_dir = os.path.join(script_dir, "flows")
output_dir = os.path.join(script_dir, "output", "scenario_pdfs")
os.makedirs(output_dir, exist_ok=True)

# --- Months & scenarios ---
months = [
    ('mar', '2023-03-01', '2023-03-31'),
    ('apr', '2023-04-01', '2023-04-30'),
    ('may', '2023-05-01', '2023-05-31'),
    ('jun', '2023-06-01', '2023-06-30'),
    ('jul', '2023-07-01', '2023-07-31'),
    ('aug', '2023-08-01', '2023-08-31'),
    ('sep', '2023-09-01', '2023-09-30'),
]

scenarios = ['NB']  # add more when ready: ['NB','5K','8K','12K','15K','20K','26K','50K']

# --- Loop scenarios and months ---
for scenario in scenarios:
    for m, start, end in months:

        csv_path = os.path.join(flows_dir, f"flow_{scenario}_{m}23.csv")
        pdf_path = os.path.join(output_dir, f"{scenario}_{m}.pdf")

        results = pd.read_csv(csv_path, header=[0, 1], index_col=0, parse_dates=True)

        # Define flows
        col_grid_import = (('House1', 'ElectricityGridConnection', 'grid_import'),
                           ('House1', 'ElectricityCarrier', 'distribution'))
        col_grid_export = (('House1', 'ElectricityCarrier', 'feed_in'),
                           ('House1', 'ElectricityGridConnection', 'grid_export'))
        col_pv_dist = (('House1', 'PV', 'connection'),
                       ('House1', 'ElectricityCarrier', 'distribution'))
        col_demand = (('House1', 'demand', 'input'),
                        ('House1', 'demand', 'sink'))

        if scenario != 'NB':
            col_batt_charge = (('House1', 'ElectricityCarrier', 'distribution'),
                               ('House1', 'storage1', 'Battery_Storage'))
            col_batt_discharge = (('House1', 'storage1', 'Battery_Storage'),
                                   ('House1', 'ElectricityCarrier', 'distribution'))
        else:
            col_batt_charge = col_batt_discharge = None

        # Build DF
        df = pd.DataFrame(index=pd.to_datetime(results.index, utc=True))
        df["Grid_import"] = get_flow(results, col_grid_import)
        df["Grid_export"] = get_flow(results, col_grid_export)
        df["PV_Distribution"] = get_flow(results, col_pv_dist)
        df["Demand"] = get_flow(results, col_demand)

        if scenario != 'NB':
            df["Battery_charge"] = get_flow(results, col_batt_charge)
            df["Battery_discharge"] = get_flow(results, col_batt_discharge)
        else:
            df["Battery_charge"] = 0
            df["Battery_discharge"] = 0

        df["PV_self"] = (df["PV_Distribution"] - df["Battery_charge"]).clip(lower=0)
        df = df / 60000.0  # convert Wh-min → kWh

        start_date = pd.Timestamp(start, tz='UTC')
        end_date = pd.Timestamp(end, tz='UTC')
        step = pd.Timedelta(days=7)
        df = df[(df.index >= start_date) & (df.index <= end_date)]

        # Export PDF
        with PdfPages(pdf_path) as pdf:
            current_date = start_date
            while current_date <= end_date:
                end_interval = min(current_date + step - pd.Timedelta(days=1), end_date)
                df_filtered = df.loc[(df.index >= current_date) & (df.index <= end_interval)]

                if not df_filtered.empty:
                    fig, axes = plt.subplots(nrows=2, ncols=1, figsize=(21, 9), sharex=True, dpi=150)
                    plt.subplots_adjust(hspace=0.5)

                    df_filtered["Grid_import"].plot(ax=axes[0], label="Grid Import (kWh)")
                    df_filtered["Grid_export"].plot(ax=axes[0], label="Grid Export (kWh)")
                    df_filtered["Demand"].plot(ax=axes[0], label="Demand (kWh)", linestyle="--")
                    axes[0].set_ylabel("Energy (kWh)")
                    axes[0].legend()
                    axes[0].grid(True)

                    if scenario != 'NB':
                        df_filtered["Battery_charge"].plot(ax=axes[1], label="Battery Charge (kWh)")
                        df_filtered["Battery_discharge"].plot(ax=axes[1], label="Battery Discharge (kWh)", linestyle="--")

                    df_filtered["PV_self"].plot(ax=axes[1], label="PV Self-Use (kWh)", linestyle=":")
                    axes[1].set_ylabel("Energy (kWh)")
                    axes[1].legend()
                    axes[1].grid(True)

                    fig.suptitle(f"{scenario} — {current_date.date()} to {end_interval.date()}", fontsize=16)
                    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
                    pdf.savefig(fig)
                    plt.close(fig)

                current_date += step

        print(f"✅ Saved PDF for {scenario}, month {m} → {pdf_path}")
