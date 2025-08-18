import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Data from the provided image
data = {
    'Scenario': ['NoPV', 'PV_NoBattery', '5kWh', '8kWh', '12kWh', '15kWh', '20kWh', '26kWh', '50kWh'],
    'Operational CO2 (gCO2eq) (Method 1 - Jasper et al)': [0, 0, 7178262, 10795544, 15127096, 17830214, 21406623, 24469282, 30367750],
    'Operational CO2 (gCO2eq) (Method 2 - Detailed Operational)': [0, 0, 389106983.6, 374462281.2, 356925827.1, 345982999.9, 331507134, 319112252.9, 295316399.2]
}

df_comparison = pd.DataFrame(data)
df_comparison.set_index('Scenario', inplace=True)

script_dir = os.path.dirname(os.path.abspath(__file__))
# Create output directory if it doesn't exist
output_dir = os.path.join(script_dir, "output","co2_methods_comp")
os.makedirs(output_dir, exist_ok=True)

# Plotting the bar chart
plt.figure(figsize=(14, 8))
ax = df_comparison.plot(kind='bar', width=0.8, figsize=(14, 8), ax=plt.gca())

plt.title('Comparison of Operational CO2 Emissions by Method', fontsize=16)
plt.xlabel('Scenario', fontsize=12)
plt.ylabel('Operational CO2 (gCO2eq)', fontsize=12)
plt.xticks(rotation=45, ha='right', fontsize=10)
plt.yticks(fontsize=10)
plt.legend(title='Method', fontsize=10, title_fontsize=12)
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()

# Annotate bars with values
for container in ax.containers:
    for rect in container.patches:
        height = rect.get_height()
        if height > 0: # Only annotate non-zero values
            ax.annotate(f'{height:,.0f}',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=8, rotation=90) # Rotate for better fit

# Adjust y-axis limit to accommodate annotations
max_co2 = df_comparison.values.max()
ax.set_ylim(0, max_co2 * 1.2) # Add 20% padding

plot_filename = os.path.join(output_dir, "operational_co2_method_comparison_bar_plot.png")
plt.savefig(plot_filename)
print(f"Saved comparison plot to: {plot_filename}")
plt.close()

# Also save the comparison table to CSV
csv_filename = os.path.join(output_dir, "operational_co2_method_comparison_table.csv")
df_comparison.to_csv(csv_filename, float_format="%.2f")
print(f"Saved comparison table to: {csv_filename}")
