Energy Modeling and Optimization of the Alhambra Semi-Commercial Building: Project Report

1. Project Overview and Motivation

The Alhambra building, located in Oldenburg, serves as a prominent semi-commercial event venue and community space. The facility currently utilizes a rooftop photovoltaic (PV) system with a peak capacity of 26.5 kW. Under existing arrangements, this system is owned by a third party, with all generated energy exported directly to the grid. In 2027, ownership will transition to the building stakeholders, who will then inherit a feed-in tariff of €0.08/kWh.

This ownership transfer necessitates a strategic re-evaluation of the building's energy management. The primary motivation of this project is to identify the most cost-effective and environmentally sustainable strategies for energy self-utilization. A central engineering challenge is the temporal mismatch between energy production and demand: the building’s consumption peaks during nighttime events and weekends, whereas PV production peaks during midday hours.

The core research objectives are:

* Developing strategies to manage daily and seasonal PV-demand mismatches.
* Quantifying the economic and environmental impacts of integrating battery storage and load-shifting protocols.
* Defining the optimal technology mix to maximize self-sufficiency while minimizing the building's CO_2 footprint.

2. System Technical Specifications

The modeling parameters are derived from the physical characteristics and monitoring hardware of the Alhambra installation.

PV System Parameters

Parameter	Value
Latitude	53.143890
Longitude	8.213889
Tilt Angle	38°
Azimuth Angle	253°
Number of Strings	5
Modules per String	22
Module Name	Suniva Titan 240
Module Power Rating	240 W
Total Installed Capacity	26.4 kW
Inverter Capacity	30 kW
DC Capacity (p_{dc0})	20 kW

Data Acquisition Setup

The system monitoring infrastructure includes:

* Temperature Sensor: Mounted externally under the roof to capture environmental thermal data affecting module efficiency.
* Inverter: Records real-time production data directly from the PV plant.
* Energy Meter: Government-issue meter for monitoring total building load consumption.
* Pyranometer: Irradiance data sourced from the OLWIN station (University of Oldenburg, Wechloy campus).

Model Nomenclature

The system architecture in the model is categorized as follows:

* System: The boundary of the Alhambra energy environment.
* Energy Sources: Inputs from the PV plant and the external electricity grid.
* Energy Demands: The building's electrical load (lighting, audio systems, and appliances).
* Components and Nodes: Functional model units including feed_in (self-consumption), grid_export, and Battery_Storage.

3. Technical Methodology: Modeling and Optimization

3.1 PVLIB Modeling

Photovoltaic output was simulated using the pvsystem.pvwatts function within the PVLIB Python library. The model calculates Plane of Array (G_{poa}) irradiance to determine DC power output (P_{dc}) using the following mathematical model:

P_{dc} = \frac{G_{poa}}{1000} P_{dc0} (1 + \gamma_{pdc} (T_{cell} - T_{ref}))

Where:

* P_{dc0} = 20 kW (DC Capacity)
* \gamma_{pdc} = -0.0045 (Temperature coefficient)
* T_{ref} = 25°C

The AC power output is calculated assuming a system efficiency of 86.9%. Furthermore, a threshold of 500W is applied; power outputs below this value are excluded as the physical inverter requires 500W as a minimum operating power.

3.2 MTRESS Framework

The Model Template for Residential Energy Supply Systems (MTRESS) was utilized to optimize energy flows. MTRESS facilitates the fulfillment of fixed demand by prioritizing "feed_in" components for self-consumption. Any surplus energy following demand satisfaction and battery charging is directed to the "grid_export" component.

3.3 Scenario Definition

Eight battery storage scenarios were analyzed to identify the point of diminishing returns:

* No Battery (Baseline Case)
* 5 kWh, 8 kWh, 12 kWh, 15 kWh, 20 kWh, 26 kWh, and 50 kWh.

4. Model Validation and Performance Metrics

The accuracy of the PVLIB model is influenced by the 4.51 km distance between the Alhambra building and the OLWIN pyranometer. This geographic separation introduces a potential RMSE error of 2% of nominal power and a bias of 0.8%.

Error Metrics of Real vs. Modeled Values

Analysis was performed over 790 days, yielding 1,137,600 data points for comparison.

Metric	Minutely Interval (W)	Hourly Interval (W)
Mean Absolute Error (MAE)	760.81	414.73
Root Mean Square Error (RMSE)	2617.39	1441.12
Mean Bias Error (MBE)	0.37	-0.96

