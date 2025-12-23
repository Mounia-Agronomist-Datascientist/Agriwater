# Usage Guide - AgriWater

## Table of Contents
1. Installation
2. CLI Usage
3. Usage as a Python Library
4. Practical Examples
5. Interpreting Results
6. FAQ
7. Troubleshooting



## Installation

### Prerequisites
* Python 3.8 or higher
* pip (Python package manager)
* Internet connection (for real-time weather data retrieval)

### Installation Steps

```bash
# 1. Clone the repository
git clone [https://github.com/your-username/agriwater.git](https://github.com/your-username/agriwater.git)
cd agriwater

# 2. Create a virtual environment (recommended)
python -m venv venv

# 3. Activate the virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt
```
### Verify Installation

```Bash
python main.py --help
```
If the installation is successful, the help menu will be displayed.

### CLI Usage
Launching the Interactive Interface

```
python main.py
```

### Step-by-Step Workflow

**Step 1: Location Configuration**
You can either:
- Select a predefined city (Montpellier, Paris, Lyon, Toulouse)
- Enter custom GPS coordinates

```
Location Configuration
Predefined locations:
   1. Montpellier, France
   2. Paris, France
   3. Lyon, France
   4. Toulouse, France
   5. Custom
Select a location [1/2/3/4/5] (1): 1
```

### Step 2: Crop and Stage Selection
Select from:

- Wheat (Triticum aestivum)
- Maize (Zea mays)
- Tomato (Solanum lycopersicum)
- Grapevine (Vitis vinifera)

Then choose the phenological stage:
- Initial
- Development
- Mid-season
- Late-season

```
Crop Selection
Available crops:
   1. Wheat (wheat)
   2. Maize (maize)
   3. Tomato (tomato)
   4. Grapevine (grapevine)
Select crop number: 2

Growth stages for Maize:
   1. Initial (Kc = 0.30)
   2. Development (Kc = 0.80)
   3. Mid Season (Kc = 1.20)
   4. Late Season (Kc = 0.60)
Select growth stage: 3
```

### Step 3: Enter Surface 

````
Enter surface area in hectares [default: 10.0]: 15
Surface area: 15.00 ha
````

### Step 4: Analysis Parameters

```
Analysis Parameters
Analysis period in days [default: 7]: 7
Irrigation efficiency (0-1) [default: 0.85]: 0.85
Period: 7 days, Efficiency: 85%
```

### Step 5: Results

The full report displays:
- Water balance ($ET_c$, precipitation)
- Irrigation needs (net and gross)
- Total water volume required (in $m^3$)
- Recommendations

### Step 6: Additional Actions
After the calculation, you can:
- Export to CSV: Save results to a file
- Create Visualizations: Generate performance charts
- View Crop Info: Display detailed parameters
- New Analysis: Restart with different parameters
- Quit

## Library UsageBasic

```
ImportPythonfrom src.irrigation_calculator import IrrigationCalculator

# Initialize the calculator
calculator = IrrigationCalculator(
    latitude=43.6109,
    longitude=3.8772,
    crop_name="maize",
    crop_stage="mid_season",
    surface_ha=10.0
)

# Calculate needs
results = calculator.calculate_irrigation_needs(
    days_count=7,
    efficiency=0.85
)

print(f"Required water volume: {results['gross_volume_m3']:.0f} m3")
````

**Display Full Report**

```
calculator.display_full_report(days_count=7, efficiency=0.85)
````

**Export to CSV**

```
calculator.export_results_to_csv(
    filename="results.csv",
    days_count=7,
    efficiency=0.85
)
```

**Interpreting Results**

Water Balance: 
The report displays three key values:
- Average daily $ET_c$ (mm/day)Meaning: 
- The crop consumes an average of $X$ mm of water per day.Total $ET_c$ (mm)Meaning: Over the selected period, the crop requires $X$ mm of water in total.
- Precipitation (mm)Meaning: Total rainfall measured over the period.

Irrigation Requirements
- Net Irrigation Need (mm): The water deficit to be covered.

Formula: $\text{Total } ET_c - \text{Precipitation}$
- Gross Irrigation Need (mm): The amount to apply considering system losses.

Formula: $\text{Net Need} / \text{Efficiency}$
- Total Volume ($m^3$): The actual amount of water to pump.

Formula: $\text{Gross Need} \times 10 \times \text{Surface Area}$

**Recommendations**
Net Need : 

- =0 mm -> No irrigation needed
- <10 mm -> "Low requirement, monitor closely"
≥10 mm -> Irrigation required

**FAQ**

- **Q1: Which analysis period should I choose?**
Answer: It depends on your soil type. 
Sandy soils usually require 3-5 days analysis,while clay soils can support a 7-day cycle. It also depends on the culture (more or less sensitive to hydric stress) and the climate. By default, use the recommended periods in `crops_parameter.json`

- **Q2: How do I choose irrigation efficiency?**
Answer:It depends on your irrigation system : 
    - Surface irrigation: 0.60 - 0.75
    - Sprinkler: 0.75 - 0.85
    - Drip: 0.85 - 0.95

By default, we selected 0.85%

- **Q3: Can I add new crops?**
Answer: Yes. You can edit data/crops_parameters.json following the FAO-56 standards.

## Troubleshooting

**Problem**: `ModuleNotFoundError`
- Cause: Dependencies are not installed.
- Solution: Run pip install -r requirements.txt.

**Problem**: `Failed to fetch weather data` 
- Cause: API connection issue or invalid coordinates.
- Solution: Check your internet connection and verify your GPS coordinates.

**Problem**: `Invalid crop`
- Cause: The name of the crop is incorrect.
- Solution: Use the exact names used in `crops_parameter.json`

**Problem**: Graphics not displayed:
- Cause : Matplotlib is not well configuated
- Solution : `pip install --upgrade matplotlib`. On linux, install the system dependencies : `sudo apt-get install python3-tk`

## Support
- **Email:** mounia.tonazzini@gmail.com
Author: Mounia TonazziniVersion: 1.0 (December 2025)