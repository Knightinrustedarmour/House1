import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def soc(charge_series, discharge_series, index, 
        nominal_capacity_wh=5000, charge_eff=0.96, discharge_eff=0.96, 
        loss_rate=0.0005, initial_soc_wh=None, soc_min_frac=0.1):
    """
    Calculates the State of Charge (SoC) over time.
    """
    if initial_soc_wh is None:
        initial_soc_wh = 0.5 * nominal_capacity_wh

    soc_values = [initial_soc_wh]
    soc_min = soc_min_frac * nominal_capacity_wh

    for i in range(1, len(index)):
        dt_hours = (index[i] - index[i - 1]).total_seconds() / 3600
        last_soc = soc_values[-1]

        available_capacity = nominal_capacity_wh - last_soc
        usable_energy = last_soc - soc_min

        # The input data is in Wh-min, convert to Wh.
        charge_energy = min(charge_series.iloc[i] * charge_eff, available_capacity)
        discharge_energy = min(discharge_series.iloc[i] / discharge_eff, usable_energy)

        effective_soc = last_soc - (loss_rate * nominal_capacity_wh * dt_hours)
        new_soc = effective_soc + charge_energy - discharge_energy

        soc_values.append(new_soc)

    return [val / nominal_capacity_wh * 100 for val in soc_values]

def generate_monthly_soc_dsp(scenario_identifier, scenario_config, nominal_capacities):
    """
    Generates monthly density scatter plots for the battery's State of Charge.
    """
    
    ALL_FLOWS = {
        "Battery_Charge": [
            ("SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='distribution')", "SolphLabel(location='House1', mtress_component='storage1', solph_node='Battery_Storage')"),
            ("('House1', 'ElectricityCarrier', 'distribution')", "('House1', 'storage1', 'Battery_Storage')")
        ],
        "Battery_Discharge": [
            ("SolphLabel(location='House1', mtress_component='storage1', solph_node='Battery_Storage')", "SolphLabel(location='House1', mtress_component='ElectricityCarrier', solph_node='distribution')"),
            ("('House1', 'storage1', 'Battery_Storage')", "('House1', 'ElectricityCarrier', 'distribution')")
        ]
    }

    nominal_capacity = nominal_capacities.get(scenario_identifier)
    if nominal_capacity is None:
        print(f"No nominal capacity found for {scenario_identifier}. Skipping SoC plots.")
        return

    output_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "output", 
        "soc_dsps",
        scenario_identifier
    )
    os.makedirs(output_dir, exist_ok=True)

    for month, filename in scenario_config["files"].items():
        filepath = os.path.join(scenario_config["flow_dir"], filename)
        if not os.path.exists(filepath):
            print(f"File not found: {filepath}. Skipping.")
            continue
        
        try:
            df = pd.read_csv(filepath, header=[0, 1], index_col=0)
            df.index = pd.to_datetime(df.index, errors='coerce')
            
            if df.index.isna().all():
                print(f"Skipping {filepath}: All timestamps are invalid. File may be empty or corrupted.")
                continue

            charge_series = pd.Series(0.0, index=df.index)
            discharge_series = pd.Series(0.0, index=df.index)
            
            for solph_label_tuple in ALL_FLOWS["Battery_Charge"]:
                try:
                    charge_series = df[solph_label_tuple]
                    break
                except KeyError:
                    continue
            
            for solph_label_tuple in ALL_FLOWS["Battery_Discharge"]:
                try:
                    discharge_series = df[solph_label_tuple]
                    break
                except KeyError:
                    continue

            soc_values = soc(
                charge_series=charge_series,
                discharge_series=discharge_series,
                index=df.index,
                nominal_capacity_wh=nominal_capacity
            )
            
            plot_data = pd.DataFrame({
                'Time': df.index.hour + df.index.minute / 60,
                'Day': df.index.day,
                'SoC': soc_values
            })

            # Generate Density Scatter Plot using a 2D histogram
            plt.figure(figsize=(10, 8))
            ax = sns.histplot(
                x=plot_data['Day'],
                y=plot_data['Time'],
                weights=plot_data['SoC'],
                cbar=True,
                cmap="viridis",
                bins=(31, 24), # Bins for each day and hour
                cbar_kws={'label': 'Average SoC (%)'},
                vmin=0, # Set min value for color scale
                vmax=100 # Set max value for color scale
            )
            
            ax.set_title(f'Battery SoC Density Plot for {month} ({scenario_identifier})')
            ax.set_xlabel('Day of Month')
            ax.set_ylabel('Time of Day (hr)')
            plt.savefig(os.path.join(output_dir, f'soc_dsp_{month}.png'))
            plt.close()
            print(f"Generated SoC density plot for {month}.")
        
        except Exception as e:
            print(f"Error processing {filepath}: {e}. Skipping plots for this file.")
            continue

