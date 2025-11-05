import pandas as pd
from datetime import timedelta
import os

# === Parameters ===
os.chdir(os.path.dirname(__file__))
input_path = os.path.join("..", "op_data_power.csv")
output_path = os.path.join("..", "op_data_LS.csv")

party_start = 20  # 22:00
party_end = 6     # 04:00 next day
sundowner_start = 10  # 12:00
sundowner_end = 20    # 20:00
months = [5, 6, 7, 8, 9]  # May–Sept

df = pd.read_csv(input_path)
df.rename(columns={df.columns[0]: "timestamp"}, inplace=True)
df["timestamp"] = pd.to_datetime(df["timestamp"], format="%Y-%m-%d %H:%M:%S:%z", errors="coerce")
df["timestamp"] = df["timestamp"].dt.tz_convert(None)  
df = df.sort_values("timestamp").reset_index(drop=True)
df.set_index("timestamp", inplace=True)


# === Estimate base load using 7-day rolling minimum ===
df["base_load"] = df["Load_W"].rolling("7D", min_periods=1).min()

# === Identify two highest-load party nights per month ===
df["date"] = df.index.date
df["hour"] = df.index.hour

party_energy = []

for date, day_df in df.groupby("date"):
    # define window 22:00 to 04:00 next day
    start_time = pd.Timestamp(date) + pd.Timedelta(hours=party_start)
    end_time = pd.Timestamp(date) + pd.Timedelta(hours=24 + party_end)
    mask = (df.index >= start_time) & (df.index < end_time)
    total_energy = df.loc[mask, "Load_W"].sum()
    party_energy.append({
        "date": pd.Timestamp(date),
        "month": pd.Timestamp(date).month,
        "energy": total_energy
    })

party_df = pd.DataFrame(party_energy)
party_df = party_df[party_df["month"].isin(months)]

# top 2 party days per month
top_days = (
    party_df.groupby("month")
    .apply(lambda x: x.nlargest(2, "energy"))
    .reset_index(drop=True)
)

# === Simulate shifting ===
df["Load_W_shifted"] = df["Load_W"]

for _, row in top_days.iterrows():
    date = row["date"]

    # Nighttime (original party)
    night_start = pd.Timestamp(date) + pd.Timedelta(hours=party_start)
    night_end = pd.Timestamp(date) + pd.Timedelta(hours=24 + party_end)
    night_mask = (df.index >= night_start) & (df.index < night_end)

    # Sundowner (shifted)
    sun_start = pd.Timestamp(date) + pd.Timedelta(hours=sundowner_start)
    sun_end = pd.Timestamp(date) + pd.Timedelta(hours=sundowner_end)
    sun_mask = (df.index >= sun_start) & (df.index < sun_end)

    # Compute "party load" above base
    night_load = df.loc[night_mask, "Load_W"]
    night_base = df.loc[night_mask, "base_load"]
    extra_load = (night_load - night_base).clip(lower=0)

    # Ensure matching length between night and sundowner
    if len(extra_load) == len(df.loc[sun_mask, "Load_W"]):
        df.loc[night_mask, "Load_W_shifted"] = night_base  # keep base load
        df.loc[sun_mask, "Load_W_shifted"] = df.loc[sun_mask, "Load_W_shifted"] + extra_load.values
    else:
        print(f"⚠️ Warning: length mismatch for {date}")

# === Output new CSV ===
df_out = df[["Load_W_shifted"]].rename(columns={"Load_W_shifted": "Load_W"})
df_out.to_csv(output_path, index_label="")

print(f"✅ Sundowner simulation complete.\nSaved as: {output_path}")
