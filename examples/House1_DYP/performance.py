import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FLOW_DIR = os.path.join(BASE_DIR, "House1_DYP", "flows")
OUT_DIR  = os.path.join(BASE_DIR, "House1_DYP", "output")
PNG_DIR  = os.path.join(OUT_DIR, "plots")
PDF_DIR  = os.path.join(OUT_DIR, "scenario_pdfs")

os.makedirs(PNG_DIR, exist_ok=True)
os.makedirs(PDF_DIR, exist_ok=True)

SCENARIOS = ["PV_NoBattery", "5kWh", "8kWh", "12kWh",
             "15kWh", "20kWh", "26kWh", "50kWh"]
MONTHS = ["jan23", "apr23", "aug23", "oct23", "dec23"]

# Map scenario to filename prefix
SCENARIO_MAP = {
    "PV_NoBattery": "NB",
    "5kWh": "5k",
    "8kWh": "8k",
    "12kWh": "12k",
    "15kWh": "15k",
    "20kWh": "20k",
    "26kWh": "26k",
    "50kWh": "50k",
}

# 4 weekly windows (in days since start of month)
WEEKS = [(0,7), (7,14), (14,21), (21,28)]


# --------------------------------------------------
# LOAD CSV
# --------------------------------------------------
def load_results(filepath):
    # Read CSV with two header rows
    df = pd.read_csv(filepath, header=[0,1], index_col=0, parse_dates=True)

    # Normalize index to remove timezone
    if df.index.tz is not None:
        df.index = df.index.tz_convert(None)
    print("\nLoaded columns:")
    for c in df.columns:
     print(c)


    return df


# ------------------------------
# Column mapping
# ------------------------------
COL_MAP = {
    "Grid_import": [
        ("('House1', 'ElectricityGridConnection', 'grid_import')",
         "('House1', 'ElectricityCarrier', 'distribution')")
    ],
    "Grid_export": [
        ("('House1', 'ElectricityCarrier', 'feed_in')",
         "('House1', 'ElectricityGridConnection', 'grid_export')")
    ],
    "Battery_Charge": [
        ("SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='distribution')",
         "SolphLabel(location='House1', mtress_component='storage1', solph_node='Battery_Storage')"),
        ("('House1', 'ElectricityCarrier', 'distribution')",
         "('House1', 'storage1', 'Battery_Storage')")
    ],
    "Battery_Discharge": [
        ("SolphLabel(location='House1', mtress_component='storage1', solph_node='Battery_Storage')",
         "SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='distribution')"),
        ("('House1', 'storage1', 'Battery_Storage')",
         "('House1', 'ElectricityCarrier', 'distribution')")
    ]
}

# ------------------------------
# Adjusted plot_results
# ------------------------------
def plot_results(df, scenario, month, save_dir, week_start, week_end):
    # Slice one week
    start_date = df.index.min().normalize() + pd.Timedelta(days=week_start)
    end_date   = df.index.min().normalize() + pd.Timedelta(days=week_end)
    df_week = df.loc[(df.index >= start_date) & (df.index < end_date)]
    if df_week.empty:
        print(f"    No data for {scenario} - {month} in week {week_start//7+1}, skipping.")
        return

    # Build a clean dataframe
    df_filtered = pd.DataFrame(index=df_week.index)

    for label, pairs in COL_MAP.items():
        found = False
        for pair in pairs:
            if pair in df_week.columns:
                df_filtered[label] = df_week[pair]
                found = True
                break
        if not found:
            df_filtered[label] = 0.0  # fallback if not found

    # Plotting
    fig, axes = plt.subplots(nrows=2, ncols=1, figsize=(14, 8), sharex=True)
    plt.subplots_adjust(hspace=0.3)

    # Grid import/export
    if df_filtered["Grid_import"].sum() != 0:
        df_filtered["Grid_import"].plot(ax=axes[0], label="Grid Import (W)", color="blue")
    if df_filtered["Grid_export"].sum() != 0:
        df_filtered["Grid_export"].plot(ax=axes[0], label="Grid Export (W)", color="orange")
    axes[0].set_ylabel("Grid Power (W)")
    axes[0].legend(bbox_to_anchor=(1,1), loc='upper right')
    axes[0].grid(True)

    # Battery charge/discharge
    if df_filtered["Battery_Charge"].sum() != 0:
        df_filtered["Battery_Charge"].plot(ax=axes[1], label="Battery Charge (W)", color="green")
    if df_filtered["Battery_Discharge"].sum() != 0:
        df_filtered["Battery_Discharge"].plot(ax=axes[1], label="Battery Discharge (W)",
                                              color="purple", linestyle="--")
    axes[1].set_ylabel("Battery Power (W)")
    axes[1].set_xlabel("Time")
    axes[1].legend(bbox_to_anchor=(1,1), loc='upper right')
    axes[1].grid(True)

    fig.suptitle(f"{scenario} - {month.upper()} - Week {week_start//7+1}", fontsize=14)
    fig.tight_layout(rect=[0,0,1,0.96])

    # Save figure
    fname = os.path.join(save_dir, f"{scenario}_{month}_week{week_start//7+1}.png")
    fig.savefig(fname, dpi=150)
    plt.close(fig)
    print(f"    Saved plot: {fname}")




# --------------------------------------------------
# MAIN PROCESS
# --------------------------------------------------
print("--- Starting Data Loading, Plotting and PDF Creation ---")
print(f"Base directory assumed: {BASE_DIR}\n")

for scenario in SCENARIOS:
    print(f"Processing scenario: {scenario}")
    prefix = SCENARIO_MAP[scenario]

    for month in MONTHS:
        fname = f"flow_{prefix}_{month}.csv"
        file_path = os.path.join(FLOW_DIR, fname)

        print(f"  Checking file: {file_path}")

        if not os.path.exists(file_path):
            print(f"    File missing, skipping.")
            continue

        try:
            df = load_results(file_path)

            for wstart, wend in WEEKS:
                plot_results(df, scenario, month, PNG_DIR, wstart, wend)

        except Exception as e:
            print(f"  ERROR loading/plotting {file_path}: {type(e).__name__}: {e}")
            continue


# --------------------------------------------------
# MERGE PNGS INTO PDF PER SCENARIO
# --------------------------------------------------
print("\n--- Creating PDFs ---")
for scenario in SCENARIOS:
    pngs = [os.path.join(PNG_DIR, f) for f in os.listdir(PNG_DIR)
            if f.startswith(scenario+"_")]
    pngs.sort()

    if not pngs:
        print(f"  No plots found for scenario {scenario}, skipping PDF.")
        continue

    pdf_path = os.path.join(PDF_DIR, f"weekly_flows_{scenario}.pdf")
    with PdfPages(pdf_path) as pdf:
        for png in pngs:
            img = plt.imread(png)
            fig, ax = plt.subplots(figsize=(12,6))
            ax.imshow(img)
            ax.axis('off')
            pdf.savefig(fig)
            plt.close(fig)

    print(f"  PDF created for {scenario}: {pdf_path}")

print("\nAll processing complete.")
