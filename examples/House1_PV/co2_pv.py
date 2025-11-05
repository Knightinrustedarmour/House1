

import os
import pandas as pd

# --- CO2 Factors (gCO2eq) ---
CO2_EMISSION_FACTORS = {
    "Grid_import": 471,  # gCO2eq per kWh
    "PV_manufacturing": 515 * 26.5,# 515 gCO2eq/kWh * 26.5 kW installed peak power
    "PV_manufacturing2": 670 * 3.5  # 670 gCO2eq/kWh * 3.5 kW installed peak power
}

# --- Battery Manufacturing CO2 (gCO2eq per year) ---
# Formula: capacity (kWh) * 109 kgCO2eq/kWh * 1000 g/kg / 20-year lifespan = per-year impact
BATTERY_MANUFACTURING_CO2_G = {
    "PV_NoBattery": 0,
    "5kWh": 5 * 109 * 50,
    "8kWh": 8 * 109 * 50,
    "12kWh": 12 * 109 * 50,
    "15kWh": 15 * 109 * 50,
    "20kWh": 20 * 109 * 50,
    "26kWh": 26 * 109 * 50,
    "50kWh": 50 * 109 * 50,
}


def calculate_monthly_co2_emissions(scenario_identifier, scenario_config):
    """Calculates monthly and yearly CO2 emissions for a given scenario, considering:
       - Grid import operational emissions
       - PV manufacturing emissions
       - Battery manufacturing emissions
    """
    monthly_data = []

    GRID_FLOW_LABELS = [
        ("SolphLabel(location='House1', mtress_component='ElectricityGridConnection', solph_node='grid_import')",
         "SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='distribution')"),
        ("('House1', 'ElectricityGridConnection', 'grid_import')",
         "('House1', 'ElectricityCarrier', 'distribution')")
    ]

    for month_name, filename in scenario_config["files"].items():
        filepath = os.path.join(scenario_config["flow_dir"], filename)
        if not os.path.exists(filepath):
            continue

        try:
            results = pd.read_csv(filepath, header=[0, 1], index_col=0)
            results.index = pd.to_datetime(results.index, utc=True)
        except Exception:
            continue

        # --- Extract grid import flow ---
        total_grid_import_kwh = 0.0
        for solph_label in GRID_FLOW_LABELS:
            try:
                data_series = results[solph_label]
                total_grid_import_kwh = data_series.sum() / 60000  # adjust factor to match your data scale
                break
            except KeyError:
                continue

        # --- CO2 Calculations ---
        co2_grid_import = total_grid_import_kwh * CO2_EMISSION_FACTORS["Grid_import"]
        co2_pv_mfg = CO2_EMISSION_FACTORS["PV_manufacturing"] + CO2_EMISSION_FACTORS["PV_manufacturing2"]
        co2_battery_mfg = BATTERY_MANUFACTURING_CO2_G.get(scenario_identifier, 0)

        total_co2_emissions_g = co2_pv_mfg + co2_battery_mfg + co2_grid_import

        monthly_data.append({
            "Scenario": scenario_identifier,
            "Month": month_name,
            "Grid Import (kWh)": total_grid_import_kwh,
            "CO2 from PV Manufacturing (gCO2eq)": co2_pv_mfg,
            "CO2 from Battery Manufacturing (gCO2eq)": co2_battery_mfg,
            "CO2 from Grid Import (gCO2eq)": co2_grid_import,
            "Total CO2 Emissions (gCO2eq)": total_co2_emissions_g
        })

    if not monthly_data:
        return None, None

    df_monthly = pd.DataFrame(monthly_data)

    yearly_total_grid_import = df_monthly["Grid Import (kWh)"].sum()
    yearly_co2_grid_import = df_monthly["CO2 from Grid Import (gCO2eq)"].sum()
    co2_pv_mfg = CO2_EMISSION_FACTORS["PV_manufacturing"] + CO2_EMISSION_FACTORS["PV_manufacturing2"]
    co2_battery_mfg = BATTERY_MANUFACTURING_CO2_G.get(scenario_identifier, 0)
    yearly_total_co2_emissions = co2_pv_mfg + co2_battery_mfg + yearly_co2_grid_import

    yearly_summary = pd.DataFrame({
        "Scenario": [scenario_identifier],
        "Total Yearly Grid Import (kWh)": [yearly_total_grid_import],
        "Yearly CO2 from PV Manufacturing (gCO2eq)": [co2_pv_mfg],
        "Yearly CO2 from Battery Manufacturing (gCO2eq)": [co2_battery_mfg],
        "Yearly CO2 from Grid Import (gCO2eq)": [yearly_co2_grid_import],
        "Total Yearly CO2 Emissions (gCO2eq)": [yearly_total_co2_emissions]
    })

    return df_monthly, yearly_summary


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "output", "co2_footprint_analysis_csv")
    os.makedirs(output_dir, exist_ok=True)

    # --- Scenario configurations ---
    scenarios_config = {
        # PV without battery (special naming pattern)
        "PV_NoBattery": {
            "flow_dir": os.path.join(script_dir, "flows"),
            "files": {m: f"flow_nobattery_{m}23.csv" for m in
                      ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']},
        },
        # Battery scenarios (standard naming pattern)
        **{
            f"{k}kWh": {
                "flow_dir": os.path.join(script_dir, "flows"),
                "files": {m: f"flow_{k}k_{m}23.csv" for m in
                          ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']},
            }
            for k in [5, 8, 12, 15, 20, 26, 50]
        }
    }

    all_monthly, all_yearly = [], []
    month_order = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']

    for scenario, config in scenarios_config.items():
        monthly_df, yearly_df = calculate_monthly_co2_emissions(scenario, config)
        if monthly_df is not None:
            all_monthly.append(monthly_df)
        if yearly_df is not None:
            all_yearly.append(yearly_df)

    # --- Combine all yearly results ---
    if all_yearly:
        df_yearly_all = pd.concat(all_yearly).set_index("Scenario")

        # --- Save in gCO2eq ---
        gco2eq_path = os.path.join(output_dir, "annual_co2_all_scenarios_gCO2eq.csv")
        df_yearly_all.to_csv(gco2eq_path, float_format="%.2f")

        # --- Convert to kgCO2eq ---
        df_yearly_kg = df_yearly_all.copy() / 1000
        df_yearly_kg.rename(columns=lambda c: c.replace("(gCO2eq)", "(kgCO2eq)"), inplace=True)
        kgco2eq_path = os.path.join(output_dir, "annual_co2_all_scenarios_kgCO2eq.csv")
        df_yearly_kg.to_csv(kgco2eq_path, float_format="%.3f")

        print("\n✅ CO2 Footprint Summary Saved:")
        print(f"- {gco2eq_path}")
        print(f"- {kgco2eq_path}")
        print("\nPreview:\n", df_yearly_all.head())
