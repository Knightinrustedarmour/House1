import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import numpy as np

# --- Configuration & Setup ---
# Set the directory and file path relative to where the script is executed.
try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    file_path = os.path.join("..", "Cost table.xlsx")
except NameError:
    # Fallback for environments where __file__ is not defined
    print("Warning: Could not determine script directory. Ensure 'file_path' is correct.")
    file_path = os.path.join("..", "Cost table.xlsx")
    
sheets = ["Orginal", "Additional PV", "Dynamic"]
output_dir = "energy_analysis_plots_marketing_v3" # Folder remains the same
os.makedirs(output_dir, exist_ok=True)

# Define 21:9 aspect ratio
FIG_WIDTH = 14
FIG_HEIGHT = 6

# Style Settings for a Modern, Professional Look
sns.set(style="whitegrid", context="notebook", font_scale=1.2)

# Professional Color Palette (Set of 3 Distinct Colors)
palette = sns.color_palette("viridis", 3) 
COLOR_MAP = {sheet: palette[i] for i, sheet in enumerate(sheets)}
MARKER_MAP = {"Orginal": "o", "Additional PV": "s", "Dynamic": "D"} # Distinct markers

# Define the exact column names for the new plot
CARBON_BREAKEVEN_COL = "Carbon Breakeven based on Difference from base scenario"
COST_BREAKEVEN_COL = "Break even based on difference" # Cost Breakeven time column

# --- Load Data & Consolidation ---
# --- Load Data & Consolidation ---
data = {}
try:
    for sheet in sheets:
        df = pd.read_excel(file_path, sheet_name=sheet)
        df["Scenario"] = df["Scenario"].astype(str)

        # --- Normalize column names across sheets ---
        df.columns = df.columns.str.strip()  # remove any extra spaces

        rename_map = {
            # Cost breakeven (difference)
            "Cost Break even based on difference": "Break even based on difference",

            # Cost breakeven (revenue)
            "Cost Breakeven based on revenue": "Breakeven based on revenue",

            # Carbon breakeven variants
            "Battery Carbon Breakeven based on Difference from base scenario": 
                "Carbon Breakeven based on Difference from base scenario",
        }

        df.rename(columns=rename_map, inplace=True)

        # Add a column to identify the model/sheet source
        df["Model"] = sheet
        data[sheet] = df

except FileNotFoundError:
    print(f"Error: Excel file not found at '{file_path}'. Please check the path.")
    exit()


# Combine all dataframes into a single one for cross-scenario plotting
combined_df = pd.concat(data.values(), ignore_index=True)

# --- Visualization Function Definitions ---

def create_combined_line_plot(df, metric, y_label, title, filename):
    """Generates a line plot comparing the metric across all models/sheets."""
    plt.figure(figsize=(FIG_WIDTH, FIG_HEIGHT))
    plt.grid(axis='y', linestyle='--', alpha=0.6)

    sns.lineplot(
        data=df,
        x="Scenario",
        y=metric,
        hue="Model",
        palette=COLOR_MAP,
        marker="o",
        markersize=8,
        linewidth=2.5,
        style="Model"
    )

    plt.title(title, fontsize=18, fontweight='bold', pad=20)
    plt.xlabel("Optimization Scenario", fontsize=14)
    plt.ylabel(y_label, fontsize=14)
    plt.legend(title="Energy System Model", frameon=True, loc='best')
    plt.tick_params(axis='x', rotation=0)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/{filename}.png", dpi=300)
    plt.close()

def create_stacked_bar_plot(df, sheet_name, columns, y_label, title, filename):
    """Generates a stacked bar plot for cost structure for a single model/sheet."""
    plt.figure(figsize=(FIG_WIDTH, FIG_HEIGHT))
    plot_df = df.set_index("Scenario")[columns]

    plot_df.plot(kind="bar", stacked=True, ax=plt.gca(),
                 color=sns.color_palette("Reds_r", len(columns)))

    plt.title(f"{title} - {sheet_name}", fontsize=18, fontweight='bold', pad=20)
    plt.xlabel("Optimization Scenario", fontsize=14)
    plt.ylabel(y_label, fontsize=14)
    plt.xticks(rotation=0)
    plt.legend(title="Economic Component", frameon=False, loc='best')
    plt.tight_layout()
    plt.savefig(f"{output_dir}/{filename}.png", dpi=300)
    plt.close()

# --- Main Plot Generation ---

# 1. ENERGY FLOW COMPARISON (Combined Cross-Scenario)
create_combined_line_plot(combined_df, "Annual Grid Import", "Grid Import (kWh)",
                          "Energy Procurement Comparison Across Models",
                          "Annual_Grid_Import_Combined")

create_combined_line_plot(combined_df, "Annual Grid Export", "Grid Export (kWh)",
                          "Surplus Energy Export Comparison Across Models",
                          "Annual_Grid_Export_Combined")
                          
# 2. ECONOMIC PERFORMANCE (Combined Net Expense)
create_combined_line_plot(combined_df, "Net Expense", "Net Expense (Currency)",
                          "Overall Annual Net Expense Across All Models",
                          "Net_Expense_Comparison_Combined")

