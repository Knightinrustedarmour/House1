import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import re

# Define CO2 emission factors in gCO2eq/kWh
CO2_EMISSION_FACTORS = {
    "PV_production": 22,
    "Battery_discharge": 53,
    "Grid_import": 471, 
}

# Estimated CO2 footprint from battery manufacturing in gCO2eq
# Source: Values provided by user (converted from kgCO2eq to gCO2eq)
BATTERY_MANUFACTURING_CO2_G = {
    "5kWh": 5 * 109 * 50,      # 5 kWh capacity * 109 kg/kWh * 1000 g/kg / 20 per year lifespan
    "8kWh": 8 * 109 * 50,
    "12kWh": 12 * 109 * 50,
    "15kWh": 15 * 109 * 50,
    "20kWh": 20 * 109 * 50,
    "26kWh": 26 * 109 * 50,
    "50kWh": 50 * 109 * 50,
}

# Define column paths for flows
FLOW_COLUMN_PATHS = {
    "PV_production": (
        "SolphLabel(location='House1', mtress_component='PV', solph_node='connection')",
        "SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='distribution')"
    ),
    "Battery_discharge": (
        "SolphLabel(location='House1', mtress_component='storage1', solph_node='Battery_Storage')",
        "SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='distribution')"
    ),
    "Grid_import": (
        "SolphLabel(location='House1', mtress_component='ElectricityGridConnection', solph_node='grid_import')",
        "SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='distribution')"
    ),
    "Demand": (
        "SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='distribution')",
        "SolphLabel(location='House1', mtress_component='demand', solph_node='input')"
    )
}

def _get_simplified_solph_label_string(solph_label_str):
    """Converts a string representation of SolphLabel to its internal tuple string."""
    match = re.search(r"location='([^']+)', mtress_component='([^']+)', solph_node='([^']+)'", solph_label_str)
    if match:
        location, component, node = match.groups()
        return repr((location, component, node))
    return None

def get_column_data(df, flow_name, scenario_config):
    """Gets column data using two potential naming conventions."""
    expected_col_path_solphlabel = FLOW_COLUMN_PATHS[flow_name]
    
    if expected_col_path_solphlabel in df.columns:
        return df[expected_col_path_solphlabel]

    simplified_col_path = (
        _get_simplified_solph_label_string(expected_col_path_solphlabel[0]),
        _get_simplified_solph_label_string(expected_col_path_solphlabel[1])
    )
    if simplified_col_path[0] is not None and simplified_col_path[1] is not None and simplified_col_path in df.columns:
        return df[simplified_col_path]

    if (flow_name == "PV_production" and not scenario_config["has_pv"]) or \
       (flow_name == "Battery_discharge" and not scenario_config["has_battery"]):
        return pd.Series(0.0, index=df.index)
    
    print(f"Warning: Column for '{flow_name}' not found for current file.")
    return pd.Series(0.0, index=df.index)

