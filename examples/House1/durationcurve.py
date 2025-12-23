import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# -----------------------------
# --- Setup & Configuration ---
# -----------------------------
try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
except NameError:
    script_dir = os.getcwd()

FLOW_DIR = os.path.join(script_dir, "flows")
OUTPUT_DIR = os.path.join(script_dir,"output", "duration_curves")
os.makedirs(OUTPUT_DIR, exist_ok=True)

FIG_WIDTH = 14
FIG_HEIGHT = 6

sns.set(style="whitegrid", context="talk", font_scale=1.1)


# ----------------------------------------------------------
# --- Header-Flexible Labels (reusing design language) -----
# ----------------------------------------------------------
ALL_FLOWS = {
    "Grid_Import": [
        ("SolphLabel(location='House1', mtress_component='ElectricityGridConnection', solph_node='grid_import')",
         "SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='distribution')"),
        ("('House1', 'ElectricityGridConnection', 'grid_import')",
         "('House1', 'ElectricityCarrier', 'distribution')")
    ],
    "Grid_Export": [
        ("SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='feed_in')",
         "SolphLabel(location='House1', mtress_component='ElectricityGridConnection', solph_node='grid_export')"),
        ("('House1', 'ElectricityCarrier', 'feed_in')",
         "('House1', 'ElectricityGridConnection', 'grid_export')")
    ],
    "PV_Direct": [
        ("SolphLabel(location='House1', mtress_component='PV', solph_node='connection')",
         "SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='distribution')"),
        ("('House1', 'PV', 'connection')",
         "('House1', 'ElectricityCarrier', 'distribution')")
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

# ----------------------------------------------------------
# --- Scenarios & Files (same structure as your script) ----
# ----------------------------------------------------------
SCENARIOS = {
    
    "PV_NoBattery": {m: f"flow_NB_{m}23.csv" for m in
                     ["jan","feb","mar","apr","may","jun","jul","aug","sep","oct","nov","dec"]},

    "5kWh": {m: f"flow_5k_{m}23.csv" for m in
             ["jan","feb","mar","apr","may","jun","jul","aug","sep","oct","nov","dec"]},

    "8kWh": {m: f"flow_8k_{m}23.csv" for m in
             ["jan","feb","mar","apr","may","jun","jul","aug","sep","oct","nov","dec"]},

    "12kWh": {m: f"flow_12k_{m}23.csv" for m in
              ["jan","feb","mar","apr","may","jun","jul","aug","sep","oct","nov","dec"]},

    "15kWh": {m: f"flow_15k_{m}23.csv" for m in
              ["jan","feb","mar","apr","may","jun","jul","aug","sep","oct","nov","dec"]},

    "20kWh": {m: f"flow_20k_{m}23.csv" for m in
              ["jan","feb","mar","apr","may","jun","jul","aug","sep","oct","nov","dec"]},

    "26kWh": {m: f"flow_26k_{m}23.csv" for m in
              ["jan","feb","mar","apr","may","jun","jul","aug","sep","oct","nov","dec"]},

    "50kWh": {m: f"flow_50k_{m}23.csv" for m in
              ["jan","feb","mar","apr","may","jun","jul","aug","sep","oct","nov","dec"]}
}


# ----------------------------------------------------------
# --- Function: Load all hourly flows for one scenario -----
# ----------------------------------------------------------
def load_hourly_flow(scenario, flow_key):
    """Returns a single long hourly vector for a given scenario and flow type."""

    hourly_values = []

    for month, filename in SCENARIOS[scenario].items():
        path = os.path.join(FLOW_DIR, filename)
        if not os.path.exists(path):
            print(f"Missing file: {path}")
            continue

        try:
            df = pd.read_csv(path, header=[0, 1], index_col=0)
        except Exception as e:
            print(f"Error reading {path}: {e}")
            continue

        # Try both header formats
        value_series = None
        for solph_pair in ALL_FLOWS[flow_key]:
            try:
                value_series = df[solph_pair]
                break
            except KeyError:
                continue

        if value_series is None:
            print(f"No matching columns for {flow_key} in {path}")
            continue

        hourly_values.extend(value_series.values)

    return np.array(hourly_values)


# ----------------------------------------------------------
# --- Function: Plot Duration Curve for one flow type -------
# ----------------------------------------------------------
def plot_duration_curve(flow_key, flow_title):
    plt.figure(figsize=(FIG_WIDTH, FIG_HEIGHT))

    for scenario in SCENARIOS.keys():
        values = load_hourly_flow(scenario, flow_key)

        if len(values) == 0:
            continue

        # Duration curve
        sorted_vals = np.sort(values)[::-1]  

        plt.plot(sorted_vals, label=scenario, linewidth=2)

    plt.title(f"{flow_title} – Duration Curve", fontsize=18, fontweight="bold", pad=20)
    plt.xlabel("Hours Sorted (Descending)")
    plt.ylabel("Power Flow (W)")
    plt.grid(alpha=0.4, linestyle="--")
    plt.legend()
    plt.tight_layout()

    filename = os.path.join(OUTPUT_DIR, f"DurationCurve_{flow_key}.png")
    plt.savefig(filename, dpi=300)
    plt.close()
    print(f"Saved: {filename}")


# -----------------------------
# --- Generate All Plots ------
# -----------------------------
print("\n--- Generating Duration Curves ---")

PLOT_LIST = {
    "Grid_Import": "Grid Import",
    "Grid_Export": "Grid Export",
    "PV_Direct": "PV Self-Consumption",
    "Battery_Charge": "Battery Charging",
    "Battery_Discharge": "Battery Discharging"
}

for key, title in PLOT_LIST.items():
    plot_duration_curve(key, title)

print("\n✅ All duration curve plots saved in:", OUTPUT_DIR)
