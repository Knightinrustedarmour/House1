import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import numpy as np
import re

# --- Configuration & Setup ---
try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    file_path = os.path.join("Cost_table.xlsx")
except NameError:
    print("Warning: Could not determine script directory. Ensure 'file_path' is correct.")
    file_path = os.path.join("Cost_table.xlsx")

sheets = ["Orginal", "Additional PV", "Dynamic", "Load Shift"]

output_dir = "cost_analysis_plots"
os.makedirs(output_dir, exist_ok=True)

# Figure aspect ratio for the SCATTER PLOT (21:9)
SCATTER_FIG_WIDTH = 21
SCATTER_FIG_HEIGHT = 9

# Standard figure aspect ratio for other plots
OTHER_FIG_WIDTH = 14
OTHER_FIG_HEIGHT = 6

sns.set(style="whitegrid", context="talk", font_scale=1.1) 

# Color and marker mappings for models
palette = sns.color_palette("viridis", len(sheets))
COLOR_MAP_MODELS = {sheet: palette[i] for i, sheet in enumerate(sheets)}
MARKER_MAP = {"Orginal": "o", "Additional PV": "s", "Dynamic": "D", "Load Shift": "^"}

STANDARD_COLUMNS = [
    "Scenario",
    "Annual Grid Import",
    "Import Cost",
    "Annual Grid Export",
    "Export revenue",
    "Investment cost",
    "Net Expense",
    "Cost Difference from base scenario",
    "Cost Breakeven based on revenue",
    "Cost Break even based on difference",
    "Carbon Footprint (KgCO2eq)",
    "Carbon Difference from Base scenario",
    "Battery Manufacturing CO2 (KG/KW capacity)",
    "PV Manufacturing CO2 (KG/KW capacity)",
    "Carbon Breakeven based on Difference from base scenario"
]

CARBON_BREAKEVEN_COL = "Carbon Breakeven based on Difference from base scenario"
COST_BREAKEVEN_COL = "Cost Break even based on difference" # COST is now X-AXIS

# --- Helper function to extract battery size ---
def extract_battery_size(scenario_name):
    """Extract numeric battery size in kW/kWh, or 0 for 'PV_NoBattery'."""
    if "NoBattery" in str(scenario_name):
        return 0
    m = re.search(r"(\d+)", str(scenario_name))
    return float(m.group(1)) if m else np.nan

# --- Load Data & Consolidation ---
print(f"Loading data from: {file_path}")
data = {}
try:
    for sheet in sheets:
        df = pd.read_excel(file_path, sheet_name=sheet)
        df["Scenario"] = df["Scenario"].astype(str)
        df.columns = df.columns.str.strip()

        df = df[[col for col in STANDARD_COLUMNS if col in df.columns]]

        df["Model"] = sheet
        df["Battery_kW"] = df["Scenario"].apply(extract_battery_size) # Column renamed to kW
        data[sheet] = df

except FileNotFoundError:
    print(f"Error: Excel file not found at '{file_path}'. Please check the path and ensure the file exists.")
    exit()

# Using Battery_kW for consistency
combined_df = pd.concat(data.values(), ignore_index=True)
combined_df['Battery_kW'] = pd.to_numeric(combined_df['Battery_kW'], errors='coerce')
print("Data loaded and combined successfully.")


# --- Visualization Functions (Standard Plots) ---
def create_combined_line_plot(df, metric, y_label, title, filename):
    plt.figure(figsize=(OTHER_FIG_WIDTH, OTHER_FIG_HEIGHT)) 
    plt.grid(axis='y', linestyle='--', alpha=0.6)

    sns.lineplot(
        data=df,
        x="Scenario",
        y=metric,
        hue="Model",
        palette=COLOR_MAP_MODELS,
        style="Model",
        markers=True,
        dashes=False,
        linewidth=2.5,
        markersize=9
    )

    plt.title(title, fontsize=18, fontweight='bold', pad=20)
    plt.xlabel("Optimization Scenario", fontsize=14)
    plt.ylabel(y_label, fontsize=14)
    plt.legend(title="Energy System Model", frameon=True, loc='upper right') 
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/{filename}.png", dpi=300)
    plt.close()