# --- Core Script Execution ---
if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    scenarios_config = {
        "PV_NoBattery": { "flow_dir": os.path.join(script_dir, "flows"), "files": { 'jan': 'flow_nobattery_jan23.csv', 'feb': 'flow_nobattery_feb23.csv', 'mar': 'flow_nobattery_mar23.csv', 'apr': 'flow_nobattery_apr23.csv', 'may': 'flow_nobattery_may23.csv', 'jun': 'flow_nobattery_jun23.csv', 'jul': 'flow_nobattery_jul23.csv', 'aug': 'flow_nobattery_aug23.csv', 'sep': 'flow_nobattery_sep23.csv', 'oct': 'flow_nobattery_oct23.csv', 'nov': 'flow_nobattery_nov23.csv', 'dec': 'flow_nobattery_dec23.csv' } },
        "5kWh": { "flow_dir": os.path.join(script_dir, "flows"), "files": { 'jan': 'flow_5k_jan23.csv', 'feb': 'flow_5k_feb23.csv', 'mar': 'flow_5k_mar23.csv', 'apr': 'flow_5k_apr23.csv', 'may': 'flow_5k_may23.csv', 'jun': 'flow_5k_jun23.csv', 'jul': 'flow_5k_jul23.csv', 'aug': 'flow_5k_aug23.csv', 'sep': 'flow_5k_sep23.csv', 'oct': 'flow_5k_oct23.csv', 'nov': 'flow_5k_nov23.csv', 'dec': 'flow_5k_dec23.csv' } },
        "8kWh": { "flow_dir": os.path.join(script_dir, "flows"), "files": { 'jan': 'flow_8k_jan23.csv', 'feb': 'flow_8k_feb23.csv', 'mar': 'flow_8k_mar23.csv', 'apr': 'flow_8k_apr23.csv', 'may': 'flow_8k_may23.csv', 'jun': 'flow_8k_jun23.csv', 'jul': 'flow_8k_jul23.csv', 'aug': 'flow_8k_aug23.csv', 'sep': 'flow_8k_sep23.csv', 'oct': 'flow_8k_oct23.csv', 'nov': 'flow_8k_nov23.csv', 'dec': 'flow_8k_dec23.csv' } },
        "12kWh": { "flow_dir": os.path.join(script_dir, "flows"), "files": { 'jan': 'flow_12k_jan23.csv', 'feb': 'flow_12k_feb23.csv', 'mar': 'flow_12k_mar23.csv', 'apr': 'flow_12k_apr23.csv', 'may': 'flow_12k_may23.csv', 'jun': 'flow_12k_jun23.csv', 'jul': 'flow_12k_jul23.csv', 'aug': 'flow_12k_aug23.csv', 'sep': 'flow_12k_sep23.csv', 'oct': 'flow_12k_oct23.csv', 'nov': 'flow_12k_nov23.csv', 'dec': 'flow_12k_dec23.csv' } },
        "15kWh": { "flow_dir": os.path.join(script_dir, "flows"), "files": { 'jan': 'flow_15k_jan23.csv', 'feb': 'flow_15k_feb23.csv', 'mar': 'flow_15k_mar23.csv', 'apr': 'flow_15k_apr23.csv', 'may': 'flow_15k_may23.csv', 'jun': 'flow_15k_jun23.csv', 'jul': 'flow_15k_jul23.csv', 'aug': 'flow_15k_aug23.csv', 'sep': 'flow_15k_sep23.csv', 'oct': 'flow_15k_oct23.csv', 'nov': 'flow_15k_nov23.csv', 'dec': 'flow_15k_dec23.csv' } },
        "20kWh": { "flow_dir": os.path.join(script_dir, "flows"), "files": { 'jan': 'flow_20k_jan23.csv', 'feb': 'flow_20k_feb23.csv', 'mar': 'flow_20k_mar23.csv', 'apr': 'flow_20k_apr23.csv', 'may': 'flow_20k_may23.csv', 'jun': 'flow_20k_jun23.csv', 'jul': 'flow_20k_jul23.csv', 'aug': 'flow_20k_aug23.csv', 'sep': 'flow_20k_sep23.csv', 'oct': 'flow_20k_oct23.csv', 'nov': 'flow_20k_nov23.csv', 'dec': 'flow_20k_dec23.csv' } },
        "26kWh": { "flow_dir": os.path.join(script_dir, "flows"), "files": { 'jan': 'flow_26k_jan23.csv', 'feb': 'flow_26k_feb23.csv', 'mar': 'flow_26k_mar23.csv', 'apr': 'flow_26k_apr23.csv', 'may': 'flow_26k_may23.csv', 'jun': 'flow_26k_jun23.csv', 'jul': 'flow_26k_jul23.csv', 'aug': 'flow_26k_aug23.csv', 'sep': 'flow_26k_sep23.csv', 'oct': 'flow_26k_oct23.csv', 'nov': 'flow_26k_nov23.csv', 'dec': 'flow_26k_dec23.csv' } },
        "50kWh": { "flow_dir": os.path.join(script_dir, "flows"), "files": { 'jan': 'flow_50k_jan23.csv', 'feb': 'flow_50k_feb23.csv', 'mar': 'flow_50k_mar23.csv', 'apr': 'flow_50k_apr23.csv', 'may': 'flow_50k_may23.csv', 'jun': 'flow_50k_jun23.csv', 'jul': 'flow_50k_jul23.csv', 'aug': 'flow_50k_aug23.csv', 'sep': 'flow_50k_sep23.csv', 'oct': 'flow_50k_oct23.csv', 'nov': 'flow_50k_nov23.csv', 'dec': 'flow_50k_dec23.csv' } }
    }
    
    # Map scenario identifiers to nominal capacity in Wh.
    nominal_capacities = {
        "PV_NoBattery": None,
        "5kWh": 5000,
        "8kWh": 8000,
        "12kWh": 12000,
        "15kWh": 15000,
        "20kWh": 20000,
        "26kWh": 26000,
        "50kWh": 50000
    }

    scenarios_to_plot = list(nominal_capacities.keys())
    
    for scenario_identifier in scenarios_to_plot:
        print(f"\n--- Generating SoC plots for scenario: {scenario_identifier} ---")
        generate_monthly_soc_dsp(scenario_identifier, scenarios_config[scenario_identifier], nominal_capacities)
    
    print("\nSoC plot generation complete. Check the 'output/soc_dsps' directory.")