import os
import pandas as pd

CO2_EMISSION_FACTORS = {
    "PV_production": 22,
    "Battery_discharge": 53,
    "Grid_import": 471,
}

# Source: Values provided by user (converted from kgCO2eq to gCO2eq)
BATTERY_MANUFACTURING_CO2_G = {
    "5kWh": 5 * 109 * 50,  # 5 kWh capacity * 109 kg/kWh * 1000 g/kg / 20 per year lifespan
    "8kWh": 8 * 109 * 50,
    "12kWh": 12 * 109 * 50,
    "15kWh": 15 * 109 * 50,
    "20kWh": 20 * 109 * 50,
    "26kWh": 26 * 109 * 50,
    "50kWh": 50 * 109 * 50,
}

def calculate_monthly_co2_emissions(scenario_identifier, scenario_config):
    """Calculates monthly and yearly CO2 emissions for a given scenario."""
    monthly_data = []

    ALL_FLOWS = {
        "PV_production": [
            ("SolphLabel(location='House1', mtress_component='PV', solph_node='source')",
             "SolphLabel(location='House1', mtress_component='PV', solph_node='connection')"),
            ("('House1', 'PV', 'source')", "('House1', 'PV', 'connection')")
        ],
        "Battery_discharge": [
            ("SolphLabel(location='House1', mtress_component='storage1', solph_node='Battery_Storage')",
             "SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='distribution')"),
            ("('House1', 'storage1', 'Battery_Storage')", "('House1', 'ElectricityCarrier', 'distribution')")
        ],
        "Grid_import": [
            ("SolphLabel(location='House1', mtress_component='ElectricityGridConnection', solph_node='grid_import')",
             "SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='distribution')"),
            ("('House1', 'ElectricityGridConnection', 'grid_import')", "('House1', 'ElectricityCarrier', 'distribution')")
        ],
        "Demand": [
            ("SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='distribution')",
             "SolphLabel(location='House1', mtress_component='demand', solph_node='input')"),
            ("('House1', 'ElectricityCarrier', 'distribution')", "('House1', 'demand', 'input')")
        ],
    }

    for month_name, filename in scenario_config["files"].items():
        filepath = os.path.join(scenario_config["flow_dir"], filename)
        if not os.path.exists(filepath):
            continue
        try:
            results = pd.read_csv(filepath, header=[0, 1], index_col=0)
            results.index = pd.to_datetime(results.index, utc=True)
        except Exception as e:
            continue

        flow_data = {}
        for flow_name, solph_labels in ALL_FLOWS.items():
            for solph_label in solph_labels:
                try:
                    data_series = results[solph_label]
                    flow_data[flow_name] = data_series.sum()
                    break
                except KeyError:
                    continue
            if flow_name not in flow_data:
                flow_data[flow_name] = 0.0

        if not flow_data:
            continue

        total_pv_kwh = flow_data.get("PV_production", 0) / 60000
        total_grid_import_kwh = flow_data.get("Grid_import", 0) / 60000
        total_battery_discharge_kwh = flow_data.get("Battery_discharge", 0) / 60000
        total_demand_kwh = flow_data.get("Demand", 0) / 60000

        co2_pv = total_pv_kwh * CO2_EMISSION_FACTORS["PV_production"]
        co2_grid_import = total_grid_import_kwh * CO2_EMISSION_FACTORS["Grid_import"]
        co2_battery_discharge = total_battery_discharge_kwh * CO2_EMISSION_FACTORS["Battery_discharge"]
        mfg_co2 = BATTERY_MANUFACTURING_CO2_G.get(scenario_identifier, 0)
        
        # Uncomment the desired calculation for total monthly CO2 emissions
        #total_co2_emissions_g = co2_pv + co2_grid_import + co2_battery_discharge + mfg_co2
        total_co2_emissions_g = co2_pv + co2_grid_import + mfg_co2
        #total_co2_emissions_g = co2_pv + co2_grid_import + co2_battery_discharge

        monthly_data.append({
            "Scenario": scenario_identifier,
            "Month": month_name,
            "Total Demand (kWh)": total_demand_kwh,
            "PV Production (kWh)": total_pv_kwh,
            "Grid Import (kWh)": total_grid_import_kwh,
            "Battery Discharge (kWh)": total_battery_discharge_kwh,
            "CO2 from PV Production (gCO2eq)": co2_pv,
            "CO2 from Grid Import (gCO2eq)": co2_grid_import,
            "CO2 from Battery Discharge (gCO2eq)": co2_battery_discharge,
            "Total CO2 Emissions (gCO2eq)": total_co2_emissions_g
        })

    if not monthly_data:
        return None, None

    df_monthly = pd.DataFrame(monthly_data)
    
    yearly_total_demand = df_monthly["Total Demand (kWh)"].sum()
    yearly_total_pv_production = df_monthly["PV Production (kWh)"].sum()
    yearly_total_grid_import = df_monthly["Grid Import (kWh)"].sum()
    yearly_total_battery_discharge = df_monthly["Battery Discharge (kWh)"].sum()
    
    yearly_co2_pv = df_monthly["CO2 from PV Production (gCO2eq)"].sum()
    yearly_co2_grid_import = df_monthly["CO2 from Grid Import (gCO2eq)"].sum()
    yearly_co2_battery_discharge = df_monthly["CO2 from Battery Discharge (gCO2eq)"].sum()

    # Uncomment the desired calculation for total yearly CO2 emissions
    #yearly_total_co2_emissions = yearly_co2_pv + yearly_co2_grid_import + yearly_co2_battery_discharge + mfg_co2
    
    #yearly_total_co2_emissions = yearly_co2_pv + yearly_co2_grid_import + yearly_co2_battery_discharge
    yearly_total_co2_emissions = yearly_co2_pv + yearly_co2_grid_import + mfg_co2
    
    yearly_summary = pd.DataFrame({
        "Scenario": [scenario_identifier],
        "Total Yearly Demand (kWh)": [yearly_total_demand],
        "Total Yearly PV Production (kWh)": [yearly_total_pv_production],
        "Total Yearly Grid Import (kWh)": [yearly_total_grid_import],
        "Total Yearly Battery Discharge (kWh)": [yearly_total_battery_discharge],
        "Yearly CO2 from PV Production (gCO2eq)": [yearly_co2_pv],
        "Yearly CO2 from Grid Import (gCO2eq)": [yearly_co2_grid_import],
        "Yearly CO2 from Battery Discharge (gCO2eq)": [yearly_co2_battery_discharge],
        "Total Yearly CO2 Emissions (gCO2eq)": [yearly_total_co2_emissions]
    })
    return df_monthly, yearly_summary

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Uncomment the desired output directory
    #output_dir = os.path.join(script_dir, "output", "carbon_footprint_analysis_csv")
    #output_dir = os.path.join(script_dir, "output", "co3_footprint_analysis_csv")
    output_dir = os.path.join(script_dir, "output", "co2_footprint_analysis_csv")
    os.makedirs(output_dir, exist_ok=True)

    scenarios_config = {
        "NoPV": {
            "flow_dir": os.path.join(script_dir, "flows_nopv"),
            "files": {
                'jan': 'flow_nopv_jan23.csv', 'feb': 'flow_nopv_feb23.csv',
                'mar': 'flow_nopv_mar23.csv', 'apr': 'flow_nopv_apr23.csv', 'may': 'flow_nopv_may23.csv',
                'jun': 'flow_nopv_jun23.csv', 'jul': 'flow_nopv_jul23.csv', 'aug': 'flow_nopv_aug23.csv',
                'sep': 'flow_nopv_sep23.csv', 'oct': 'flow_nopv_oct23.csv', 'nov': 'flow_nopv_nov23.csv',
                'dec': 'flow_nopv_dec23.csv'
            },
            "has_pv": False,
            "has_battery": False
        },
        "PV_NoBattery": {
            "flow_dir": os.path.join(script_dir, "flows_nobattery"),
            "files": {
                'jan': 'flow_NB_jan23.csv', 'feb': 'flow_NB_feb23.csv',
                'mar': 'flow_NB_mar23.csv', 'apr': 'flow_NB_apr23.csv', 'may': 'flow_NB_may23.csv',
                'jun': 'flow_NB_jun23.csv', 'jul': 'flow_NB_jul23.csv', 'aug': 'flow_NB_aug23.csv',
                'sep': 'flow_NB_sep23.csv', 'oct': 'flow_NB_oct23.csv', 'nov': 'flow_NB_nov23.csv',
                'dec': 'flow_NB_dec23.csv'
            },
            "has_pv": True,
            "has_battery": False
        },
        "5kWh": {
            "flow_dir": os.path.join(script_dir, "flows_5k"),
            "files": {
                'jan': 'flow_5k_jan23.csv', 'feb': 'flow_5k_feb23.csv',
                'mar': 'flow_5k_mar23.csv', 'apr': 'flow_5k_apr23.csv', 'may': 'flow_5k_may23.csv',
                'jun': 'flow_5k_jun23.csv', 'jul': 'flow_5k_jul23.csv', 'aug': 'flow_5k_aug23.csv',
                'sep': 'flow_5k_sep23.csv', 'oct': 'flow_5k_oct23.csv', 'nov': 'flow_5k_nov23.csv',
                'dec': 'flow_5k_dec23.csv'
            },
            "has_pv": True,
            "has_battery": True
        },
        "8kWh": {
            "flow_dir": os.path.join(script_dir, "flows_8k"),
            "files": {
                'jan': 'flow_8k_jan23.csv', 'feb': 'flow_8k_feb23.csv',
                'mar': 'flow_8k_mar23.csv', 'apr': 'flow_8k_apr23.csv', 'may': 'flow_8k_may23.csv',
                'jun': 'flow_8k_jun23.csv', 'jul': 'flow_8k_jul23.csv', 'aug': 'flow_8k_aug23.csv',
                'sep': 'flow_8k_sep23.csv', 'oct': 'flow_8k_oct23.csv', 'nov': 'flow_8k_nov23.csv',
                'dec': 'flow_8k_dec23.csv'
            },
            "has_pv": True,
            "has_battery": True
        },
        "12kWh": {
            "flow_dir": os.path.join(script_dir, "flows_12k"),
            "files": {
                'jan': 'flow_12k_jan23.csv', 'feb': 'flow_12k_feb23.csv',
                'mar': 'flow_12k_mar23.csv', 'apr': 'flow_12k_apr23.csv', 'may': 'flow_12k_may23.csv',
                'jun': 'flow_12k_jun23.csv', 'jul': 'flow_12k_jul23.csv', 'aug': 'flow_12k_aug23.csv',
                'sep': 'flow_12k_sep23.csv', 'oct': 'flow_12k_oct23.csv', 'nov': 'flow_12k_nov23.csv',
                'dec': 'flow_12k_dec23.csv'
            },
            "has_pv": True,
            "has_battery": True
        },
        "15kWh": {
            "flow_dir": os.path.join(script_dir, "flows_15k"),
            "files": {
                'jan': 'flow_15k_jan23.csv', 'feb': 'flow_15k_feb23.csv',
                'mar': 'flow_15k_mar23.csv', 'apr': 'flow_15k_apr23.csv', 'may': 'flow_15k_may23.csv',
                'jun': 'flow_15k_jun23.csv', 'jul': 'flow_15k_jul23.csv', 'aug': 'flow_15k_aug23.csv',
                'sep': 'flow_15k_sep23.csv', 'oct': 'flow_15k_oct23.csv', 'nov': 'flow_15k_nov23.csv',
                'dec': 'flow_15k_dec23.csv'
            },
            "has_pv": True,
            "has_battery": True
        },
        "20kWh": {
            "flow_dir": os.path.join(script_dir, "flows_20k"),
            "files": {
                'jan': 'flow_20k_jan23.csv', 'feb': 'flow_20k_feb23.csv',
                'mar': 'flow_20k_mar23.csv', 'apr': 'flow_20k_apr23.csv', 'may': 'flow_20k_may23.csv',
                'jun': 'flow_20k_jun23.csv', 'jul': 'flow_20k_jul23.csv', 'aug': 'flow_20k_aug23.csv',
                'sep': 'flow_20k_sep23.csv', 'oct': 'flow_20k_oct23.csv', 'nov': 'flow_20k_nov23.csv',
                'dec': 'flow_20k_dec23.csv'
            },
            "has_pv": True,
            "has_battery": True
        },
        "26kWh": {
            "flow_dir": os.path.join(script_dir, "flows_26k"),
            "files": {
                'jan': 'flow_26k_jan23.csv', 'feb': 'flow_26k_feb23.csv',
                'mar': 'flow_26k_mar23.csv', 'apr': 'flow_26k_apr23.csv', 'may': 'flow_26k_may23.csv',
                'jun': 'flow_26k_jun23.csv', 'jul': 'flow_26k_jul23.csv', 'aug': 'flow_26k_aug23.csv',
                'sep': 'flow_26k_sep23.csv', 'oct': 'flow_26k_oct23.csv', 'nov': 'flow_26k_nov23.csv',
                'dec': 'flow_26k_dec23.csv'
            },
            "has_pv": True,
            "has_battery": True
        },
        "50kWh": {
            "flow_dir": os.path.join(script_dir, "flows_50k"),
            "files": {
                'jan': 'flow_50k_jan23.csv', 'feb': 'flow_50k_feb23.csv',
                'mar': 'flow_50k_mar23.csv', 'apr': 'flow_50k_apr23.csv', 'may': 'flow_50k_may23.csv',
                'jun': 'flow_50k_jun23.csv', 'jul': 'flow_50k_jul23.csv', 'aug': 'flow_50k_aug23.csv',
                'sep': 'flow_50k_sep23.csv', 'oct': 'flow_50k_oct23.csv', 'nov': 'flow_50k_nov23.csv',
                'dec': 'flow_50k_dec23.csv'
            },
            "has_pv": True,
            "has_battery": True
        }
    }

    all_raw_monthly_data = [] # To collect all monthly data from all scenarios
    all_raw_yearly_data = [] # To collect all yearly data from all scenarios
    
    # Store monthly ordering for consistent output
    month_order = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']

    for scenario_identifier, config in scenarios_config.items():
        monthly_df, yearly_df_single_row = calculate_monthly_co2_emissions(scenario_identifier, config)

        if monthly_df is not None:
            all_raw_monthly_data.append(monthly_df)
        
        if yearly_df_single_row is not None:
            all_raw_yearly_data.append(yearly_df_single_row)

    # --- Consolidated Monthly Data to Wide Format ---
    if all_raw_monthly_data:
        combined_monthly_df = pd.concat(all_raw_monthly_data)
        
        # Monthly CO2 from PV Production
        monthly_pv_co2_wide = combined_monthly_df.pivot_table(index='Month', columns='Scenario', values='CO2 from PV Production (gCO2eq)')
        monthly_pv_co2_wide = monthly_pv_co2_wide.reindex(month_order) # Ensure consistent month order
        monthly_pv_co2_wide.index.name = "Month"
        monthly_pv_co2_wide.to_csv(os.path.join(output_dir, "monthly_co2_pv_all_scenarios_wide.csv"), float_format="%.2f")

        # Monthly CO2 from Battery Discharge
        monthly_battery_co2_wide = combined_monthly_df.pivot_table(index='Month', columns='Scenario', values='CO2 from Battery Discharge (gCO2eq)')
        monthly_battery_co2_wide = monthly_battery_co2_wide.reindex(month_order) # Ensure consistent month order
        monthly_battery_co2_wide.index.name = "Month"
        monthly_battery_co2_wide.to_csv(os.path.join(output_dir, "monthly_co2_battery_all_scenarios_wide.csv"), float_format="%.2f")

        # Monthly CO2 from Grid Import
        monthly_grid_co2_wide = combined_monthly_df.pivot_table(index='Month', columns='Scenario', values='CO2 from Grid Import (gCO2eq)')
        monthly_grid_co2_wide = monthly_grid_co2_wide.reindex(month_order) # Ensure consistent month order
        monthly_grid_co2_wide.index.name = "Month"
        monthly_grid_co2_wide.to_csv(os.path.join(output_dir, "monthly_co2_grid_all_scenarios_wide.csv"), float_format="%.2f")

        # Optional: Monthly Total Operational CO2 (if you want this in wide format too)
        monthly_total_co2_wide = combined_monthly_df.pivot_table(index='Month', columns='Scenario', values='Total CO2 Emissions (gCO2eq)')
        monthly_total_co2_wide = monthly_total_co2_wide.reindex(month_order) # Ensure consistent month order
        monthly_total_co2_wide.index.name = "Month"
        monthly_total_co2_wide.to_csv(os.path.join(output_dir, "monthly_total_operational_co2_all_scenarios_wide.csv"), float_format="%.2f")

    # --- Consolidated Annual Data (already in a somewhat wide format, just combine and save) ---
    if all_raw_yearly_data:
        df_yearly_all_scenarios = pd.concat(all_raw_yearly_data)
        df_yearly_all_scenarios = df_yearly_all_scenarios.set_index("Scenario") # Set scenario as index for clarity

        # Annual CO2 from PV Production
        df_yearly_all_scenarios[["Yearly CO2 from PV Production (gCO2eq)"]].T.to_csv(
            os.path.join(output_dir, "annual_co2_pv_all_scenarios.csv"), float_format="%.2f"
        )
        # Annual CO2 from Battery Discharge
        df_yearly_all_scenarios[["Yearly CO2 from Battery Discharge (gCO2eq)"]].T.to_csv(
            os.path.join(output_dir, "annual_co2_battery_all_scenarios.csv"), float_format="%.2f"
        )
        # Annual CO2 from Grid Import
        df_yearly_all_scenarios[["Yearly CO2 from Grid Import (gCO2eq)"]].T.to_csv(
            os.path.join(output_dir, "annual_co2_grid_all_scenarios.csv"), float_format="%.2f"
        )
        # Annual Total Operational CO2
        df_yearly_all_scenarios[["Total Yearly CO2 Emissions (gCO2eq)"]].T.to_csv(
            os.path.join(output_dir, "annual_total_operational_co2_all_scenarios.csv"), float_format="%.2f"
        )

        # Battery manufacturing vs operational CO2 table
        manufacturing_data = []
        for scenario in df_yearly_all_scenarios.index:
            mfg_co2 = BATTERY_MANUFACTURING_CO2_G.get(scenario, 0)
            yearly_discharge_co2 = df_yearly_all_scenarios.loc[scenario, "Yearly CO2 from Battery Discharge (gCO2eq)"]
            total_operational_co2 = df_yearly_all_scenarios.loc[scenario, "Total Yearly CO2 Emissions (gCO2eq)"]
            manufacturing_data.append({
                "Scenario": scenario,
                "CO2 from Battery Manufacturing (gCO2eq)": mfg_co2,
                "CO2 from Battery Discharge (gCO2eq)": yearly_discharge_co2,
                "Total Yearly Operational CO2 (gCO2eq)": total_operational_co2
            })
        pd.DataFrame(manufacturing_data).to_csv(
            os.path.join(output_dir, "battery_co2_manufacturing_vs_usage.csv"), index=False, float_format="%.2f"
        )