# Stacked Bar: Cost structure (Best viewed per model)
COST_COLUMNS = ["Import Cost", "Investment cost", "Export revenue"]
for sheet in sheets:
    create_stacked_bar_plot(data[sheet], sheet, COST_COLUMNS, "Monetary Value (Currency)",
                            "Detailed Financial Structure", f"Cost_Structure_{sheet}")

# 3. FINANCIAL BREAKEVEN ANALYSIS (Combined)
# Plot 1: Breakeven based on difference (comparison against a base case)
create_combined_line_plot(
    combined_df,
    "Break even based on difference",
    "Financial Breakeven Period (Years)",
    "ROI Comparison: Breakeven based on Cost Difference (vs Base Case)",
    "Breakeven_Difference_Combined"
)

# Plot 2: Breakeven based on revenue (comparison against no system/grid purchase)
create_combined_line_plot(
    combined_df,
    "Breakeven based on revenue",
    "Financial Breakeven Period (Years)",
    "ROI Comparison: Breakeven based on Net Revenue (vs Grid Power)",
    "Breakeven_Revenue_Combined"
)

# 4. CARBON EMISSIONS (Combined Cross-Scenario)
create_combined_line_plot(
    combined_df,
    "Carbon Footprint (KgCO2eq)",
    "Annual CO2 Emissions (KgCO2eq)",
    "Environmental Impact Across All Models",
    "Carbon_Footprint_Combined"
)

# 5. CARBON BREAKEVEN ANALYSIS (Combined)
# Check if the column exists in the combined DataFrame before plotting
if CARBON_BREAKEVEN_COL in combined_df.columns:
    create_combined_line_plot(
        combined_df,
        CARBON_BREAKEVEN_COL,
        "Carbon Breakeven Period (Years)",
        "Environmental ROI: Carbon Breakeven (vs Base Scenario)",
        "Carbon_Breakeven_Difference_Combined"
    )
else:
    print(f"Warning: Column '{CARBON_BREAKEVEN_COL}' not found. Skipping Carbon Breakeven plot.")

# --------------------------------------------------------------------------------------
# ---------- NEW: COST BREAKEVEN VS. CARBON BREAKEVEN SCATTER PLOT ----------
# --------------------------------------------------------------------------------------

# Ensure both required columns exist before plotting
required_columns = [CARBON_BREAKEVEN_COL, COST_BREAKEVEN_COL]
if all(col in combined_df.columns for col in required_columns):
    print("Generating Breakeven Trade-off Scatter Plot...")

    plt.figure(figsize=(FIG_WIDTH, FIG_HEIGHT))
    ax = plt.gca()

    # Iterate through each unique Model to plot as a separate series for the legend
    for model in combined_df["Model"].unique():
        # Filter for the current model and drop rows where the breakeven columns are NaN
        df_model = combined_df[combined_df["Model"] == model].dropna(subset=required_columns)
        
        # Scatter plot: X = Carbon Breakeven, Y = Cost Breakeven
        ax.scatter(
            df_model[CARBON_BREAKEVEN_COL], 
            df_model[COST_BREAKEVEN_COL],
            label=model,
            color=COLOR_MAP[model],
            marker=MARKER_MAP[model],
            s=150, # Size of the markers
            edgecolor='k',
            alpha=0.75
        )
        
        # Annotate each point with its specific Scenario name
        for i, row in df_model.iterrows():
            text = row["Scenario"]
            ax.annotate(
                text, 
                (row[CARBON_BREAKEVEN_COL], row[COST_BREAKEVEN_COL]),
                xytext=(5, 5), 
                textcoords='offset points', 
                fontsize=9, 
                ha='left'
            )

    # Apply aesthetics
    ax.set_title("Financial ROI vs. Environmental ROI (Breakeven Time)", 
                 fontsize=18, fontweight='bold', pad=20)
    ax.set_xlabel("Carbon Breakeven Period (Years, vs Base Scenario)", fontsize=14)
    ax.set_ylabel("Cost Breakeven Period (Years, vs Base Scenario)", fontsize=14)
    ax.legend(title="Energy System Model", frameon=True, loc='best')
    
    # Add guidelines for interpretation (lower-left is optimal)
    ax.axhline(0, color='r', linestyle=':', alpha=0.5, zorder=0) # Zero Cost Breakeven
    ax.axvline(0, color='g', linestyle=':', alpha=0.5, zorder=0) # Zero Carbon Breakeven

    plt.tight_layout()
    plt.savefig(f"{output_dir}/Cost_Carbon_Breakeven_Tradeoff_Scatter.png", dpi=300)
    plt.close()

else:
    print(f"Error: One or both breakeven columns not found in the DataFrame.")
    print(f"Expected: '{CARBON_BREAKEVEN_COL}' and '{COST_BREAKEVEN_COL}'")

print(f"\n✅ All financial and environmental plots (including the Breakeven Trade-off Scatter Plot) generated successfully in: '{output_dir}' folder.")