def create_stacked_bar_plot(df, sheet_name, columns, y_label, title, filename):
    plt.figure(figsize=(OTHER_FIG_WIDTH, OTHER_FIG_HEIGHT))
    plot_df = df.set_index("Scenario")[columns]
    
    plot_df.plot(kind="bar", stacked=True, ax=plt.gca(),
                 color=sns.color_palette("Set1", len(columns))) 

    plt.title(f"{title} - {sheet_name}", fontsize=18, fontweight='bold', pad=20)
    plt.xlabel("Optimization Scenario", fontsize=14)
    plt.ylabel(y_label, fontsize=14)
    plt.xticks(rotation=0)
    plt.legend(title="Economic Component", frameon=False, loc='best')
    plt.tight_layout()
    plt.savefig(f"{output_dir}/{filename}.png", dpi=300)
    plt.close()

# --- Main Plot Generation ---
print("Generating plots...")

# 1. ENERGY FLOW
create_combined_line_plot(combined_df, "Annual Grid Import", "Grid Import (kWh)",
                              "Energy Procurement Comparison Across Models",
                              "Annual_Grid_Import_Combined")

create_combined_line_plot(combined_df, "Annual Grid Export", "Grid Export (kWh)",
                              "Surplus Energy Export Comparison Across Models",
                              "Annual_Grid_Export_Combined")

# 2. ECONOMIC PERFORMANCE
create_combined_line_plot(combined_df, "Net Expense", "Net Expense (Currency)",
                              "Overall Annual Net Expense Across All Models",
                              "Net_Expense_Comparison_Combined")

# Stacked cost breakdown
COST_COLUMNS = ["Import Cost", "Investment cost", "Export revenue"]
for sheet in sheets:
    create_stacked_bar_plot(data[sheet], sheet, COST_COLUMNS,
                            "Monetary Value (Currency)",
                            "Detailed Financial Structure",
                            f"Cost_Structure_{sheet}")

# 3. FINANCIAL BREAKEVEN
create_combined_line_plot(combined_df,
                              COST_BREAKEVEN_COL,
                              "Financial Breakeven Period (Years)",
                              "ROI Comparison: Breakeven based on Cost Difference (vs Base Case)",
                              "Breakeven_Difference_Combined")

create_combined_line_plot(combined_df,
                              "Cost Breakeven based on revenue",
                              "Financial Breakeven Period (Years)",
                              "ROI Comparison: Breakeven based on Net Revenue (vs Grid Power)",
                              "Breakeven_Revenue_Combined")

# 4. CARBON EMISSIONS
create_combined_line_plot(combined_df,
                              "Carbon Footprint (KgCO2eq)",
                              "Annual CO2 Emissions (KgCO2eq)",
                              "Environmental Impact Across All Models",
                              "Carbon_Footprint_Combined")

# 5. CARBON BREAKEVEN
if CARBON_BREAKEVEN_COL in combined_df.columns:
    create_combined_line_plot(combined_df,
                              CARBON_BREAKEVEN_COL,
                              "Carbon Breakeven Period (Years)",
                              "Environmental ROI: Carbon Breakeven (vs Base Scenario)",
                              "Carbon_Breakeven_Difference_Combined")
else:
    print(f"Warning: Column '{CARBON_BREAKEVEN_COL}' not found. Skipping Carbon Breakeven plot.")


