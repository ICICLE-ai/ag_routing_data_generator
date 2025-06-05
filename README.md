# Agricultural Routing Synthetic Data Generation

This repository provides a python script to generate synthetic location and vehicle data (csv files) for developers and researchers aiming to model and solve agricultural logistics problems such as:
- Vehicle Routing Problem (VRP)
- Traveling Salesman Problem (TSP)
- Network Design Problem

# Explanation

1. **locations.csv**  
   - Contains synthetic “location” rows (depots and customers).  
   - The first row (`L001`) is a fixed depot at the specified latitude/longitude.  
   - The remaining rows are random points within a given radius; each has a 10% chance to be flagged as an additional depot.  
   - All rows include fields such as demand, product type, temperature requirements, ripeness/expiration dates, packaging, handling notes, and time windows.

2. **vehicles.csv**  
   - Contains synthetic “vehicle” rows.  
   - The number of vehicles is at least 30% of the number of location rows (rounded up).  
   - Each vehicle’s start location is randomly chosen from any location flagged as a depot.  
   - Vehicle capacity is randomly between 100 and 500 boxes.  
   - Availability windows span any two hour marks in the 24-hour day (00:00–23:00).

---

# How-To Guide

Follow these steps in order to clone the repository, set up your environment, install dependencies, and generate the CSV files.

1. **Clone the Repository**  
   ```bash
   git clone https://github.com/ICICLE-ai/ag_routing_data_generator.git
   cd agricultural-routing-data-template
2. **Create a Python Virtual Environment**
    ```bash
    python3 -m venv venv
3. **Activate the Virtual Environment**
    - For macOS/Linux
        ```bash
        source venv/bin/activate
    - Windows/Powershell
        ```bash
        .\venv\Scripts\Activate.ps1
4. **Install Required Packages**
    ```bash
    pip install -r requirements.txt
5. **Run the Data Generator Script**
    ```bash
    python data_generator_script.py \
    --num_records 20 \
    --lat 44.3538510 \
    --lon -89.2031370 \
    --radius 400 \
    --locations_output locations.csv \
    --vehicles_output vehicles.csv
- --num_records: Total location rows to generate (including the fixed depot L001).

- --lat and --lon: Center coordinates (decimal degrees) for the fixed depot.

- --radius: Radius in miles around (lat, lon) to randomly generate additional locations.

- --locations_output: Output filename for locations.csv.

- --vehicles_output: Output filename for vehicles.csv.