def calculate_monthly_co2_emissions(scenario_identifier, scenario_config):
    """Calculates monthly and yearly CO2 emissions for a given scenario."""
    monthly_data = []
    for month_name, filename in scenario_config["files"].items():
        filepath = os.path.join(scenario_config["flow_dir"], filename)
        if not os.path.exists(filepath):
            print(f"Error: File not found for {scenario_identifier} - {month_name}: {filepath}. Skipping month.")
            continue
        try:
            results = pd.read_csv(filepath, header=[0, 1], index_col=0)
            results.index = pd.to_datetime(results.index, utc=True)

            pv_production = get_column_data(results, "PV_production", scenario_config)
            grid_import = get_column_data(results, "Grid_import", scenario_config)
            battery_discharge = get_column_data(results, "Battery_discharge", scenario_config)
            demand = get_column_data(results, "Demand", scenario_config)

            total_pv_kwh = pv_production.sum() / 1000
            total_grid_import_kwh = grid_import.sum() / 1000
            total_battery_discharge_kwh = battery_discharge.sum() / 1000
            total_demand_kwh = demand.sum() / 1000

            co2_pv = total_pv_kwh * CO2_EMISSION_FACTORS["PV_production"]
            co2_grid_import = total_grid_import_kwh * CO2_EMISSION_FACTORS["Grid_import"]
            co2_battery_discharge = total_battery_discharge_kwh * CO2_EMISSION_FACTORS["Battery_discharge"]

            total_co2_emissions_g = co2_pv + co2_grid_import + co2_battery_discharge

            monthly_data.append({
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

        except Exception as e:
            print(f"An error occurred while processing {filepath}: {e}. Skipping month.")
            continue

    if not monthly_data:
        print(f"No data processed for scenario {scenario_identifier}.")
        return None, None

    df_monthly = pd.DataFrame(monthly_data).set_index("Month")
    
    yearly_total_demand = df_monthly["Total Demand (kWh)"].sum()
    yearly_total_pv_production = df_monthly["PV Production (kWh)"].sum()
    yearly_total_grid_import = df_monthly["Grid Import (kWh)"].sum()
    yearly_total_battery_discharge = df_monthly["Battery Discharge (kWh)"].sum()
    
    yearly_co2_pv = df_monthly["CO2 from PV Production (gCO2eq)"].sum()
    yearly_co2_grid_import = df_monthly["CO2 from Grid Import (gCO2eq)"].sum()
    yearly_co2_battery_discharge = df_monthly["CO2 from Battery Discharge (gCO2eq)"].sum()

    yearly_total_co2_emissions = yearly_co2_pv + yearly_co2_grid_import + yearly_co2_battery_discharge

    yearly_summary = pd.DataFrame({
        "Metric": [
            "Total Yearly Demand (kWh)",
            "Total Yearly PV Production (kWh)",
            "Total Yearly Grid Import (kWh)",
            "Total Yearly Battery Discharge (kWh)",
            "Yearly CO2 from PV Production (gCO2eq)",
            "Yearly CO2 from Grid Import (gCO2eq)",
            "Yearly CO2 from Battery Discharge (gCO2eq)",
            "Total Yearly CO2 Emissions (gCO2eq)"
        ],
        "Value": [
            yearly_total_demand,
            yearly_total_pv_production,
            yearly_total_grid_import,
            yearly_total_battery_discharge,
            yearly_co2_pv,
            yearly_co2_grid_import,
            yearly_co2_battery_discharge,
            yearly_total_co2_emissions
        ]
    }).set_index("Metric")

    return df_monthly, yearly_summary

# Scenario configurations
script_dir = os.path.dirname(os.path.abspath(__file__))
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

if __name__ == "__main__":
    output_dir = os.path.join(script_dir, "output","carbon_footprint_analysis1")
    os.makedirs(output_dir, exist_ok=True)

    all_monthly_dfs = {}
    all_yearly_dfs = {}

    print("Starting CO2 Emissions Analysis...")

    for scenario_identifier, config in scenarios_config.items():
        print(f"\nProcessing scenario: {scenario_identifier}")
        monthly_df, yearly_df = calculate_monthly_co2_emissions(scenario_identifier, config)

        if monthly_df is not None:
            all_monthly_dfs[scenario_identifier] = monthly_df
            all_yearly_dfs[scenario_identifier] = yearly_df

            # Save monthly and yearly summaries to CSV
            monthly_output_path = os.path.join(output_dir, f"monthly_co2_summary_2023_{scenario_identifier}.csv")
            yearly_output_path = os.path.join(output_dir, f"yearly_co2_summary_2023_{scenario_identifier}.csv")
            
            monthly_df.to_csv(monthly_output_path, float_format="%.2f")
            yearly_df.to_csv(yearly_output_path, float_format="%.2f")
            print(f"Saved monthly CO2 summary to: {monthly_output_path}")
            print(f"Saved yearly CO2 summary to: {yearly_output_path}")
        else:
            print(f"Skipping saving results for {scenario_identifier} due to processing errors.")

    # Generate comparative plots for specific monthly CO2 metrics only
    print("\nGenerating selected monthly comparative plots...")

    plot_metrics = [
        "Total CO2 Emissions (gCO2eq)",
        "CO2 from PV Production (gCO2eq)",
        "CO2 from Grid Import (gCO2eq)",
        "CO2 from Battery Discharge (gCO2eq)"
    ]

    for metric in plot_metrics:
        plt.figure(figsize=(12, 6))
        ax = plt.gca()
        plotted_any_data = False
        
        for scenario_identifier, df_monthly in all_monthly_dfs.items():
            if metric in df_monthly.columns:
                plt.plot(df_monthly.index, df_monthly[metric], label=scenario_identifier)
                plotted_any_data = True
            else:
                print(f"Warning: Metric '{metric}' not found for scenario '{scenario_identifier}' in monthly data. Skipping plot for this scenario.")

        if plotted_any_data:
            plt.title(f'Monthly {metric} Comparison')
            plt.xlabel('Month')
            plt.ylabel(metric)
            plt.xticks(rotation=45)
            plt.legend()
            plt.grid(True)
            plt.tight_layout()

            if metric == "CO2 from Battery Discharge (gCO2eq)":
                for bat_size_str, co2_val in BATTERY_MANUFACTURING_CO2_G.items():
                    if bat_size_str in all_monthly_dfs: # Only plot if a scenario for this battery size exists
                        ax.axhline(
                            y=co2_val, 
                            color='r', 
                            linestyle='--', 
                            label=f'Mfg. CO2 ({bat_size_str})',
                            alpha=0.7
                        )
                plt.legend()


            plot_filename = os.path.join(output_dir, f"monthly_{metric.replace(' ', '_').replace('(', '').replace(')', '')}_comparison.png")
            plt.savefig(plot_filename)
            print(f"Saved plot: {plot_filename}")
        else:
            print(f"No data to plot for '{metric}' across any scenarios. Skipping plot.")
        plt.close()

    # --- Annual CO2 Impact Bar Graph (Stacked) ---
    if all_yearly_dfs:
        scenario_names = list(all_yearly_dfs.keys())
        operational_co2 = []
        manufacturing_co2 = []

        for scenario in scenario_names:
            yearly_df = all_yearly_dfs[scenario]
            # Ensure we're getting the 'Total Yearly CO2 Emissions (gCO2eq)' which is the operational CO2
            op_co2 = yearly_df.loc["Total Yearly CO2 Emissions (gCO2eq)", "Value"]
            operational_co2.append(op_co2)

            mfg_co2 = 0
            if scenario in BATTERY_MANUFACTURING_CO2_G:
                mfg_co2 = BATTERY_MANUFACTURING_CO2_G[scenario]
            manufacturing_co2.append(mfg_co2)
        
        operational_co2 = np.array(operational_co2)
        manufacturing_co2 = np.array(manufacturing_co2)

        plt.figure(figsize=(14, 8))
        bar_width = 0.6
        indices = np.arange(len(scenario_names))

        p1 = plt.bar(indices, manufacturing_co2, bar_width, label='Manufacturing CO2', color='lightcoral')
        p2 = plt.bar(indices, operational_co2, bar_width, bottom=manufacturing_co2, label='Operational CO2 (Annual)', color='skyblue')

        plt.xlabel('Scenario')
        plt.ylabel('CO2 Emissions (gCO2eq)')
        plt.title('Annual CO2 Impact by Scenario (Manufacturing + Operational)')
        plt.xticks(indices, scenario_names, rotation=45, ha='right')
        plt.legend()
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        
        # Annotate stacked bars
        for i in indices:
            total_height = manufacturing_co2[i] + operational_co2[i]
            if manufacturing_co2[i] > 0:
                plt.text(i, manufacturing_co2[i] / 2, f'{manufacturing_co2[i]:.0f}', ha='center', va='center', color='black', fontsize=9)
            if operational_co2[i] > 0:
                plt.text(i, manufacturing_co2[i] + operational_co2[i] / 2, f'{operational_co2[i]:.0f}', ha='center', va='center', color='black', fontsize=9)
            if total_height > 0:
                plt.text(i, total_height + 0.02 * plt.ylim()[1], f'{total_height:.0f}', ha='center', va='bottom', color='black', fontsize=9, fontweight='bold')


        stacked_bar_filename = os.path.join(output_dir, "annual_co2_impact_stacked_bar.png")
        plt.savefig(stacked_bar_filename)
        print(f"Saved plot: {stacked_bar_filename}")
        plt.close()
    else:
        print("No yearly data available for stacked CO2 bar chart.")

    # --- NEW: Annual CO2 Impact Bar Graph (Side-by-Side) ---
    if all_yearly_dfs:
        scenario_names = list(all_yearly_dfs.keys())
        operational_co2 = []
        manufacturing_co2 = []

        for scenario in scenario_names:
            yearly_df = all_yearly_dfs[scenario]
            # Ensure we're getting the 'Total Yearly CO2 Emissions (gCO2eq)' which is the operational CO2
            op_co2 = yearly_df.loc["Total Yearly CO2 Emissions (gCO2eq)", "Value"]
            operational_co2.append(op_co2)

            mfg_co2 = 0
            if scenario in BATTERY_MANUFACTURING_CO2_G:
                mfg_co2 = BATTERY_MANUFACTURING_CO2_G[scenario]
            manufacturing_co2.append(mfg_co2)
        
        operational_co2 = np.array(operational_co2)
        manufacturing_co2 = np.array(manufacturing_co2)

        plt.figure(figsize=(14, 8))
        bar_width = 0.35
        indices = np.arange(len(scenario_names))

        rects1 = plt.bar(indices - bar_width/2, manufacturing_co2, bar_width, label='Manufacturing CO2', color='lightcoral')
        rects2 = plt.bar(indices + bar_width/2, operational_co2, bar_width, label='Operational CO2 (Annual)', color='skyblue')

        plt.xlabel('Scenario')
        plt.ylabel('CO2 Emissions (gCO2eq)')
        plt.title('Annual CO2 Impact by Scenario (Manufacturing vs. Operational)')
        plt.xticks(indices, scenario_names, rotation=45, ha='right')
        plt.legend()
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        
        # Annotate side-by-side bars
        def autolabel(rects):
            for rect in rects:
                height = rect.get_height()
                if height > 0:
                    plt.text(rect.get_x() + rect.get_width() / 2, height + 0.01 * plt.ylim()[1],
                             f'{height:.0f}', ha='center', va='bottom', fontsize=8)

        autolabel(rects1)
        autolabel(rects2)

        side_by_side_bar_filename = os.path.join(output_dir, "annual_co2_impact_side_by_side_bar.png")
        plt.savefig(side_by_side_bar_filename)
        print(f"Saved plot: {side_by_side_bar_filename}")
        plt.close()
    else:
        print("No yearly data available for side-by-side CO2 bar chart.")


    # --- CO2 Break-even Time Calculation ---
    print("\nCalculating CO2 Break-even Times...")
    break_even_data_for_plot = {} # Store break-even times for plotting
    co2_breakeven_energy_values = {} # Store break-even energy values

    # Reference scenario: NoPV
    if "NoPV" in all_yearly_dfs:
        yearly_co2_nopv = all_yearly_dfs["NoPV"].loc["Total Yearly CO2 Emissions (gCO2eq)", "Value"]
        
        for scenario_identifier, yearly_df in all_yearly_dfs.items():
            if scenario_identifier == "NoPV":
                continue 

            yearly_co2_scenario_operational = yearly_df.loc["Total Yearly CO2 Emissions (gCO2eq)", "Value"]
            
            scenario_mfg_co2 = BATTERY_MANUFACTURING_CO2_G.get(scenario_identifier, 0)
            
            annual_operational_co2_savings_vs_nopv = yearly_co2_nopv - yearly_co2_scenario_operational

            if annual_operational_co2_savings_vs_nopv > 0 and (scenario_mfg_co2 > 0 or scenario_identifier == "PV_NoBattery"):
                # For PV_NoBattery, mfg_co2 is 0, but we still want to calculate savings vs NoPV
                break_even_years = scenario_mfg_co2 / annual_operational_co2_savings_vs_nopv if annual_operational_co2_savings_vs_nopv > 0 else np.nan
                break_even_data_for_plot.setdefault(scenario_identifier, {})['vs_NoPV'] = break_even_years
                # Calculate break-even energy in terms of grid import
                equivalent_grid_energy_kwh = scenario_mfg_co2 / CO2_EMISSION_FACTORS["Grid_import"] if CO2_EMISSION_FACTORS["Grid_import"] > 0 else np.nan
                co2_breakeven_energy_values.setdefault(scenario_identifier, {})['vs_NoPV (kWh Grid)'] = equivalent_grid_energy_kwh
            else:
                if scenario_identifier in BATTERY_MANUFACTURING_CO2_G or scenario_identifier == "PV_NoBattery":
                    break_even_data_for_plot.setdefault(scenario_identifier, {})['vs_NoPV'] = np.nan 
                    co2_breakeven_energy_values.setdefault(scenario_identifier, {})['vs_NoPV (kWh Grid)'] = np.nan
    else:
        print("'NoPV' scenario data not found, cannot calculate break-even times relative to it.")

    # Reference scenario: PV_NoBattery (for battery scenarios only)
    if "PV_NoBattery" in all_yearly_dfs:
        yearly_co2_pv_nobattery = all_yearly_dfs["PV_NoBattery"].loc["Total Yearly CO2 Emissions (gCO2eq)", "Value"]
        
        for scenario_identifier, yearly_df in all_yearly_dfs.items():
            # Only consider scenarios with batteries for comparison against PV_NoBattery
            if scenario_identifier not in BATTERY_MANUFACTURING_CO2_G:
                continue 

            yearly_co2_scenario_operational = yearly_df.loc["Total Yearly CO2 Emissions (gCO2eq)", "Value"]
            
            annual_operational_co2_savings_vs_pv_nobattery = yearly_co2_pv_nobattery - yearly_co2_scenario_operational

            if annual_operational_co2_savings_vs_pv_nobattery > 0:
                mfg_co2 = BATTERY_MANUFACTURING_CO2_G[scenario_identifier]
                break_even_years = mfg_co2 / annual_operational_co2_savings_vs_pv_nobattery
                break_even_data_for_plot.setdefault(scenario_identifier, {})['vs_PV_NoBattery'] = break_even_years
                # Calculate break-even energy in terms of grid import
                equivalent_grid_energy_kwh = mfg_co2 / CO2_EMISSION_FACTORS["Grid_import"] if CO2_EMISSION_FACTORS["Grid_import"] > 0 else np.nan
                co2_breakeven_energy_values.setdefault(scenario_identifier, {})['vs_PV_NoBattery (kWh Grid)'] = equivalent_grid_energy_kwh
            else:
                break_even_data_for_plot.setdefault(scenario_identifier, {})['vs_PV_NoBattery'] = np.nan
                co2_breakeven_energy_values.setdefault(scenario_identifier, {})['vs_PV_NoBattery (kWh Grid)'] = np.nan
    else:
        print("'PV_NoBattery' scenario data not found, cannot calculate break-even times relative to it for battery scenarios.")

    # Display break-even results in text format
    if break_even_data_for_plot:
        print("\n--- CO2 Break-even Time Results ---")
        for scenario, comparisons in break_even_data_for_plot.items():
            vs_nopv_str = f"{comparisons.get('vs_NoPV', np.nan):.2f} years" if not np.isnan(comparisons.get('vs_NoPV', np.nan)) else "N/A (No savings or initial CO2)"
            vs_pv_nobat_str = f"{comparisons.get('vs_PV_NoBattery', np.nan):.2f} years" if not np.isnan(comparisons.get('vs_PV_NoBattery', np.nan)) else "N/A (No savings)"
            print(f"CO2 Break-even for '{scenario}':")
            print(f"   vs 'NoPV': {vs_nopv_str}")
            print(f"   vs 'PV_NoBattery': {vs_pv_nobat_str}")
    else:
        print("No CO2 break-even time results to display.")

    # Display CO2 Break-even Energy Values in terms of grid energy
    if co2_breakeven_energy_values:
        print("\n--- CO2 Break-even Energy Values (in kWh Grid Equivalent) ---")
        df_breakeven_energy = pd.DataFrame.from_dict(co2_breakeven_energy_values, orient='index')
        df_breakeven_energy.index.name = 'Scenario'
        
        # Add the manufacturing CO2 in gCO2eq for context
        mfg_co2_for_table = {s: BATTERY_MANUFACTURING_CO2_G.get(s, 0) for s in df_breakeven_energy.index}
        df_breakeven_energy.insert(0, "Battery Manufacturing CO2 (gCO2eq)", pd.Series(mfg_co2_for_table))
        
        print(df_breakeven_energy.to_string(float_format="%.2f"))
        
        # Save to CSV
        breakeven_energy_csv_path = os.path.join(output_dir, "co2_breakeven_energy_grid_equivalent.csv")
        df_breakeven_energy.to_csv(breakeven_energy_csv_path, float_format="%.2f")
        print(f"Saved CO2 break-even energy values to: {breakeven_energy_csv_path}")
    else:
        print("No CO2 break-even energy values to display.")


    # --- New: CO2 Break-even Time Bar Graph ---
    if break_even_data_for_plot:
        df_break_even = pd.DataFrame.from_dict(break_even_data_for_plot, orient='index')
        df_break_even.index.name = 'Scenario'
        df_break_even.columns.name = 'Comparison Basis'

        # Filter out scenarios that are not battery sizes for the graph, if any non-battery scenarios made it here.
        # This graph is specifically for battery break-even.
        battery_scenarios_for_plot = [s for s in df_break_even.index if s in BATTERY_MANUFACTURING_CO2_G]
        df_break_even_filtered = df_break_even.loc[battery_scenarios_for_plot]


        if not df_break_even_filtered.empty:
            plt.figure(figsize=(12, 7))
            ax = df_break_even_filtered.plot(kind='bar', ax=plt.gca(), width=0.8)
            plt.title('CO2 Break-even Time for Battery Scenarios')
            plt.xlabel('Battery Scenario')
            plt.ylabel('Break-even Time (Years)')
            plt.xticks(rotation=45, ha='right')
            plt.legend(title='Compared to')
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            plt.tight_layout()

            # Annotate bars
            for container in ax.containers:
                for j, rect in enumerate(container.patches):
                    height = rect.get_height()
                    if not np.isnan(height):
                        ax.annotate(f'{height:.2f}',
                                    xy=(rect.get_x() + rect.get_width() / 2, height),
                                    xytext=(0, 3),  # 3 points vertical offset
                                    textcoords="offset points",
                                    ha='center', va='bottom', fontsize=8)

            break_even_plot_filename = os.path.join(output_dir, "co2_break_even_time_bar_graph.png")
            plt.savefig(break_even_plot_filename)
            print(f"Saved plot: {break_even_plot_filename}")
            plt.close()
        else:
            print("No valid break-even data for battery scenarios to plot.")
    else:
        print("No CO2 break-even data to plot.")


    print("\nCO2 Emissions Analysis Complete.")
    print("Check the 'output/carbon_footprint_analysis' folder for summary CSVs and plots.")

    # Generate the distinct table for manufacturing and usage CO2
    battery_co2_data = []
    for scenario_identifier, config in scenarios_config.items():
        manufacturing_co2 = BATTERY_MANUFACTURING_CO2_G.get(scenario_identifier, 0)
        
        # Get yearly operational CO2 from battery discharge AND total operational CO2
        yearly_operational_co2_battery_discharge = 0
        yearly_total_operational_co2 = 0 # This will store the "Total Yearly CO2 Emissions (gCO2eq)"

        if scenario_identifier in all_yearly_dfs:
            yearly_df = all_yearly_dfs[scenario_identifier]
            if "Yearly CO2 from Battery Discharge (gCO2eq)" in yearly_df.index:
                yearly_operational_co2_battery_discharge = yearly_df.loc["Yearly CO2 from Battery Discharge (gCO2eq)", "Value"]
            if "Total Yearly CO2 Emissions (gCO2eq)" in yearly_df.index:
                yearly_total_operational_co2 = yearly_df.loc["Total Yearly CO2 Emissions (gCO2eq)", "Value"]
        
        battery_co2_data.append({
            "Scenario": scenario_identifier,
            "CO2 from Battery Manufacturing (gCO2eq)": manufacturing_co2,
            "CO2 from Battery Discharge (gCO2eq)": yearly_operational_co2_battery_discharge, # CO2 directly from battery usage
            "Total Yearly Operational CO2 (gCO2eq)": yearly_total_operational_co2 # Total operational CO2 for the scenario
        })

    df_battery_co2 = pd.DataFrame(battery_co2_data)

    # Save the battery CO2 table
    battery_co2_table_path = os.path.join(output_dir, "battery_co2_manufacturing_vs_usage.csv")
    df_battery_co2.to_csv(battery_co2_table_path, index=False, float_format="%.2f")
    print(f"\nSaved battery CO2 manufacturing vs. usage summary to: {battery_co2_table_path}")

    # Create a new plot of total operational CO2 output alone (previously named "operational CO2 output")
    if all_yearly_dfs:
        operational_co2_data = []
        for scenario_identifier, yearly_df in all_yearly_dfs.items():
            # Get the TOTAL operational CO2, which includes PV, Grid, and Battery Discharge
            op_co2 = yearly_df.loc["Total Yearly CO2 Emissions (gCO2eq)", "Value"]
            operational_co2_data.append({"Scenario": scenario_identifier, "Total Yearly Operational CO2 (gCO2eq)": op_co2})
        
        df_operational_co2 = pd.DataFrame(operational_co2_data).set_index("Scenario")
        
        plt.figure(figsize=(12, 7))
        ax = df_operational_co2.plot(kind='bar', ax=plt.gca(), width=0.7, color='lightgreen')
        plt.title('Total Yearly Operational CO2 Emissions by Scenario')
        plt.xlabel('Scenario')
        plt.ylabel('Total Yearly Operational CO2 (gCO2eq)')
        plt.xticks(rotation=45, ha='right')
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        
        # Annotate bars
        for container in ax.containers:
            for rect in container.patches:
                height = rect.get_height()
                if height > 0:
                    ax.annotate(f'{height:.0f}',
                                xy=(rect.get_x() + rect.get_width() / 2, height),
                                xytext=(0, 3),  # 3 points vertical offset
                                textcoords="offset points",
                                ha='center', va='bottom', fontsize=9)

        operational_co2_plot_filename = os.path.join(output_dir, "total_yearly_operational_co2_bar_graph.png")
        plt.savefig(operational_co2_plot_filename)
        print(f"Saved plot: {operational_co2_plot_filename}")
        plt.close()
    else:
        print("No yearly data available to plot total yearly operational CO2.")