# 6. COST vs CARBON BREAKEVEN SCATTER (FINAL VERSION)
required_columns = [CARBON_BREAKEVEN_COL, COST_BREAKEVEN_COL, "Battery_kW"] 
if all(col in combined_df.columns for col in required_columns):
    print("Generating Final Enhanced Breakeven Trade-off Scatter Plot...")

    plt.figure(figsize=(SCATTER_FIG_WIDTH, SCATTER_FIG_HEIGHT))
    ax = plt.gca()

    # Get unique battery sizes (kW) to create a contrasting color palette for them
    unique_battery_sizes = sorted(combined_df["Battery_kW"].dropna().unique())
    # Using 'Dark2' for contrasting, qualitative colors 
    battery_color_palette = sns.color_palette("Dark2", n_colors=len(unique_battery_sizes))
    BATTERY_COLOR_MAP = {size: battery_color_palette[i] 
                         for i, size in enumerate(unique_battery_sizes)}

    for model in combined_df["Model"].unique():
        df_model = combined_df[combined_df["Model"] == model].dropna(subset=required_columns)
        df_model = df_model.sort_values("Battery_kW") 

        for i, row in df_model.iterrows():
            current_battery_kw = row["Battery_kW"]
            
            color_to_use = BATTERY_COLOR_MAP.get(current_battery_kw, "grey")

            # X-AXIS is COST_BREAKEVEN_COL; Y-AXIS is CARBON_BREAKEVEN_COL
            ax.scatter(row[COST_BREAKEVEN_COL], # Swapped X-axis
                       row[CARBON_BREAKEVEN_COL], # Swapped Y-axis
                       color=color_to_use, 
                       marker=MARKER_MAP[model], 
                       s=200, 
                       edgecolor='k',
                       alpha=0.8,
                       zorder=5 
                       )
            
            # Annotation text uses 'kW'
            annotation_text = f"{int(current_battery_kw)}kW" if current_battery_kw > 0 else "NoBatt" 
            
            # Annotation coordinates are also swapped
            ax.annotate(annotation_text,
                         (row[COST_BREAKEVEN_COL], row[CARBON_BREAKEVEN_COL]), # Swapped coordinates
                         xytext=(7, 7), 
                         textcoords='offset points',
                         fontsize=8, 
                         ha='left',
                         color='dimgrey',
                         zorder=6
                         )


    ax.set_title("Financial ROI vs. Environmental ROI (Breakeven Time)",
                  fontsize=18, fontweight='bold', pad=20)
    # Swapped X and Y labels
    ax.set_xlabel("Cost Breakeven Period (Years, vs Base Scenario)", fontsize=14) 
    ax.set_ylabel("Carbon Breakeven Period (Years, vs Base Scenario)", fontsize=14) 
    
    # --- Custom Dual Legends (within picture) ---
    # Legend for Models (markers)
    legend_markers = [plt.Line2D([0], [0], marker=MARKER_MAP[m], color='w', 
                                 markerfacecolor='k', markersize=10, 
                                 label=m) for m in combined_df["Model"].unique()]
    
    # Custom Legend for Battery Sizes (colors) - Label uses 'kW'
    legend_colors = [plt.Line2D([0], [0], marker='o', color='w', 
                                markerfacecolor=BATTERY_COLOR_MAP[s], markersize=10, 
                                label=f"{int(s)} kW") for s in unique_battery_sizes]
    
    # Place legends inside the plot area
    first_legend = ax.legend(handles=legend_markers, title="Model", 
                             loc='upper left', bbox_to_anchor=(0.01, 0.99), frameon=True, fontsize=10, title_fontsize=12)
    ax.add_artist(first_legend)
    
    # Legend Title also reflects 'kW'
    ax.legend(handles=legend_colors, title="Battery Size (kW)", 
              loc='lower right', bbox_to_anchor=(0.99, 0.01), frameon=True, fontsize=10, title_fontsize=12)

    # Swapped reference line colors for visual cue (Red for Cost (X), Green for Carbon (Y))
    ax.axvline(0, color='r', linestyle=':', alpha=0.5, label='Zero Cost Breakeven') 
    ax.axhline(0, color='g', linestyle=':', alpha=0.5, label='Zero Carbon Breakeven')
    
    plt.tight_layout() 
    plt.savefig(f"{output_dir}/Cost_Carbon_Breakeven_Tradeoff_Scatter_Final.png", dpi=300)
    plt.close()
else:
    print(f"Error: One or more required columns ({required_columns}) not found in the DataFrame for scatter plot.")

print(f"\n✅ All plots (including final enhanced scatter plot with correct axes and 'kW' labels) generated successfully in the: '{output_dir}' folder.")