The scatter density analysis shows a high concentration of data (approximately 10^5 points) along the ideal fit line. Given these metrics, the PVLIB model serves as a valid technical replacement for empirical production data in this study.

5. The Base Case: Baseline Energy Analysis

The "Base Case" represents the system's performance without storage or behavioral intervention. Yearly data indicates that Alhambra often generates more energy than it consumes (e.g., 23,288 kWh produced vs. 19,038 kWh consumed in 2023). However, the nocturnal profile of the venue results in high grid dependency.

* Winter Baseload: Engineering analysis reveals a significant increase in winter energy consumption. This is attributed to the operation of a 1 kW motor used for continuous air circulation, which raises the baseload regardless of event activity.
* Grid Dependency: Without storage, dependency remains highest during evening events.
* Battery Behavior:
  * Small Batteries (5 kWh): Exhibit shallow, high-frequency cycles.
  * Large Batteries (≥20 kWh): Charge throughout the solar peak and discharge during peak nighttime demand.

6. Sensitivity Analysis: Comparative Case Studies

6.1 Load Shifting

This case modeled the impact of shifting the top 2 high-load nights per month specifically from May to September to "sundowner" hours.

* Technical Impact: For a 12 kWh battery scenario, this shift results in a grid import reduction of 193.34 kWh annually.
* Economic Impact: This behavioral change yields an annual net expense saving of €52.24.

6.2 Additional PV

An expansion scenario was modeled using the System Advisory Model (SAM). The proposed addition includes 9 modules (21 m^2) for a nominal capacity increase of 3583W.

* Production: Increases annual output by 3047.9 kWh.
* Result: While increasing export revenue, the returns for self-sufficiency diminish unless paired with significantly larger battery storage.

6.3 Dynamic Pricing

The model compared the standard fixed rate (€0.35/kWh) against dynamic hourly day-ahead prices from SMARD.

* Pricing Statistics (2023): Mean: €0.1787, Max: €0.6893, Min: -€0.5296.
* Impact: Dynamic pricing reduces the net expense due to lower average market rates but increases the economic necessity of battery storage to arbitrage against high-price volatility periods.

7. Economic and Environmental Impact Assessment

7.1 Carbon Impact

The environmental footprint is calculated by summing grid emissions and component manufacturing impacts. The manufacturing footprint is normalized to provide an annual CO_2 value.

\text{Total } CO_2 \text{ Impact} = (\text{Grid Emission Factor} \times \text{Grid Import}) + \text{Battery Manufacturing Emission} + \text{PV Manufacturing Emission}

* Factors: Battery manufacturing is rated at 109 kgCO_2eq/kWh; PV modules (Mono) at 515 gCO_2eq/kWp.
* Carbon Breakeven: Small batteries achieve breakeven in approximately 0.87 to 0.92 years by displacing carbon-intensive grid energy.

7.2 Cost-Benefit Analysis

The following table presents the operating cost summary based on the €0.35/kWh import and €0.08/kWh export rates.

Scenario	Investment Cost	Net Expense	Cost Breakeven (Years)
PV_NoBattery	€0.00	€3621.15	0.00
5 kWh	€5982.13	€3246.72	15.98
8 kWh	€8000.61	€3058.18	14.21
12 kWh	€10691.91	€2832.41	13.56
15 kWh	€12710.39	€2691.57	13.67
20 kWh	€16074.52	€2505.36	14.41
26 kWh	€20111.48	€2346.00	15.77
50 kWh	€36259.30	€2041.09	22.95

7.3 Optimization Synthesis

The "sweet spot" for optimization is the 8-12 kWh range. A 12 kWh battery provides the fastest financial breakeven (13.56 years) while maintaining a carbon breakeven period of less than one year (0.98 years).

8. Conclusions and Strategic Recommendations

Energy modeling confirms that the current PV system alone mitigates approximately 30% of total consumption. To achieve higher self-sufficiency following the 2027 ownership transition, additional hardware and behavioral shifts are required.

Strategic Recommendations:

1. Battery Procurement: Invest in a 12 kWh battery system. This capacity offers the most efficient balance between investment cost and operational savings.
2. Load Management: Implement "sundowner" scheduling for high-energy events between May and September to align demand with peak PV production.
3. System Health Monitoring: Stakeholders should utilize the Performance Ratio (PR) as a primary metric to monitor system health and efficiency post-transition.
4. Ownership Readiness: Prepare for the €0.08/kWh feed-in tariff by maximizing on-site consumption, as the delta between import costs (€0.35) and export revenue is significant.
