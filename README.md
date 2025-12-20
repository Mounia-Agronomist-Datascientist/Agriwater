# AgriWater - Irrigation Needs Calculator

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![Methodology](https://img.shields.io/badge/methodology-FAO--56-green)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

## Description
**AgriWater** is a specialized Python-based decision support tool designed to estimate crop irrigation requirements. By implementing the **FAO-56 Penman-Monteith methodology**, it bridges the gap between raw meteorological data and actionable agronomic insights.

The project combines:
* **Real-time weather data** integration via the Open-Meteo API.
* **Biophysical modeling** for evapotranspiration (ET0, ETc).
* **Rainfall deficit analysis** (effective precipitation).
* **Actionable recommendations** for field-level water management.

**Goal:** To help farmers and AgTech professionals optimize water use based on real-time biological needs rather than static schedules.



## Key Features
* **Reference Evapotranspiration ($ET_0$)**: Precise calculation using the FAO Penman-Monteith equation.
* **Crop Evapotranspiration ($ET_c$)**: Support for multiple crops (Wheat, Maize, Tomato, Grapevine).
* **Phenological Tracking**: Integration of Crop Coefficients ($K_c$) tailored to specific growth stages.
* **Rainfall Integration**: Automated analysis of precipitation over 3, 5, or 7-day windows.
* **Irrigation Recommendations**: Dynamic output provided in $m^3/ha$.
* **Data Export**: Results available in CSV format.


## Scientific Methodology

The engine follows the **FAO Irrigation and Drainage Paper No. 56** standards.

### 1. Reference Evapotranspiration ($ET_0$)
The model calculates evaporation from a hypothetical grass reference crop using the standardized Penman-Monteith equation:

$$ET_0 = \frac{0.408 \Delta (R_n - G) + \gamma \frac{900}{T + 273} u_2 (e_s - e_a)}{\Delta + \gamma (1 + 0.34 u_2)}$$

*Where:*
* $R_n$ is the net radiation at the crop surface.
* $G$ is the soil heat flux density.
* $T$ is the mean daily air temperature at 2m height.
* $u_2$ is the wind speed at 2m height.
* $(e_s - e_a)$ represents the vapor pressure deficit.

### 2. Crop Evapotranspiration ($ET_c$)
We adjust the reference value using a specific crop coefficient based on the current growth stage:

$$ET_c = ET_0 \times K_c$$

### 3. Net Irrigation Requirement
The final recommendation considers the effective rainfall ($P_{eff}$) to avoid over-irrigation:

$$Requirement = ET_c - P_{eff}$$


## Installation

### Prerequisites
* Python 3.8 or higher
* `pip` (Python package manager)

### Setup
```bash
# Clone the repository
git clone [https://github.com/Mounia-Agronomist-Datascientist/Agriwater.git](https://github.com/Mounia-Agronomist-Datascientist/Agriwater.git)
cd agriwater

# Create and activate a virtual environment
python -m venv venv
    # Windows:
    venv\Scripts\activate
    # Mac/Linux:
    source venv/bin/activate

# Install dependencies
pip install -r requirements.txt